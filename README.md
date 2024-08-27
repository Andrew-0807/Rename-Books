# Project 
### Made for Marius 
#### in the course of 2 weeks 
# Instalation 
## Requerments 
- python
- ollama
Installation of ollama the model needed is gemma2:2b
```bat
ollama pull gemma2:2b
```
# Usage

1. Make a folder carti place all the books there
```bat
mkdir D:/11/carti
```
2. Run split batches 
```bat
 python D:\11\---Code\Split Batches.py
```
3. Run rename books until the count is 0 and duplicates deleted are 0
```bat
python D:\11\---Code\RenameBooks.py
```
4. Run remove errors 
```bat
python D:\11\---Code\RemoveErrors.py
```
### **Note**
If there are **errors** in the renaming process (the books don't have the corect name format) those books will be rerouted to the carti folder and split within the existing folders again please go back to step 3.
## Warning sometimes it creates empty files 
The empty files are deleted by step 4.
