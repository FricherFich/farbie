import os
from parse_fixture_idea import (
    fixture_idea_to_fixture_idea_dict,
    split_fixture_idea_dict_into_channels,
    identify_clip_length
)
from prepare_envelope_xml import end_list_to_envelope_xml
from append_to_clip_slots import add_new_clip_to_als


def add_fixture_idea_as_clip_to_ableton_project(als_file: str, fixture_idea_file: str):
    """Fügt genau einen Clip aus der TXT-Datei in die angegebene .als-Datei ein."""
    base_filename = os.path.basename(fixture_idea_file)
    clip_name = os.path.splitext(base_filename)[0]

    clip_length = identify_clip_length(fixture_idea_file)
    print(f"Importiere Clip '{clip_name}' (Länge: {clip_length} Beats)")

    txt_dict = fixture_idea_to_fixture_idea_dict(fixture_idea_file)
    end_dict = split_fixture_idea_dict_into_channels(txt_dict)
    envelope_xml = end_list_to_envelope_xml(end_dict)

    add_new_clip_to_als(
        old_als_file=als_file,
        new_als_file=als_file,
        clip_name=clip_name,
        scene_name=clip_name,
        clip_length=clip_length,
        envelope_entry=envelope_xml
    )