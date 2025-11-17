from PIL import Image, UnidentifiedImageError
import logging
import argparse
import os
from datetime import datetime
import git
import io

logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger_file_handler = logging.FileHandler(datetime.now().strftime('check_image_%d_%m_%Y_%H_%M_.log'))
logger_file_handler.setFormatter(formatter)
logger_console_handler = logging.StreamHandler()
logger_console_handler.setFormatter(formatter)
root_logger.addHandler(logger_file_handler)
root_logger.addHandler(logger_console_handler)


def is_png_bytes(blob_data: bytes) -> bool:
    try:
        with Image.open(io.BytesIO(blob_data)) as img:
            logger.info(f"Image format detected: {img.format}")
            return img.format == "PNG"
    except (UnidentifiedImageError, FileNotFoundError):
        return False
    except Exception as e:
        logger.error(f"Error checking PNG bytes: {e}")
        return False


def process_git_directory(git_directory, image_directory, output_directory):
    try:
        repo = git.Repo(git_directory)
    except git.exc.InvalidGitRepositoryError:
        logger.error(f"Error: {git_directory} is not a valid Git repository")
        return

    os.makedirs(output_directory, exist_ok=True)

    copied_files = set(os.listdir(output_directory)) 

    for commit in repo.iter_commits():
        logger.info(f"Processing commit {commit.hexsha[:7]} - {commit.committed_datetime}")

        try:
            tree = commit.tree / image_directory
        except KeyError:
            logger.warning(f"Directory '{image_directory}' does not exist in this commit.")
            continue

        for blob in tree.traverse():
            if blob.type != "blob":
                continue  # skip directories

            filename = os.path.basename(blob.path)
            if filename in copied_files:
                continue  # skip files already saved

            try:
                blob_data = blob.data_stream.read()
                if is_png_bytes(blob_data):
                    output_path = os.path.join(output_directory, filename)
                    with open(output_path, "wb") as f:
                        f.write(blob_data)
                    copied_files.add(filename)
                    logger.info(f"Copied new PNG: {filename} from commit {commit.hexsha[:7]}")
            except Exception as e:
                logger.error(f"Error reading {blob.path} in {commit.hexsha[:7]}: {e}")

    logger.info(f"\n✅ Completed extraction. Output directory: {os.path.abspath(output_directory)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract PNGs from a directory across Git commits (no overwrite).")
    parser.add_argument("-gd", "--git-directory", help="Path to a Git repository.")
    parser.add_argument("-o", "--output-directory", help="Path to output PNG files to.")
    parser.add_argument("-d", "--directory", help="Path to directory (within repo) containing images.")
    args = parser.parse_args()

    if args.git_directory and args.directory and args.output_directory:
        process_git_directory(args.git_directory, args.directory, args.output_directory)
    else:
        logger.error("Please provide --git-directory, --directory, and --output-directory.")
