import xml.etree.ElementTree as ET
from als_xml_conversion import als_file_to_xml_file


def get_red_channel_by_fixture_name(fixture_name):
    fixture_kanalbelegung = {
        "PAR64.3L":65,
        "PAR64.2L":72,
        "PAR64.1L":76,
        "PAR64.1R":92,
        "PAR64.2R":88,
        "PAR64.3R":81,
        "Apestick01":1,
        "Apestick02":5,
        "Apestick03":9,
        "Apestick04":13,
        "Apestick05":17,
        "Apestick06":21,
        "Apestick07":25,
        "Apestick08":29,
        "Apestick09":33,
        "Apestick10":37

    }

    return fixture_kanalbelegung.get(fixture_name)

def find_dmxis_channel_mapping(als_file_path):

    xml_temp_file = "xml_temp_to_find_channel.xml"
    als_file_to_xml_file(als_file_path, xml_temp_file)




    # XML-Datei einlesen
    tree = ET.parse(xml_temp_file)
    root = tree.getroot()

    # Dictionary erstellen
    param_dict = {}

    # Alle 'PluginFloatParameter'-Elemente finden
    for parameter in root.findall(".//PluginFloatParameter"):
        # ParameterName und AutomationTarget extrahieren
        parameter_name = parameter.find(".//ParameterName").get('Value')
        automation_target = parameter.find(".//AutomationTarget").get('Id')

        # Mapping im Dictionary hinzufügen
        param_dict[parameter_name] = automation_target

    return param_dict


