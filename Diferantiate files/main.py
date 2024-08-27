import os
import shutil
import concurrent.futures
from rich import print
# Define your folders

folder2 = os.path.normpath("D:\\11\\carti")  # This folder contains 2800 files
folder1 = os.path.normpath("D:\\11\\Processed\\carti")  # This folder contains 200 + the same 2800 files
output_folder = os.path.normpath('D:\\11\\UnProcessedFiles')  # Where you want to move/copy the unique files

def copy_or_move_file(file_name):
    src_path = os.path.join(folder2, file_name)
    dest_path = os.path.join(output_folder, file_name)
    
    try:
        # Copy the file
        shutil.copy2(src_path, dest_path)
        
        # Or move the file (uncomment if you want to move instead of copy)
        # shutil.move(src_path, dest_path)
        
        return f"[green1]Successfully copied/moved {file_name}\n"
    except Exception as e:
        return f"[red]Error processing {file_name}: {e}\n"

# Ensure output folder exists
for i in range (len(folder1)):
    folder_1 = os.listdir(folder1)
    folder_2 = os.listdir(folder2)

    os.makedirs(output_folder, exist_ok=True)
    
    # Get sets of filenames in both folders
    files_in_folder1 = set(os.listdir(os.path.join(folder1, folder_1[i])))
    files_in_folder2 = set(os.listdir(os.path.join(folder2, folder_2[i])))
    
    # Find files that are in folder2 but not in folder1
    unique_files_in_folder2 = files_in_folder2 - files_in_folder1
    # print(unique_files_in_folder2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    # Submit tasks to the executor
        futures = [executor.submit(copy_or_move_file, file_name) for file_name in unique_files_in_folder2]

        # Wait for all tasks to complete and print results
        for future in concurrent.futures.as_completed(futures):
            _ = future.result()

# Use ThreadPoolExecutor for parallel processing

print(f"\n[blue]Processed {len(unique_files_in_folder2)} unique files.")
