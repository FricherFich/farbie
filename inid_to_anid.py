import shutil
from datetime import datetime

input_filepath = "input.txt"


dest_filename = f'{datetime.now().strftime("%Y-%m-%d_%M-%S")}.txt'
dest_filepath = f"TXTs_not_imported/{dest_filename}"

shutil.copy(input_filepath, dest_filepath)
print(f"Datei erfolgreich kopiert nach {dest_filepath}")