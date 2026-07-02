from lxml import etree
from als_xml_conversion import decompress_als_file, xml_file_to_als



"""Ziel dieser Funktionen ist es, dass die DMXis-Kanaele 1 bis 127 ansteuerbar sind. Hierfür muss das vorhandene als-File ein mal modifiziert werden"""

def modify_xml_file(input_file, output_file):
    # XML-Datei einlesen
    tree = etree.parse(input_file)
    root = tree.getroot()
    
    # durch alle PluginFloatParameter-Elemente iterieren
    for parameter in root.findall('.//PluginFloatParameter'):
        # Id-Wert abrufen
        id_value = int(parameter.get('Id'))
        
        # ParameterName und ParameterId aktualisieren
        parameter_name = parameter.find('.//ParameterName')
        parameter_id = parameter.find('.//ParameterId')
        
        # Stellen Sie sicher, dass ParameterName und ParameterId existieren
        if parameter_name is not None and parameter_id is not None:
            # ParameterName und ParameterId auf den neuen Wert setzen
            parameter_name.set('Value', str(id_value + 1))
            parameter_id.set('Value', str(id_value + 15))
        
    # Verändertes XML-Tree in eine neue Datei schreiben
    tree.write(output_file)


def modify_als_file(input_als_file, output_als_file):

    xml_file="temp_modify_als_file.xml"
    decompress_als_file(input_file_path=input_als_file, output_file_path=xml_file)
    
    xml_output_file = "output_modify_als_files.xml"
    modify_xml_file(input_file=xml_file, output_file=xml_output_file)

    xml_file_to_als(input_xml_filename=xml_output_file, output_als_filename=output_als_file)

