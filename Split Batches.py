import os
import shutil
import math
os.chdir("D://11//")
def split_files(target_folder, max_files_per_folder):
    # Get a list of all files in the target folder
    files = [f for f in os.listdir(target_folder) if os.path.isfile(os.path.join(target_folder, f))]

    # Calculate how many folders we'll need to split the files into
    num_folders = math.ceil(len(files) / max_files_per_folder)

    # Create an empty list to store the folder names
    folder_names = []

    for i in range(num_folders):
        # Generate the name of this folder (e.g. "folder_001", "folder_002", etc.)
        folder_name = f"Folder_{i+1:03d}"

        # Create the new folder if it doesn't already exist
        os.makedirs(os.path.join(target_folder, folder_name), exist_ok=True)

        # Add this folder name to our list of folder names
        folder_names.append(folder_name)

    # Loop over all the files in the target folder
    for i, file in enumerate(files):
        # Get the absolute path to this file
        file_path = os.path.join(target_folder, file)

        # Move the file into its corresponding folder (using modulo for wrap-around)
        shutil.move(file_path, os.path.join(target_folder, folder_names[i % num_folders]))

# Example usage:
split_files("./carti", 3000)