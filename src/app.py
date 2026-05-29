import os
import sys
import base64
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from markdown_pdf import MarkdownPdf, Section


load_dotenv() # Load environment variables from .env file

__client = OpenAI()
__chat_model = "gpt-5.4-mini"
__image_model = "gpt-image-2"
__default_word_count = 3000
__max_retries = 3

class AIResponseError(Exception):
    pass

class ArticleReviewResponse(BaseModel):
    need_revision: bool = Field(description="True or False, Indicates whether the article needs revision or not")
    feedback: str = Field(description="Detailed feedback on the article if revision is needed, otherwise can be empty")

def review_article(article: str, outline: str) -> ArticleReviewResponse:
    
    prompt = f"""
                Review the following article and check if it follows the given outline 
                <article>
                {article}
                </article>

                <outline>
                {outline}
                </outline>
                Rules:
                 - If the article follows the outline and is in line with the style of the example posts, return a JSON object with need_revision as False and feedback as an empty string.
                 - If the article does not follow the outline or is not in line with the style of the example posts, return a JSON object with need_revision as True and feedback containing detailed feedback on what needs to be revised in the article.
                 - Don't add any additional text or explanations, just return the JSON object as specified above.
                 - Check if article is gramtically correct and if there are any spelling mistakes and include that in the feedback if revision is needed.
                 - Check if the language is easy to understand and if the article is engaging enough and include that in the feedback if revision is needed.
                 - Check if the arciel is well structured and if the ideas are presented in a logical order and include that in the feedback if revision is needed.
                 - Check if it's professional enough and if the tone is appropriate for a blog post and include that in the feedback if revision is needed.
            """
    response = __client.responses.parse(
        model=__chat_model,
        input=[
            {
                "role" : "developer",
                "content" : "You are an expert article reviewer. You have reviewed many articles in the past and you are very good at it. You have a unique style of providing feedback and you are very good at pointing out what is wrong with an article and how to improve it. You are also very good at understanding the outline and style of writing from example posts and checking if the article follows them."
            },
            {
                "role" : "user",
                "content" : prompt
            }
        ],
        text_format = ArticleReviewResponse
    )
    if hasattr(response,"output_parsed"):
       return response.output_parsed
    raise AIResponseError("No Response from AI while reviewing article")

def generate_article(outline: str, example_posts: List[str], past_article: str = "", past_feedback: str = "", word_count: int = __default_word_count) -> str:

    example_posts_markup = "\n\n".join([f"<example-post-{i}>{post}</example-post-{i}>" for i, post in enumerate(example_posts)])

    if not (past_article and past_feedback):
        prompt = f"""
                    Write a detailed blog post based on the following outline:

                    <outline>
                    {outline}
                    </outline>

                    Below are some example blog posts I wrote in the past:
                    <example-posts>
                    {example_posts_markup}
                    </example-posts>

                    Use the language, tone, style and way of writing from the example posts to generate your draft for the new blog post.
                    DON'T use the content from those example posts!

                    Rules:
                    - Return the blog post draft in raw markdown format so that I can directly use it in my markdown-processing pipeline.
                    - Don't add any additional text or explanations, just return the raw markdown content.
                """
    elif past_article and past_feedback:
        prompt = f"""
                    Rewrite the blog post based on the following outline and feedback:

                    <outline>
                    {outline}
                    </outline>

                    <past-article>
                    {past_article}
                    </past-article>

                    <feedback>
                    {past_feedback}
                    </feedback>
                    Use the language, tone, style and way of writing from the example posts to generate your new draft for the blog post.
                    Rules:
                    - Return the blog post draft in raw markdown format so that I can directly use it in my markdown-processing pipeline.
                    - Don't add any additional text or explanations, just return the raw markdown content.
                """
    
    response = __client.responses.create(
        model=__chat_model,
        input=[
            {
                "role" : "developer",
                "content" : "You are a expert article writer. You have written many articles in the past and you are very good at it. You have a unique style of writing and you are very good at engaging the readers. You are also very good at explaining complex topics in a simple and easy to understand way."
            },
            {
                "role" : "user",
                "content" : prompt
            }
        ]
    )
    if hasattr(response,"output_text"):
        return response.output_text
    raise AIResponseError("No Response from AI while generating article")

def load_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "r") as f:
        return f.read()

