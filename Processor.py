import time 
import shutil
import os
from rich import print
from openai import OpenAI
import logging

# Set up logging
logging.basicConfig(filename='processed_files.log', level=logging.INFO)

# Set up variables
DESTINATION_FOLDER = "./Completed"
ERRORS_FOLDER = "./Errors"


class FileProcessor( ):
    def __init__(self, origin_folder):
        self.origin_folder = origin_folder
        self.client =  OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama',  
    )
        self.initDirectory()
        
        self.count = 0
        self.count_good = 0
        self.count_errors = 0
        self.count_empty = 0

    def initDesignedFolder(self, designed_folder):
        self.designed_folder = designed_folder
        print(f"[purple]Initializing {self.designed_folder}...\n\n")
        #set os working directory

    def initDirectory(self):
        os.makedirs(DESTINATION_FOLDER, exist_ok=True) 
        os.makedirs(ERRORS_FOLDER, exist_ok=True)
        os.makedirs("./Books", exist_ok=True)

    def mark_processed_file(self, file):
        
        # Add **processed** to the start of the file name
        
        # Rename the file with new_file
        os.makedirs(f"./Processed/{self.designed_folder}", exist_ok=True)

        shutil.copy2(file, os.path.join(f"./Processed/",file))
        print(f"[green1]File {file} processed\n")
        # Log the processed file
        logging.info(f"Processed file: {file}")

    def standardize_document_name(self, name):
        self.count += 1
        response = self.client.chat.completions.create(
            model='gemma2:2b',
            messages=[
                {
                    'role': 'system',
                    'content': """Your job is to format book titles in this exact format: 'Author - Title'. 
                        Rules:
                        1. Only output 'Author - Title'. Nothing else.
                        1,5. if the file is already formated just leavit as that and give it as a responce be careful to be already formated it needs to contaion the following charachters ' - '
                        2. Analyse the content givn the author usualy is at the start of the sentance .If you do not know the author, use 'Anonymous'. Do not guess the author's name.
                        3. Do not add any extra text, comments, symbols, emojis, or punctuation. No extra words. Only 'Author - Title'.
                        4. If the title has a known author, format it correctly. If the title is unknown, still format it as 'Anonymous - Title'.
                        5. No explanations. No extra characters. No symbols like '**', emojis, or punctuation.
                        6. Do not change the language in wich the text is provided adapt to use that language
                        7.if document name is emptyh or just spaces place **NoName** as its name """
                },        

                {'role': 'user', 'content': "Harry potter - j.k. Rowling"},
                {'role': 'assistant', 'content': "J K Rowling - Harry Potter"},

                {'role': 'user', 'content': "1365135809.pdf"},
                {'role': 'assistant', 'content': "Anonymous - 1365135809.pdf"},
                
                {'role': 'user', 'content': "j_k_rowling_harry_potter"},
                {'role': 'assistant', 'content': "J K Rowling - Harry Potter"},
                
                {'role': 'user', 'content': "khalil-gilbert-the-phrophet-book.pdf"},
                {'role': 'assistant', 'content': "Khalil Gibran - The Prophet"},
                
                {'role': 'user', 'content': "Amazing words"},
                {'role': 'assistant', 'content': "Anonymous - Amazing Words"},
                
                {'role': 'user', 'content': "(Mindf_ck Series 1) Abby, S.T. - The Risk.epub"},
                {'role': 'assistant', 'content': "S.T. Abby - The Risk (Mindf_ck Series 1)"},
                
                {'role': 'user', 'content': "Haralamb_Zincă_Interpolul_transmite_arestaţi"},
                {'role': 'assistant', 'content': "Haralamb Zincă  - Interpolul transmite arestaţi"},
                
                {'role': 'user', 'content': "Jack_L_Chalker,_Effinger,_Resnick_The_Red_Tape_War"},
                {'role': 'assistant', 'content': "Jack L Chalker - The Red Tape War"},
                
                {'role': 'user', 'content': "Hategan, Ioan - Filippo Scolari"},
                {'role': 'assistant', 'content': "Hategan, Ioan - Filippo Scolari"},
                
                {'role': 'user', 'content': "Harwey Rex - Canionul Blestemat(biblioteca noastra)"},
                {'role': 'assistant', 'content': "Harwey Rex - Canionul Blestemat"},
                
                {'role': 'user', 'content': "Jean_de_la_Hire_Cei_Trei_Cercetaşi_V23_Ultimul_deportat_1_0_"},
                {'role': 'assistant', 'content': "Jean de la Hire - Cei Trei Cercetaşi V23 Ultimul deportat"},

                {'role': 'user', 'content': "CNSAS - Romanii in Epoca de Aur"},
                {'role': 'assistant', 'content': "CNSAS - Romanii in Epoca de Aur"},
                
                {'role': 'user', 'content': "4.LISA_KLEYPAS_-_Scandal_in_primavara(biblioteca noastra)"},
                {'role': 'assistant', 'content': "Lisa Kleypas - Scandal in primavara"},

                {'role': 'user', 'content': name}
            ],
        )
        return response.choices[0].message.content

    def manage_extension(self, extension):
        return "." + extension.lower().replace(" · version 1", "").replace(" · versiunea 1", "")

    def replace_special_chars(self, filename):
        return "".join(filename.replace("\n", "").replace("file name is:\\", "").replace(".", " ").replace("_", " ").replace(" - ", "***").replace("***", " - ").replace("biblioteca noastra","").replace("{","").replace("}","").replace("(","").replace(")",""))

    def manage_file(self, file_name):

        new_filename = self.standardize_document_name("".join(file_name.split(".")[:-1]).replace("biblioteca noastra",""))
        new_filename = self.replace_special_chars(new_filename)
        
        if " - " not in new_filename:
            return False
        
        extension = os.path.splitext(os.path.join(self.origin_folder, file_name))[1].lower()
        if extension not in new_filename:
            new_filename += extension
        return self.copy_and_rename(file_name,new_filename)

    def copy_and_rename(self, original_file, new_filename):
        try:
            # print (f"copying {original_file} to {new_filename}")
            #copy the file from the origin folder to the destination folder and rename it to the new filename
            copied_file= shutil.copy2(os.path.join(self.designed_folder, os.path.basename(original_file)), DESTINATION_FOLDER + "/" + os.path.basename(new_filename))
            # print (f"[blue]{copied_file}")
            # Fix for empty files
            file_size = os.path.getsize(copied_file)
            if file_size == 0:
                os.remove(copied_file)
                self.count_empty += 1
                return False
            
            print (f"\n[green]Succesfuly renamed [/green] {original_file} to {new_filename}")

            # Rename the copied file to match the new filename
            self.mark_processed_file(original_file)
            # os.rename(copied_file, new_filename
            return True

        except Exception as e:
            print(f"[red1] Error copying and renaming file: {str(e)}")
            try:
                shutil.copy2(original_file, "./Books")
            except:
                pass
            return False
        