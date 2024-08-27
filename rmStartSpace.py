import os

for file in os.listdir("./Done from carti 6"):
    if file.startswith(" "):
        try:
            os.rename(file, file[1:])
        except:
            pass