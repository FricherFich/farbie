import xml.etree.ElementTree as ET

def end_list_to_envelope_xml(input_list):
    # Oberstes Elternelement erstellen
    root = ET.Element('Envelopes')  # Sie können den Namen des Tags nach Ihren Bedürfnissen ändern
    
    # Wurzel-Element erstellen
    envelopes = ET.SubElement(root, 'Envelopes')

    # Eindeutige automation_pointee_ids extrahieren
    unique_ids = set(item['automation_pointee_id'] for item in input_list)

    # Erstellen Sie für jede eindeutige automation_pointee_id ein ClipEnvelope-Element
    for clip_id, pointee_id in enumerate(unique_ids, start=2):
        clip_envelope = ET.SubElement(envelopes, 'ClipEnvelope', Id=str(clip_id))
        
        envelope_target = ET.SubElement(clip_envelope, 'EnvelopeTarget')
        ET.SubElement(envelope_target, 'PointeeId', Value=pointee_id)
        
        automation = ET.SubElement(clip_envelope, 'Automation')
        events = ET.SubElement(automation, 'Events')
        
        # Hinzufügen des ersten FloatEvents
        ET.SubElement(events, 'FloatEvent', Id="0", Time="-63072000", Value="0")

        # Erstellen Sie für jeden Eintrag in der Eingabeliste ein FloatEvent-Element
        for event_id, item in enumerate((item for item in input_list if item['automation_pointee_id'] == pointee_id), start=1):
            ET.SubElement(events, 'FloatEvent', Id=str(event_id), Time=str(item['time']), Value=str(item['value']))

        # Hinzufügen der restlichen XML-Struktur
        automation_transform = ET.SubElement(automation, 'AutomationTransformViewState')
        ET.SubElement(automation_transform, 'IsTransformPending', Value="false")
        ET.SubElement(automation_transform, 'TimeAndValueTransforms')

        loop_slot = ET.SubElement(clip_envelope, 'LoopSlot')
        ET.SubElement(loop_slot, 'Value')

        scroller_time_preserver = ET.SubElement(clip_envelope, 'ScrollerTimePreserver')
        ET.SubElement(scroller_time_preserver, 'LeftTime', Value="0")
        ET.SubElement(scroller_time_preserver, 'RightTime', Value="0")

    # XML-Struktur in String konvertieren
    xml_str = ET.tostring(root, encoding='unicode')

    return xml_str





def save_xml_to_file(xml_str, file_path):
    # Parsing XML string to ElementTree
    root = ET.fromstring(xml_str)
    
    # Einrücken der XML-Struktur
    indent(root)


    # Erstellen Sie ein neues ElementTree-Objekt
    tree = ET.ElementTree(root)

    # Schreiben Sie das ElementTree-Objekt in eine Datei
    tree.write(file_path, encoding='unicode', xml_declaration=True)



def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i