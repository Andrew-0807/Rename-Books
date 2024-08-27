import os 
import shutil 
from rich import print
import subprocess

os.chdir("d://11//")
count = 0
countgood = 0
countbad = 0
def makedir(dir):
    try:
        os.mkdir("./"+dir)
    except FileExistsError: # catch specific exception instead of all exceptions
        pass

for f in ["Errors", "Done", "Completed", "Processed"]:
    makedir(f)
    
# for file in os.listdir("./Books"):

#     try:
#         shutil.move("./Books/" + file , "./Processed")
#     except Exception as e:
#         print(e)
#         try: 
#             os.remove("./Books/" + file)
#         except:
#             pass
def RemoveDone(name, file):
    global count
    global countgood
    global countbad
    full_file_path = f"{name}/{file}"
    destination_path = "./Done"            
    try:
        shutil.move(full_file_path, destination_path)
        countgood +=1

    except Exception as e:

        try: 
            if "[Errno 2]" in str(e):
                os.remove(full_file_path)
                print(f"{file} is an empty file")


            
        except:
            pass
            # os.remove(full_file_path)
            # print(f"File {file} was [red]removed[/red] from {name} due to an [red1]error[/red1]: {e}. [red]It has fucked off![/red]")
        
        countbad +=1


# for file in os.listdir("./Books"):
#     if " - " in file:     
#         RemoveDone("./Books", file)

for file in os.listdir("./Completed"):
    count +=1
    if " - " in file: 
        try:
            if os.path.getsize(os.path.join("./Completed", file)) == 0:
                os.remove("./Completed/" + file )
                countbad +=1

        except:
            pass

        RemoveDone("./Completed", file)
    else:
        try:
            shutil.move("./Completed/" + file , "./carti")


        except Exception as e:
            print(e)
subprocess.run(["python", " D:/11/---Code/Split Batches.py"], capture_output=False)
print(f"[blue]From {count} file [/blue]there were [green] {countgood} done right[/green] and [red]{countbad} errors [/red]")
