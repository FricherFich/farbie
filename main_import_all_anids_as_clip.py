import shutil
import os
from datetime import datetime
from append_as_clip_to_file import add_fixture_idea_as_clip_to_ableton_project

source_folder = "ANIDs_not_imported"
dest_folder = "ANIDs_imported"
project_folder = "vierter_versuch Project"


def finde_letzte_als_datei(im_ordner):
    alle_als_dateien = [f for f in os.listdir(im_ordner) if f.endswith('.als')]
    if not alle_als_dateien:
        raise FileNotFoundError(f"Keine .als-Dateien in '{im_ordner}' gefunden.")
    letzte_datei = sorted(alle_als_dateien)[-1]
    return os.path.join(im_ordner, letzte_datei)


def verarbeite_txt_dateien(quellordner, zielordner, workdir_project):
    if not os.path.exists(zielordner):
        os.makedirs(zielordner)

    txt_dateien = [f for f in os.listdir(quellordner) if f.endswith(".txt")]
    if not txt_dateien:
        print("Keine neuen TXT-Dateien zum Importieren gefunden.")
        return

    # 1. Basis-Projekt ermitteln und als Arbeitsdatei anlegen
    basis_als_datei = finde_letzte_als_datei(workdir_project)
    temp_als_datei = "TEMP.als"
    shutil.copy2(basis_als_datei, temp_als_datei)

    print(f"Basis-Projekt: {basis_als_datei}")
    print(f"Starte Batch-Import von {len(txt_dateien)} Datei(en)...")

    # 2. Alle Clips nacheinander in TEMP.als akkumulieren
    for dateiname in txt_dateien:
        voller_pfad = os.path.join(quellordner, dateiname)
        ziel_pfad = os.path.join(zielordner, dateiname)

        add_fixture_idea_as_clip_to_ableton_project(
            als_file=temp_als_datei,
            fixture_idea_file=voller_pfad
        )
        shutil.move(voller_pfad, ziel_pfad)

    # 3. Genau EINE neue Projektdatei mit Timestamp erstellen
    base_name = basis_als_datei.split("__")[0]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_ableton_file = f"{base_name}__{timestamp}.als"

    shutil.move(temp_als_datei, new_ableton_file)
    print(f"Erfolgreich abgeschlossen! Alle Clips gespeichert in: {new_ableton_file}")


if __name__ == "__main__":
    source_folder_txt_files = "ANIDs_not_imported"
    dest_folder_txt_files = "ANIDs_imported"
    workdir_ableton_project = "output"
    verarbeite_txt_dateien(source_folder_txt_files, dest_folder_txt_files, workdir_ableton_project)


