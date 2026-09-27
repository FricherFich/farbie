from dmx_channel_mapping import find_dmxis_channel_mapping, get_red_channel_by_fixture_name
from constants import ur_filename

def convert_to_number(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            print(f"Error: {s} kann nicht in eine Zahl umgewandelt werden!")
            return None

def fixture_idea_to_fixture_idea_dict_old(file_name_fixture_idea):
    # Resultierende Liste initialisieren
    result = []
    
    # Datei öffnen
    with open(file_name_fixture_idea, 'r') as file:
        # Alle Zeilen lesen
        lines = file.readlines()
        
        # Jede Zeile durchgehen
        for line in lines:
            # Einzelne Tupel trennen (entweder durch Semikolon oder Zeilenumbruch getrennt)
            tuples = line.strip().split(';')
            
            # Jedes Tupel durchgehen
            for tuple in tuples:
                # Teile des Tupels trennen
                parts = tuple.split(':')
                fixture_identifier = parts[0]
                position = convert_to_number(parts[1])
                
                # RGB-Werte trennen
                rgb = parts[2].split('-')
                red = int(rgb[0])
                green = int(rgb[1])
                blue = int(rgb[2])
                
                # Neues Dictionary erstellen und zur Liste hinzufügen
                result.append({"fixture_identifier": fixture_identifier, 
                               "position": position, 
                               "red": red, 
                               "green": green, 
                               "blue": blue})
    return result


def parse_hex_color(color):
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return red, green, blue

def fixture_idea_to_fixture_idea_dict(file_name, stuetzstelle:str):
    # Resultierende Liste initialisieren
    result = []
    
    # Datei öffnen
    with open(file_name, 'r') as file:
        # Alle Zeilen lesen und Leerzeilen ignorieren
        lines = [line.strip() for line in file if line.strip()]

        lines = [line for line in lines if not line.strip().startswith('//')] #filtere //-Zeilen als Kommentarzeilen
        
        # Jede Zeile durchgehen
        for line in lines:
            # Einzelne fixture_identifiers und Datenpunkte trennen
            fixture_identifier, data_points_str = line.strip().split(':')
            

            # leerzeichen entfernen
            data_points_str = data_points_str.replace(" ", "")

            # Einzelne Datenpunkte trennen
            data_points = data_points_str.split(';')

            if stuetzstelle == "first-order":
                pass
            elif stuetzstelle == "zero-order":
                enhanced_list = []
                for i, data_point in enumerate(data_points[:-1]):
                    enhanced_list.append(data_point)
                    this_position_str, this_color_str = data_points[i].split('#')
                    next_position_str, next_color_str = data_points[i+1].split("#")
                    enhanced_list.append(f"{next_position_str}#{this_color_str}") #dieser Color wird bis zur nächsten Position weitergeführt
                enhanced_list.append(data_points[-1]) # letzter Punkt wird einfach übernommen
                data_points = enhanced_list.copy()

            else:
                raise ValueError(f"stuetzstelle = {stuetzstelle} ist unbekannt")
            
            # Jeden Datenpunkt durchgehen
            for data_point in data_points:
                # Teile des Datenpunkts trennen
                position_str, color_str = data_point.split('#')
                position = convert_to_number(position_str)
                
                # RGB-Werte trennen und von Hexadezimal in Dezimal umwandeln
                red, green, blue = parse_hex_color(color_str)
                
                # Neues Dictionary erstellen und zur Liste hinzufügen
                result.append({"fixture_identifier": fixture_identifier, 
                               "position": position, 
                               "red": red, 
                               "green": green, 
                               "blue": blue})
    return result



def identify_clip_length(fixture_idea_file:str, stuetzstelle:str):
    list_ = fixture_idea_to_fixture_idea_dict(fixture_idea_file, stuetzstelle)
    max_length = 0
    for single_dict in list_:
        the_position = single_dict.get("position")
        if the_position > max_length:
            max_length = the_position
    return max_length


def split_fixture_idea_dict_into_channels(fixture_idea_dict:list):
    channel_specific_list = []
    dmxis_channel_to_automation_target = find_dmxis_channel_mapping(ur_filename())
    for single_fixture_move in fixture_idea_dict:
        fixture_name = single_fixture_move["fixture_identifier"]
        fixture_red_dmx_channel = get_red_channel_by_fixture_name(fixture_name)
        fixture_dmx_channels = {"red": fixture_red_dmx_channel,
                            "green": fixture_red_dmx_channel+1,
                            "blue": fixture_red_dmx_channel+2}
        fixture_automation_target = {k: dmxis_channel_to_automation_target["Fader "+str(v)] for k,v in fixture_dmx_channels.items()}

        for single_color_channel_name in ["red", "green", "blue"]:
            payload = {
                "automation_pointee_id": fixture_automation_target[single_color_channel_name],
                "time": single_fixture_move["position"],
                "value": single_fixture_move[single_color_channel_name]  # Echter DMX-Wert 0 bis 255
            }
            channel_specific_list.append(payload)

    return channel_specific_list