from dmx_channel_mapping import (
    find_dmxis_channel_mapping,
    get_red_channel_by_fixture_name,
    get_laser_velocity_channel,
    get_laser_direction_channel
)
from constants import ur_filename

DIRECTION_MAPPING = {
    "R": 0,  # Clockwise
    "0": 150,  # No rotation
    "L": 255  # Counter clockwise
}


def convert_to_number(s: str):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            print(f"Error: {s} kann nicht in eine Zahl umgewandelt werden!")
            return None


def parse_hex_color(color: str):
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return red, green, blue


def apply_zero_order_hold(data_points: list) -> list:
    """Hält den vorherigen Wert bis exakt vor den nächsten Stützpunkt (Sprungfunktion)."""
    if len(data_points) <= 1:
        return data_points

    enhanced_list = []
    for i in range(len(data_points) - 1):
        enhanced_list.append(data_points[i])
        this_pos_str, this_val = data_points[i].split('#')
        next_pos_str, _ = data_points[i + 1].split('#')

        if float(this_pos_str) < float(next_pos_str):
            enhanced_list.append(f"{next_pos_str}#{this_val}")

    enhanced_list.append(data_points[-1])
    return enhanced_list


def fixture_idea_to_fixture_idea_dict(file_name: str):
    result = []

    with open(file_name, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip()]
        lines = [line for line in lines if not line.startswith('//')]

        for line in lines:
            fixture_identifier, data_points_str = line.split(':')
            fixture_identifier = fixture_identifier.strip()
            data_points_str = data_points_str.replace(" ", "")
            data_points = [dp for dp in data_points_str.split(';') if dp]

            is_direction = fixture_identifier.endswith("_Direction")
            is_velocity = fixture_identifier.endswith("_Velocity")

            # Direction ist per Spezifikation immer eine Stufenfunktion
            if is_direction:
                data_points = apply_zero_order_hold(data_points)

            for data_point in data_points:
                position_str, val_str = data_point.split('#')
                position = convert_to_number(position_str)

                if is_direction:
                    dir_key = val_str.upper()
                    if dir_key not in DIRECTION_MAPPING:
                        raise ValueError(f"Ungültige Direction '{val_str}' in: {line}")
                    result.append({
                        "fixture_identifier": fixture_identifier,
                        "type": "direction",
                        "position": position,
                        "value": DIRECTION_MAPPING[dir_key]
                    })

                elif is_velocity:
                    vel_val = int(val_str)
                    if not (0 <= vel_val <= 255):
                        raise ValueError(f"Velocity {vel_val} außerhalb 0-255 in: {line}")
                    result.append({
                        "fixture_identifier": fixture_identifier,
                        "type": "velocity",
                        "position": position,
                        "value": vel_val
                    })

                else:
                    red, green, blue = parse_hex_color(val_str)
                    result.append({
                        "fixture_identifier": fixture_identifier,
                        "type": "rgb",
                        "position": position,
                        "red": red,
                        "green": green,
                        "blue": blue
                    })

    return result


def identify_clip_length(fixture_idea_file: str):
    data = fixture_idea_to_fixture_idea_dict(fixture_idea_file)
    return max((item["position"] for item in data), default=0)


def split_fixture_idea_dict_into_channels(fixture_idea_dict: list):
    channel_specific_list = []
    dmxis_channel_to_automation_target = find_dmxis_channel_mapping(ur_filename())

    for move in fixture_idea_dict:
        fixture_name = move["fixture_identifier"]
        move_type = move.get("type", "rgb")

        if move_type == "rgb":
            red_channel = get_red_channel_by_fixture_name(fixture_name)
            if red_channel is None:
                raise ValueError(f"Unbekanntes RGB-Gerät: {fixture_name}")

            color_channels = {
                "red": red_channel,
                "green": red_channel + 1,
                "blue": red_channel + 2
            }
            for color_name, dmx_nr in color_channels.items():
                fader_key = f"Fader {dmx_nr}"
                if fader_key not in dmxis_channel_to_automation_target:
                    raise KeyError(f"{fader_key} nicht im Ableton-Template gefunden!")
                channel_specific_list.append({
                    "automation_pointee_id": dmxis_channel_to_automation_target[fader_key],
                    "time": move["position"],
                    "value": move[color_name]
                })

        elif move_type == "velocity":
            laser_base = fixture_name.replace("_Velocity", "")
            dmx_nr = get_laser_velocity_channel(laser_base)
            if dmx_nr is None:
                raise ValueError(f"Unbekannter Laser für Velocity: {fixture_name}")

            channel_specific_list.append({
                "automation_pointee_id": dmxis_channel_to_automation_target[fader_key := f"Fader {dmx_nr}"],
                "time": move["position"],
                "value": move["value"]
            })

        elif move_type == "direction":
            laser_base = fixture_name.replace("_Direction", "")
            dmx_nr = get_laser_direction_channel(laser_base)
            if dmx_nr is None:
                raise ValueError(f"Unbekannter Laser für Direction: {fixture_name}")

            channel_specific_list.append({
                "automation_pointee_id": dmxis_channel_to_automation_target[fader_key := f"Fader {dmx_nr}"],
                "time": move["position"],
                "value": move["value"]
            })

    return channel_specific_list