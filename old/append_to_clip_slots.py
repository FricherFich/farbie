import xml.etree.ElementTree as ET
import copy

def append_to_existing_clipslot_list(root, clip_name, clip_current_end, clip_envelope_xml_content):
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
    new_clipslot.find('.//CurrentEnd').set('Value', str(clip_current_end))
    
    midi_clip = new_clipslot.find('.//MidiClip')
    old_envelopes = midi_clip.find('.//Envelopes')

    if clip_envelope_xml_content is None:
        new_envelopes = ET.Element('Envelopes')
    else:
        new_envelopes = ET.fromstring(clip_envelope_xml_content)

    # remove old envelopes and add new one
    midi_clip.remove(old_envelopes)
    midi_clip.append(new_envelopes)

    # Append the new_clipslot to the ClipSlotList
    base_clipslot_parent = root.find('.//ClipSlotList')
    base_clipslot_parent.append(new_clipslot)

    # Return the updated XML structure as a string
    #return ET.tostring(root, encoding='unicode')
    return root
