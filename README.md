# 📚 Rename-Books
Automated scripts for bulk-renaming eBooks, built for easy folder management and error handling.
Developed for Marius over two weeks – powered by Python and Ollama's Gemma2:2B model.

# 🚀 Features
- Batch rename books: Easily rename eBooks in bulk from one central folder.

- Error correction: Automatically reroutes books with incorrect naming formats for review.

- Duplicate removal: Clears duplicates to keep your collection tidy.

- Empty file clean-up: Detects and removes empty files from folders.

- Simple update workflow: Pull the latest code updates using Git.

- No-frills command-line usage: Just a few Python commands to run the tool.

# 🛠 Requirements
Python

Ollama with the model gemma2:2b
### To install:

```bash
ollama pull gemma2:2b
```
#📦 Installation
## Create the target books folder:

```bash
mkdir D:/11/carti
```
#### Download and set up the code in D:/11/---Code.

##⚙️ Usage
####Split batches:
```bash
python D:/11/---Code/Split Batches.py
```
#### Rename books (repeat until count is 0 and no duplicates remain):
```bash
python D:/11/---Code/RenameBooks.py
```
#### Remove errors:

```bash
python D:/11/---Code/RemoveErrors.py
```
### ✨ Note
If any books are incorrectly renamed, they will be moved back to the carti folder for retrying steps 2–3.

### ⚠️ Warnings
Sometimes empty files may be generated; step 3 will remove them.

If you update the code, run:

```bash
cd D:/11/---Code
git pull
```
The code isn’t perfect; you may encounter bugs.

### 💬 Contact
For bug reports or questions, please open an issue on GitHub.

### 📄 License
See the LICENSE file for details.

### 🏷️ About
No website or project topics yet.


Use at your own risk – the author is not responsible for any damage or lost books!
