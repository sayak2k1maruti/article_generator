import os
import sys
from src.app import run
from datetime import datetime





if __name__ == "__main__":
    if len(sys.argv) not in [2,3]:
        print("Usage: python main.py <outline_file_path> <output_dir_path>")
        sys.exit(1)
    
    outline_file_path = sys.argv[1]
    base_output_dir = os.path.expanduser(sys.argv[2]) if len(sys.argv) > 2 else os.path.expanduser("~/example_blogs/outputs")
    timestamped_output_dir = os.path.join(base_output_dir, datetime.now().strftime("%Y_%m_%d_%H%M%S"))

    os.makedirs(base_output_dir, exist_ok=True)
    os.makedirs(timestamped_output_dir, exist_ok=True)

    run(
        outline_file_path = outline_file_path,
        example_posts_dir = "./src/examples/example_blogs",
        output_dir = timestamped_output_dir,
        word_count = 1000
    )
    


