from parse_fixture_idea import fixture_idea_to_fixture_idea_dict, split_fixture_idea_dict_into_channels, identify_clip_length
from prepare_envelope_xml import end_list_to_envelope_xml
from append_to_clip_slots import add_new_clip_to_als
import shutil


def add_fixture_idea_as_clip_to_ableton_project(old_project_filename:str, new_project_filename: str, fixture_idea_file: str, stuetzstellen: str):
    
    with open(fixture_idea_file, 'r') as file:
        erste_zeile = file.readline().strip()  # strip() entfernt eventuell vorhandene Umbrüche am Ende
        if erste_zeile.startswith("//"):
            clip_name = erste_zeile[2:]
        else:
            clip_name = fixture_idea_file.split("/")[-1].split(".")[0]
    clip_length = identify_clip_length(fixture_idea_file, stuetzstelle = "first-order") #stuetzstelle ist hier nur ein Dummy
    print(f"{clip_name} hat die Clip length {clip_length}")

    shutil.copy2(old_project_filename, "TEMP.als")
    if stuetzstellen == "both":
        stuetzstellen = ["zero-order", "first-order"]
    else:
        stuetzstellen = [stuetzstellen]
    for stuetzstelle in stuetzstellen:
        anid_dict = fixture_idea_to_fixture_idea_dict(fixture_idea_file, stuetzstelle)
        end_dict = split_fixture_idea_dict_into_channels(anid_dict)
        envelope_xml = end_list_to_envelope_xml(end_dict)
        single_clip_name = clip_name + "_" + stuetzstelle[0]
        add_new_clip_to_als(old_als_file="TEMP.als",
                            new_als_file="TEMP.als",
                            clip_name=single_clip_name,
                            scene_name=single_clip_name,
                            clip_length=clip_length,
                            envelope_entry=envelope_xml)
    shutil.copy2("TEMP.als", new_project_filename)
    return



if __name__ == "__main__":
    fixture_idea_file = "dual_symmetry_2.anid"
    add_fixture_idea_as_clip_to_ableton_project("zweiter_versuch.als", "zweiter_versuch.als", fixture_idea_file=fixture_idea_file, stuetzstellen="both")