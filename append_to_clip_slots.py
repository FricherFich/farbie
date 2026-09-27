import xml.etree.ElementTree as ET
import copy
import os
import re
from als_xml_conversion import als_to_xml_structure, prettify, prettified_xml_string_to_als


def append_to_existing_clipslot_list(root, clip_name: str, clip_current_end, clip_envelope_xml_content, scene_name: str):
    """Befuellt den naechsten freien ClipSlot unter den vorhandenen Clips mit den neuen Automationskurven."""

    # 1. Basis-Clip aus Slot 0 als Template holen
    track = root.find(".//Tracks/MidiTrack")
    if track is None:
        raise ValueError("Kein MidiTrack im Projekt gefunden.")

    base_clip = track.find(".//MainSequencer/ClipSlotList/ClipSlot[@Id='0']//MidiClip")
    if base_clip is None:
        raise ValueError("Kein Basis-MidiClip in Slot 0 als Vorlage gefunden.")

    # 2. Den naechsten freien ClipSlot suchen (wo <Value/> leer ist)
    clip_slots = track.findall(".//MainSequencer/ClipSlotList/ClipSlot")
    target_slot = None
    target_slot_index = -1

    for idx, slot in enumerate(clip_slots):
        val = slot.find("ClipSlot/Value")
        if val is not None and len(val) == 0:  # leerer Slot
            target_slot = slot
            target_slot_index = idx
            break

    if target_slot is None:
        raise RuntimeError(
            f"Kein freier ClipSlot mehr verfuegbar. Alle {len(clip_slots)} vorhandenen Slots sind belegt."
        )

    # 3. Vorlage kopieren und Parameter setzen
    new_clip = copy.deepcopy(base_clip)
    new_clip.set("Id", str(target_slot_index + 1))

    # Name setzen
    name_elem = new_clip.find("Name")
    if name_elem is not None:
        name_elem.set("Value", clip_name)

    # Laenge synchron fuer CurrentEnd, LoopEnd und OutMarker setzen
    str_len = str(clip_current_end)
    cur_end = new_clip.find("CurrentEnd")
    if cur_end is not None:
        cur_end.set("Value", str_len)

    loop_elem = new_clip.find("Loop")
    if loop_elem is not None:
        loop_end = loop_elem.find("LoopEnd")
        if loop_end is not None:
            loop_end.set("Value", str_len)
        out_marker = loop_elem.find("OutMarker")
        if out_marker is not None:
            out_marker.set("Value", str_len)

    # 4. Envelopes an der EXAKTEN Schema-Position ersetzen (direkt hinter TimeSignature)
    if clip_envelope_xml_content is not None:
        if isinstance(clip_envelope_xml_content, str):
            new_envelopes = ET.fromstring(clip_envelope_xml_content)
        else:
            new_envelopes = copy.deepcopy(clip_envelope_xml_content)

        old_env = new_clip.find("Envelopes")
        if old_env is not None:
            insert_pos = list(new_clip).index(old_env)
            new_clip.remove(old_env)
            new_clip.insert(insert_pos, new_envelopes)
        else:
            time_sig = new_clip.find("TimeSignature")
            insert_pos = list(new_clip).index(time_sig) + 1
            new_clip.insert(insert_pos, new_envelopes)

    # 5. In den leeren Ziel-Slot einhaengen
    slot_value = target_slot.find("ClipSlot/Value")
    slot_value.clear()
    slot_value.append(new_clip)

    # 6. Szene an target_slot_index umbenennen (Live 12 Schema: <LiveSet><Scenes><Scene>)
    scenes = root.findall(".//LiveSet/Scenes/Scene")
    if target_slot_index < len(scenes) and scene_name:
        scene_name_elem = scenes[target_slot_index].find("Name")
        if scene_name_elem is not None:
            scene_name_elem.set("Value", scene_name)

    return root


def add_new_clip_to_als(old_als_file, new_als_file, clip_name, scene_name, clip_length, envelope_entry):
    root = als_to_xml_structure(old_als_file)

    new_root = append_to_existing_clipslot_list(
        root,
        clip_name=clip_name,
        clip_current_end=clip_length,
        clip_envelope_xml_content=envelope_entry,
        scene_name=scene_name,
    )
    pretty_xml_string = prettify(new_root)

    prettified_xml_string_to_als(pretty_xml_string, new_als_file)
    return None