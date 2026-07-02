import shutil
from datetime import datetime

input_filepath = "input.inid"


dest_filename = f'{datetime.now().strftime("%Y-%m-%d_%M-%S")}.anid'
dest_filepath = f"ANIDs_not_imported/{dest_filename}"

shutil.copy(input_filepath, dest_filepath)
print(f"Datei erfolgreich kopiert nach {dest_filepath}")