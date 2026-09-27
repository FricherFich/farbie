import xml.etree.ElementTree as ET
from als_xml_conversion import als_file_to_xml_file

# Startkanal (Rot) für RGB-Fixtures
FIXTURE_RGB_KANALBELEGUNG = {
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
    "Spot2": 143,
    "Spot3": 122,
    "Spot4": 129,
    "Spot5": 150,
    "Spot6": 136,
    "Laser1": 74,
    "Laser2": 81,
    "Laser3": 88,
    "Laser4": 95
}

FIXTURE_LASER_VELOCITY = {
    "Laser1": 78,
    "Laser2": 85,
    "Laser3": 92,
    "Laser4": 99
}

FIXTURE_LASER_DIRECTION = {
    "Laser1": 79,
    "Laser2": 86,
    "Laser3": 93,
    "Laser4": 100
}


def get_red_channel_by_fixture_name(fixture_name: str):
    return FIXTURE_RGB_KANALBELEGUNG.get(fixture_name)


def get_laser_velocity_channel(laser_name: str):
    return FIXTURE_LASER_VELOCITY.get(laser_name)


def get_laser_direction_channel(laser_name: str):
    return FIXTURE_LASER_DIRECTION.get(laser_name)


def find_dmxis_channel_mapping(als_file_path: str):
    xml_temp_file = "xml_temp_to_find_channel.xml"
    als_file_to_xml_file(als_file_path, xml_temp_file)

    tree = ET.parse(xml_temp_file)
    root = tree.getroot()

    param_dict = {}
    for parameter in root.findall(".//PluginFloatParameter"):
        param_name_elem = parameter.find(".//ParameterName")
        target_elem = parameter.find(".//AutomationTarget")
        if param_name_elem is not None and target_elem is not None:
            param_dict[param_name_elem.get('Value')] = target_elem.get('Id')

    return param_dict