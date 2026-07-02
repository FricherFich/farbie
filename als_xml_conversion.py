from xml.dom import minidom
import gzip
import xml.etree.ElementTree as ET
import os
import re


def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="\t")

    # Remove lines that contain only whitespace
    pretty_xml = os.linesep.join([line for line in pretty_xml.splitlines() if line.strip()])

    return pretty_xml



def prettify_without_leerzeilen(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    ugly_xml = reparsed.toprettyxml(indent="\t")
    # Next line is a regex to remove multiple linebreaks
    pretty_xml = re.sub('\n+', '\n', ugly_xml)
    return pretty_xml


def als_file_to_xml_file(als_input_file_path, xml_output_file_path):
    """
    Diese Funktion entpackt eine .als-Datei und speichert die resultierende XML-Datei ab.
    """
    with gzip.open(als_input_file_path, 'rb') as f_in:
        with open(xml_output_file_path, 'wb') as f_out:
            f_out.write(f_in.read())

    return None



def parse_xml_file(file_path):
    """
    Diese Funktion interpretiert eine XML-Datei und gibt den Wurzelknoten des XML-Baums zurück.
    """
    tree = ET.parse(file_path)
    return tree.getroot()



def als_to_xml_structure(input_file_path:str):
    # Temporärer Pfad für die XML-Datei
    temp_xml_path = "temp.xml"
    # Dekomprimieren Sie die .als-Datei und speichern Sie sie als XML-Datei
    als_file_to_xml_file(input_file_path, temp_xml_path)

    # Interpretieren Sie die XML-Datei
    root = parse_xml_file(temp_xml_path)

    return root

def xml_file_to_als(input_xml_filename, output_als_filename):
    root = parse_xml_file(input_xml_filename)
    xml_structure_to_als(root, output_file_path=output_als_filename)



def xml_structure_to_als(root, output_file_path):

    # Temporärer Pfad für die XML-Datei
    temp_xml_path = "new_temp.xml"
    # Pfad für die neue .als-Datei
    #output_file_path = "new_file.als"


    # Speichern Sie die Änderungen an der XML-Datei
    tree = ET.ElementTree(root)
    tree.write(temp_xml_path)

    # Komprimieren Sie die XML-Datei und speichern Sie sie als .als-Datei
    compress_and_save_as_als(temp_xml_path, output_file_path)

def prettified_xml_string_to_als(pretty_xml_string, new_als_name):
    #output_xml = append_to_existing_clipslot_list(current_xml_structure, clip_name, clip_current_end, clip_envelope_xml_content)


    # Write the output to a file
    temp_xml_path = "new_temp.xml"

    with open(temp_xml_path, 'w') as f:
        f.write(pretty_xml_string)

    compress_and_save_as_als(temp_xml_path, new_als_name)



def compress_and_save_as_als(xml_input_file_path, output_file_path):
    """
    Diese Funktion nimmt eine XML-Datei, speichert sie ab und komprimiert sie dann als .als-Datei.
    """
    with open(xml_input_file_path, 'rb') as f_in:
        with gzip.open(output_file_path, 'wb') as f_out:
            f_out.write(f_in.read())

