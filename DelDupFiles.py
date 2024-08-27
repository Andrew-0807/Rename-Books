import os
import concurrent.futures


# Define your folders
class DelDuplicateFiles():
    def __init__(self):
        self.folder1 = os.path.normpath("D:\\11\\carti")  # This folder contains 2800 files
        self.folder2 = os.path.normpath("D:\\11\\Processed\\carti")  # This folder contains 200 + the same 2800 files
        self.subfolders = set(os.listdir(self.folder1)).intersection(set(os.listdir(self.folder2)))

        for subfolder in self.subfolders:
            self.process_folder(subfolder)

    def delete_file(self, file_path):
        try:
            os.remove(file_path)
            return f"Successfully deleted {os.path.basename(file_path)}"
        except Exception as e:
            return f"Error deleting {os.path.basename(file_path)}: {e}"

    def process_folder(self, subfolder):
        subfolder1 = os.path.join(self.folder1, subfolder)
        subfolder2 = os.path.join(self.folder2, subfolder)

        # Check if both subfolders exist
        if os.path.exists(subfolder1) and os.path.exists(subfolder2):
            # Get sets of filenames in both subfolders
            files_in_subfolder1 = set(os.listdir(subfolder1))
            files_in_subfolder2 = set(os.listdir(subfolder2))

            # Find files that are in both subfolders (duplicates)
            duplicate_files = files_in_subfolder1.intersection(files_in_subfolder2)

            # Process duplicate files by deleting them
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = [
                    executor.submit(
                        self.delete_file,
                        os.path.join(subfolder1, file_name)
                    ) for file_name in duplicate_files
                ]
                for future in concurrent.futures.as_completed(futures):
                    # print(future.result())
                    pass

            print(f"Processed {len(duplicate_files)} duplicate files in subfolder: {subfolder}")

    # Get subfolders common to both folder1 and folder2

    # Process each common subfolder
