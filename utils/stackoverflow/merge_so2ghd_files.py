import argparse
import logging
from typing import Dict, Any
import os
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

class MergeFiles:
    """Class to handle merging of two so2ghd log files."""
    
    def __init__(self, base_file: str, patch_file: str, new_file: str):
        self.base_file = base_file
        self.patch_file = patch_file
        self.new_file = new_file
        self.lines_mapping = {}
    
    def merge(self):
        """Merge two so2ghd log files into a new file."""
        self.__read_file(self.base_file)
        self.__read_file(self.patch_file)

        with open(self.new_file, 'w') as merge_file:
            for line in self.lines_mapping.values():
                merge_file.write(line + '\n')

    def __read_file(self, file:str):
        with open(file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                stripped_line = line.strip()
                # Skip empty lines or lines with only whitespace
                if not stripped_line:
                    continue
                
                tokens = stripped_line.split()
                # Valid redirect lines should have at least 4 tokens: redir, path, url, permanent
                if len(tokens) >= 4 and tokens[0] == 'redir':
                    key = tokens[1]  # The path (e.g., /questions/1201)
                    self.lines_mapping[key] = stripped_line
                else:
                    logger.warning(f"Skipping line in file '{file}': {stripped_line}")


def main():
  parser = argparse.ArgumentParser(description='Merge so2ghd log files into a new single file. The first file will be considered the base file. The second file will either add or overwrite entries from the first file.')
  parser.add_argument('--base-file', required=True, help='Path to the base log file')
  parser.add_argument('--patch-file', required=True, help='Path to the patch log file to merge with the base file')
  parser.add_argument('--new-file', required=True, help='Path to the new log file to merge')
  args = parser.parse_args()

  
  if not os.path.isfile(args.base_file):
    logger.error(f"Base file '{args.base_file}' does not exist.")
    return  
  
  if not os.path.isfile(args.patch_file):
    logger.error(f"Patch file '{args.patch_file}' does not exist.")
    return

  logger.info(f"Starting merge of {args.base_file} and {args.patch_file} into {args.new_file}")
  merge_files = MergeFiles(args.base_file, args.patch_file, args.new_file)
  merge_files.merge()
  logger.info(f"Merge completed. Output written to {args.new_file}")

if __name__ == '__main__':
    main()