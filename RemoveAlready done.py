import os
import shutil
try:
    os.mkdir("./Done")
except:
    pass

def RemoveDone(name, file):
    full_file_path = f"{name}/{file}"
    destination_path = "./Done"
    if " - " in file:            
        try:
            shutil.move(full_file_path, destination_path)
        except Exception as e:
            print(e)
            try: 
                os.remove(f"{name}/" + file)
            except:
                pass

directory = "./Carti 2"
files = os.listdir(directory)
for file in files:
    RemoveDone(directory, file)