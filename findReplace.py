import os
import argparse
import shutil
import re  # For more advanced pattern matching if needed, though str.replace is fine for literal strings


class find_and_replace_in_files():
    def __init__(self,
                 path,
                 old_string,
                 new_string,
                 file_pattern=None,
                 create_backup=False,
                 recursive=True):

        if path:
            if not os.path.isdir(path) and not os.path.isfile(path):
                print(f"Error: path '{path}' not found.")
                return
            else:
                self.path = path
                print(f"Searching in: '{self.path}'")
        else:
            print(f"No path specifed.")
            exit()
        if old_string:
            if new_string:
                self.old_string = old_string
                self.new_string = new_string
                print(f"Replacing '{old_string}' with '{new_string}'")
        else:
            if not new_string:
                print(f"No old_string or new_string specifed.")
            else:
                print(f"No new_string specifed.")
            exit()
        self.file_pattern = file_pattern
        self.create_backup = create_backup
        self.recursive = recursive
        print(f"Creating backups: {self.create_backup}")
        print(f"Recursive search: {recursive}")
        print("-" * 30)
        self.find_and_replace_in_files()

    def find_and_replace_in_files(self):
        """
        Finds and replaces a string in file or files within a specified directory.

        Args:
            path (str): The path to file or directory to search.
            old_string (str): The string to find.
            new_string (str): The string to replace with.
            file_pattern (str, optional): A glob-style pattern (e.g., "*.txt").
                                        If None, all files are considered.
            create_backup (bool): If True, creates a .bak backup of each modified file.
            recursive (bool): If True, searches subdirectories as well.
        """
        if not os.path.isdir(self.path) and not os.path.isfile(self.path):
            print(f"Error: path '{self.path}' not found.")
            return

        if os.path.isdir(self.path):
            # Use re.compile for efficiency if using regex, but str.replace is simple
            # old_string_re = re.compile(re.escape(old_string)) # Use re.escape if old_string is a literal to be matched by regex

            self.files_processed = 0
            self.files_modified = 0

            if self.recursive:
                walker = os.walk(self.path)
            else:
                walker = [(self.path, [], [f for f in os.listdir(self.path)
                                           if os.path.isfile(os.path.join(self.path, f))])]

            for root, _, files in walker:
                for filename in files:
                    file_path = os.path.join(root, filename)
                    # Apply file pattern filter if specified
                    if self.file_pattern:
                        # Simple glob matching (no full fnmatch for simplicity, could add if needed)
                        if not filename.endswith(self.file_pattern.lstrip('*')):
                            continue
                    self.processFile(file_path)
        else:
            self.processFile(self.path)

        print("-" * 30)
        print(
            f"Finished. Processed {self.files_processed} files, modified {self.files_modified}.")
        if self.create_backup:
            print("Original files are backed up with a '.bak' extension.")

    def processFile(self, file_path):

        try:
            # Read the original content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()

            # Perform the replacement
            # For literal string replacement, str.replace() is ideal
            new_content = original_content.replace(
                self.old_string, self.new_string)
            # If you wanted regex replacement:
            # new_content = old_string_re.sub(new_string, original_content)

            self.files_processed += 1

            if new_content != original_content:
                self.files_modified += 1
                print(f"  Modifying: {file_path}")

                if self.create_backup:
                    backup_path = file_path + ".bak"
                    # copy2 preserves metadata
                    shutil.copy2(file_path, backup_path)
                    print(f"    Backup created at: {backup_path}")

                # Write the new content back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            else:
                # Uncomment to see all files checked
                print(f"  No changes needed for: {file_path}")

        except Exception as e:
            print(f"  Error processing {file_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Finds and replaces a string in file or files within a directory.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "path",
        help="The path to the file or directory to search (e.g., './my_files')."
    )
    parser.add_argument(
        "old_string",
        help="The string to find (e.g., 'holdSeeds/')."
    )
    parser.add_argument(
        "new_string",
        help="The string to replace with (e.g., 'piSeeds/')."
    )
    parser.add_argument(
        "-p", "--pattern",
        help="Optional: Glob-style file pattern (e.g., '*.txt', 'config*.json').\n"
             "Matches files ending with the pattern. Default: None (all files)."
    )
    parser.add_argument(
        "-nob", "--no-backup",
        action="store_false",
        dest="create_backup",
        help="Do NOT create .bak backup files. Use with caution!"
    )
    parser.add_argument(
        "-nr", "--no-recursive",
        action="store_false",
        dest="recursive",
        help="Do NOT search subdirectories. Only process files in the top-level directory."
    )

    args = parser.parse_args()

    # Define your specific strings for the problem context
    # (These can be overridden by command line arguments, or you can hardcode them here
    # if you always want to replace these specific strings without args)
    # default_old_string = "holdSeeds/"
    # default_new_string = "piSeeds/"

    find_and_replace_in_files(
        path=args.path,
        old_string=args.old_string,
        new_string=args.new_string,
        file_pattern=args.pattern,
        create_backup=args.create_backup,
        recursive=args.recursive
    )
