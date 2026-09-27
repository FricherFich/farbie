import xml.etree.ElementTree as ET
from als_xml_conversion import als_file_to_xml_file


def get_red_channel_by_fixture_name(fixture_name):
    fixture_kanalbelegung_old = {
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

    fixture_kanalbelegung = {
        "Tube01": 1,
        "Tube02": 5,
        "Tube03": 9,
        "Tube04": 13,
        "Tube05": 17,
        "Tube06": 21,
        "Tube07": 25,
        "Tube08": 29,
        "Tube09": 33,
        "Tube10": 37,
        "Spot1": 115,
    "Spot2":143,
    "Spot3":122,
    "Spot4":129,
    "Spot5":150,
    "Spot6":136,
        "Laser1": 74,
    "Laser2": 81,
    "Laser3": 88,
    "Laser4":95
    }

    fixture_kanalbelegung_laser_velocities = {
        "Laser1": 78,
    "Laser2": 85,
    "Laser3":92,
    "Laser4":99
    }

    fixture_kanalbelegung_laser_directions = {
        "Laser1": 79,
    "Laser2": 86,
    "Laser3":93,
    "Laser4":100
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


