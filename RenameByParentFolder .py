import os 
from rich import print
os.chdir("D:/11/Carti diverse/Clasice/Straine")
folders = os.listdir()
for folder in folders:
    for file in folder:
        print(file)
        print (folder)
        # rename the file to "foldername - file"
        os.rename(file, folder +  " - " + file )
