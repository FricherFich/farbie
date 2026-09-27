import shutil
import os
from datetime import datetime
from append_as_clip_to_file import add_fixture_idea_as_clip_to_ableton_project

source_folder = "ANIDs_not_imported"
dest_folder = "ANIDs_imported"

def finde_letzte_als_datei(im_ordner):
    # Liste alle Dateien im Ordner auf, die auf ".als" enden
    alle_als_dateien = [f for f in os.listdir(im_ordner) if f.endswith('.als')]

    # Wenn keine Dateien gefunden werden, gebe eine entsprechende Nachricht zurück
    if not alle_als_dateien:
        return "Es wurden keine .als-Dateien gefunden."

    # Sortiere die Dateien alphabetisch und nehme die letzte
    letzte_datei = sorted(alle_als_dateien)[-1]

    return os.path.join(im_ordner, letzte_datei)

def verarbeite_txt_dateien(quellordner, zielordner):
    # Sicherstellen, dass der Zielordner existiert
    if not os.path.exists(zielordner):
        os.makedirs(zielordner)
    
    # Durch alle Dateien im Quellordner gehen
    for dateiname in os.listdir(quellordner):
        if dateiname.endswith(".txt"):
            voller_pfad = os.path.join(quellordner, dateiname)
            ziel_pfad = os.path.join(zielordner, dateiname)
            
            # hinzufuegen
            my_path = "vierter_versuch Project"
            old_ableton_file = finde_letzte_als_datei(my_path)
            new_ableton_file = "".join(old_ableton_file.split("__")[0]) + "__" + datetime.now().strftime("%Y%m%d%H%M%S") + ".als"
            add_fixture_idea_as_clip_to_ableton_project(old_ableton_file, new_ableton_file, fixture_idea_file=voller_pfad, stuetzstellen="both")

            # Datei verschieben
            shutil.move(voller_pfad, ziel_pfad)


if __name__ == "__main__":
    verarbeite_txt_dateien(source_folder, dest_folder)


