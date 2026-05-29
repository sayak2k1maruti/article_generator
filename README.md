# Blog Generator

An automated blog draft generator that:
- reads an outline file,
- uses AI to generate and review an article,
- rewrites with human-in-the-loop feedback,
- generates a thumbnail image,
- exports a PDF containing the article and thumbnail.

## Usage

Run the generator with an outline file and an optional base output directory:

```bash
uv run main.py <outline_file_path> <output_dir_path>
```

If no output directory is provided, a default timestamped folder under `~/example_blogs/outputs` is used.

## Generated artifacts

Each run creates a timestamped output folder containing:
- `generated_article_draft.md`
- `generated_thumbnail.png`
- `generated_article_with_thumbnail.pdf`

## Development

Install dependencies:

```bash
uv sync
```

Run the pipeline:

```bash
uv run main.py bengalisongs.txt ./
```