def generate_thumbnail_from_article(article: str, path_to_save: str) -> str:
    prompt = f"""
                Generate a thumbnail image for a blog post based on the following article content:
                Rules: 
                    - The image should be relevant to the content of the article.
                    - The image should be visually appealing and eye-catching.
                    - The image should be in landscape orientation with a resolution of 1200x628 pixels.
                    - Don't add any text to the image, just generate a relevant and attractive thumbnail based on the article content.
                <article>
                {article}
                </article>
                """
    print("Generating thumbnail image from article content...")
    response = __client.images.generate(
            model=__image_model,
            prompt=prompt,
            stream = False,
            size="1536x1024",
        )
    image_base64 = response.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)
    image_base64_bytes = image_base64.encode("utf-8")

    # Save the image to a file
    print("Saving thumbnail image to file...")
    with open(path_to_save, "wb") as f:
        f.write(image_bytes)
    print(f"Thumbnail image generated and saved successfully at path: {path_to_save} !")
    return image_base64_bytes

def save_file(content: str, file_path: str):
    with open(file_path, "w") as f:
        f.write(content)

def load_example_posts(example_posts_dir: str) -> List[str]:
    example_posts = []
    for file_name in os.listdir(example_posts_dir):
        if file_name.endswith(".txt") or file_name.endswith(".md"):
            file_path = os.path.join(example_posts_dir, file_name)
            example_posts.append(load_file(file_path))
    return example_posts




def generate_pdf_from_markdown_and_thumbnail(markdown_path: str, thumbnail_base64_bytes: bytes, pdf_path: str) -> str:
    pdf = MarkdownPdf(toc_level=2, optimize=True)

    with open(markdown_path, "r") as file:
        markdown_text = file.read()

    parts = markdown_text.split("\n\n", 1)

    if len(parts) < 2:
        part1 = markdown_text
        part2 = ""
    else:
        part1, part2 = parts

    thumbnail_base64 = thumbnail_base64_bytes.decode("utf-8")

    image_markdown = f"""

![](data:image/png;base64,{thumbnail_base64})

"""
    pdf.add_section(
        Section(
            "\n\n".join(
                [
                    part1,
                    image_markdown,
                    part2
                ]
            )
        )
    )

    pdf.save(pdf_path)


def ask_human_revision_choice(review_feedback: str) -> str:
    while True:
        print("\nHuman review decision:")
        print("1) Accept reviewer's decision")
        print("2) Write my own feedback")
        print("3) Save file as it is and continue")
        choice = input("Enter choice (1/2/3): ").strip()

        if choice == "1":
            return "accept_review"
        if choice == "2":
            custom_feedback = input("Enter your feedback to rewrite the article: ").strip()
            if custom_feedback:
                return custom_feedback
            print("Feedback cannot be empty. Please enter custom feedback.")
            continue
        if choice == "3":
            return "save_as_is"
        print("Invalid choice. Please enter 1, 2, or 3.")


def run(
    outline_file_path: str,
    example_posts_dir: str,
    output_dir: str,
    word_count: int = __default_word_count
):
    try:
        print("Loading outline and example posts...")
        outline = load_file(outline_file_path)
        example_posts = load_example_posts(example_posts_dir)
        print("Generating article...")
        article = generate_article(
            outline,
            example_posts,
            word_count=word_count
        )
        print("Saving article...")
        _save_path = os.path.join(output_dir, "generated_article_draft.md")
        save_file(article, _save_path)
        print("Article generated and saved successfully at path: ", _save_path, "! ")

        # Reviewing the article and generating feedback
        rewrite_count = 0
        while True:
            if rewrite_count >= __max_retries:
                print("Maximum number of revisions reached. Proceeding to thumbnail generation with the latest article draft.")
                break
            print("Reviewing the article and generating feedback...")
            review_response = review_article(article, outline)
            if not review_response.need_revision:
                print("Article doesn't need revision. Proceeding to thumbnail generation...")
                break
            print("Article needs revision. Feedback: ", review_response.feedback)
            human_choice = ask_human_revision_choice(review_response.feedback)

            if human_choice == "save_as_is":
                print("Saving current article as-is and continuing to next process...")
                save_file(article, _save_path)
                break

            if human_choice == "accept_review":
                revision_feedback = review_response.feedback
            else:
                revision_feedback = human_choice

            print("Regenerating article based on feedback...")
            article = generate_article(outline, [], article, revision_feedback, word_count)
            print("Overwriting article...")
            save_file(article, _save_path) #Overwriting the same file with the new draft after revision
            rewrite_count += 1


        thumbnail_save_path = os.path.join(output_dir, "generated_thumbnail.png")
        thumbnail_base64_bytes = generate_thumbnail_from_article(article, thumbnail_save_path)

        pdf_save_path = os.path.join(output_dir, "generated_article_with_thumbnail.pdf")
        print("Generating PDF from markdown and thumbnail...")
        generate_pdf_from_markdown_and_thumbnail(
            _save_path,
            thumbnail_base64_bytes,
            pdf_save_path
        )
        print("PDF generated successfully at path: ", pdf_save_path, "!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)