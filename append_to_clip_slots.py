import xml.etree.ElementTree as ET
import copy
import os
import re
from als_xml_conversion import als_to_xml_structure, prettify, prettified_xml_string_to_als


def append_to_existing_clipslot_list(root, clip_name:str, clip_current_end, clip_envelope_xml_content, scene_name:str):
    """fuegt einen neuen Clip unter den letzten Clip hinzu, dessen Automasierung in clip_envelope_xml_content übergeben wird"""


    # Parse the XML document
    #root = ET.fromstring(current_xml_structure)

    # Find the ClipSlot with Id="0"
    base_clipslot = root.find(".//ClipSlot[@Id='0']")

    # If no base_clipslot is found, raise an error
    if base_clipslot is None:
        raise ValueError('No base ClipSlot found')

    # Make a copy of the base_clipslot
    new_clipslot = copy.deepcopy(base_clipslot)

    # Update the Id attribute of the new_clipslot
    clipslot_ids = [int(clipslot.get('Id')) for clipslot in root.findall('.//ClipSlot') if clipslot.get('Id') is not None]
    max_id = max(clipslot_ids)
    new_clipslot.set('Id', str(max_id + 1))

    # Update the Name, CurrentEnd and Envelopes in the new_clipslot
    new_clipslot.find('.//Name').set('Value', clip_name)
    #new_clipslot.find('.//CurrentEnd').set('Value', str(clip_current_end))


    #proxy_test
    new_clipslot.find('.//CurrentEnd').set('Value', '100')

    
    midi_clip = new_clipslot.find('.//MidiClip')
    old_envelopes = midi_clip.find('.//Envelopes')

    if clip_envelope_xml_content is not None:
        new_envelopes = ET.fromstring(clip_envelope_xml_content) #TODO evtl. unnoetig, da bereits als XML-Struktur gegeben
        # remove old envelopes and add new one
        midi_clip.remove(old_envelopes)
        midi_clip.append(new_envelopes)

    # Append the new_clipslot to the ClipSlotList
    base_clipslot_parent = root.find('.//ClipSlotList')
    base_clipslot_parent.append(new_clipslot)



    # Neue Codezeilen, um den FreezeSequencer-Bereich zu bearbeiten
    freeze_sequencer = root.find('.//FreezeSequencer')
    if freeze_sequencer is not None:
        freeze_clip_slot_list = freeze_sequencer.find('.//ClipSlotList')
        if freeze_clip_slot_list is not None:
            # Der erste ClipSlot dient als Vorlage für den neuen ClipSlot
            first_clip_slot = freeze_clip_slot_list.find('.//ClipSlot')
            new_clip_slot = copy.deepcopy(first_clip_slot)
            # Die ID des neuen ClipSlots wird auf den richtigen Wert gesetzt
            new_clip_slot.attrib['Id'] = str(len(freeze_clip_slot_list))
            # Fügt den neuen ClipSlot in die ClipSlotList ein
            freeze_clip_slot_list.append(new_clip_slot)



    # Neue Codezeilen, um den SceneNames-Bereich zu bearbeiten
    scene_names = root.find('.//SceneNames')
    if scene_names is not None:
        # Die erste Szene dient als Vorlage für die neue Szene
        first_scene = scene_names.find('.//Scene')
        new_scene = copy.deepcopy(first_scene)
        # Die ID und der Wert der neuen Szene werden auf die richtigen Werte gesetzt
        new_scene.attrib['Id'] = str(len(scene_names))
        new_scene.attrib['Value'] = scene_name
        # Fügt die neue Szene in die SceneNames-Liste ein
        scene_names.append(new_scene)

    return root






def add_new_clip_to_als(old_als_file, new_als_file, clip_name, scene_name, clip_length, envelope_entry):
    root = als_to_xml_structure(old_als_file)

    new_root = append_to_existing_clipslot_list(root, clip_name=clip_name, clip_current_end=clip_length, clip_envelope_xml_content=envelope_entry, scene_name=scene_name)
    pretty_xml_string = prettify(new_root)

    prettified_xml_string_to_als(pretty_xml_string, new_als_file)
    return None



