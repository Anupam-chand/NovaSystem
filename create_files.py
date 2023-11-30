import argparse
import json
import logging
from pathlib import Path

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default list of file names
default_files = ['file1.txt', 'file2.txt', 'file3.txt']

def create_files(file_list, target_dir):
    """
    Create files in the specified directory based on the file list.

    Parameters:
    file_list (list of str): List of file names to be created.
    target_dir (str): Path of the directory where files will be created.

    Returns:
    None
    """
    Path(target_dir).mkdir(parents=True, exist_ok=True)  # Create the target directory if it doesn't exist
    for file_name in file_list:
        file_path = Path(target_dir) / file_name
        try:
            file_path.touch(exist_ok=True)  # Create the file
            logging.info(f"Created: {file_path}")
        except Exception as e:
            logging.error(f"Failed to create {file_path}: {e}")

def load_file_list(file_path):
    """
    Load the file list from a JSON file.

    Parameters:
    file_path (str): Path to the JSON file containing the list of file names.

    Returns:
    list of str: List of file names.
    """
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format in {file_path}: {e}")
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    except Exception as e:
        logging.error(f"Unexpected error while loading JSON file: {e}")

    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create files in a specified directory')
    parser.add_argument('-d', '--directory', type=str, default='output', help='Target directory for file creation')
    parser.add_argument('-f', '--file', type=str, help='JSON file with a list of file names')
    args = parser.parse_args()

    if args.file:
        file_list = load_file_list(args.file)
        if not file_list:
            logging.info("Falling back to default file list.")
            file_list = default_files
    else:
        file_list = default_files

    create_files(file_list, args.directory)
