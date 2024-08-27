import os
from rich import print
import concurrent.futures
import time
from Processor import FileProcessor
from DelDupFiles import DelDuplicateFiles
start_time = time.time()
# Constants
ORIGIN_FOLDER = "./carti"
# ORIGIN_FOLDER = "./Carti dezvlotare personala"
os.chdir("D:/11/")



def manage_file_process(file, processor):
    return processor.manage_file(file)

def subMain(processor,designed_folder ):
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = []  # Initialize the list to store futures
        for file in os.listdir(designed_folder):
            full_path = os.path.join(designed_folder, file)
            # Submit the file processing task to the executor
            future = executor.submit(manage_file_process, full_path, processor)
            futures.append(future)  # Add the future to the list

        # Handle the results as they are completed
        for future in concurrent.futures.as_completed(futures):
            try:
                _ = future.result()  # Get the result of the future to handle any exceptions
            except Exception as e:
                print(f"[red]Error processing file: {e}[/red]")

    
processor = FileProcessor(ORIGIN_FOLDER)
if ORIGIN_FOLDER == './carti':
    for folder in os.listdir(ORIGIN_FOLDER):
        designed_folder = os.path.join(ORIGIN_FOLDER, folder)
        processor.initDesignedFolder(designed_folder)
        
        subMain(processor,designed_folder)
else:
    processor.initDesignedFolder(ORIGIN_FOLDER)
    subMain(processor, ORIGIN_FOLDER)

print(
 f"[blue]{processor.count} total there were [/blue]"+
 f"[green]{processor.count_good} done right[/green]"
+ f" and [red]{processor.count_errors} errors [/red]"
+ f"\nThere are {processor.count_empty} Empty files "
)

end_time = time.time()
total_time = end_time - start_time
DelDuplicateFiles()

print(f"Total time: {total_time:.4f} seconds")