from xml.dom import minidom
import gzip
import xml.etree.ElementTree as ET
import os
import re


def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    # Explizit utf-8 deklarieren, damit <?xml version="1.0" encoding="utf-8"?> im Header steht
    pretty_xml_bytes = reparsed.toprettyxml(indent="\t", encoding="utf-8")
    pretty_xml = pretty_xml_bytes.decode("utf-8")

    # Leerzeilen entfernen
    pretty_xml = os.linesep.join([line for line in pretty_xml.splitlines() if line.strip()])

    return pretty_xml


def prettify_without_leerzeilen(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    ugly_xml = reparsed.toprettyxml(indent="\t", encoding="utf-8").decode("utf-8")
    pretty_xml = re.sub(r'\n+', '\n', ugly_xml)
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


def als_to_xml_structure(input_file_path: str):
    temp_xml_path = "temp.xml"
    als_file_to_xml_file(input_file_path, temp_xml_path)
    root = parse_xml_file(temp_xml_path)
    return root


def xml_file_to_als(input_xml_filename, output_als_filename):
    root = parse_xml_file(input_xml_filename)
    xml_structure_to_als(root, output_file_path=output_als_filename)


def xml_structure_to_als(root, output_file_path):
    temp_xml_path = "new_temp.xml"
    tree = ET.ElementTree(root)
    tree.write(temp_xml_path, encoding="utf-8", xml_declaration=True)
    compress_and_save_as_als(temp_xml_path, output_file_path)


def prettified_xml_string_to_als(pretty_xml_string, new_als_name):
    temp_xml_path = "new_temp.xml"

    # Zwingend UTF-8 beim Schreiben unter Windows angeben
    with open(temp_xml_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_string)

    compress_and_save_as_als(temp_xml_path, new_als_name)


def compress_and_save_as_als(xml_input_file_path, output_file_path):
    """
    Diese Funktion nimmt eine XML-Datei, speichert sie ab und komprimiert sie dann als .als-Datei.
    """
    with open(xml_input_file_path, 'rb') as f_in:
        with gzip.open(output_file_path, 'wb') as f_out:
            f_out.write(f_in.read())