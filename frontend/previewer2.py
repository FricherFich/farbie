import math
import os
import sys
import tkinter as tk
from tkinter import filedialog
import pygame

# ==============================================================================
# DEFAULT DEMO PROGRAMM (Vollständige Demo aller 20 Geräte & Parameter)
# ==============================================================================
DEFAULT_SCRIPT = """// Voll-Setup Demo: 16 RGB-Pixel + 4 Laserworld EL-300
Spot1:0#000000;0#FFFFFF;0.5#000000;15.5#000000;15.5#00FFFF;16#000000
Spot2:0#000000;0.5#000000;0.5#FFFFFF;1#000000;15#000000;15#00FFFF;15.5#000000;16#000000
Spot3:0#000000;1#000000;1#FFFFFF;1.5#000000;14.5#000000;14.5#00FFFF;15#000000;16#000000
Tube01:0#000000;1.5#000000;1.5#FFFFFF;2#000000;14#000000;14#00FFFF;14.5#000000;16#000000
Tube02:0#000000;2#000000;2#FFFFFF;2.5#000000;13.5#000000;13.5#00FFFF;14#000000;16#000000
Tube03:0#000000;2.5#000000;2.5#FFFFFF;3#000000;13#000000;13#00FFFF;13.5#000000;16#000000
Tube04:0#000000;3#000000;3#FFFFFF;3.5#000000;12.5#000000;12.5#00FFFF;13#000000;16#000000
Tube05:0#000000;3.5#000000;3.5#FFFFFF;4#000000;12#000000;12#00FFFF;12.5#000000;16#000000
Tube06:0#000000;4#000000;4#FFFFFF;4.5#000000;11.5#000000;11.5#00FFFF;12#000000;16#000000
Tube07:0#000000;4.5#000000;4.5#FFFFFF;5#000000;11#000000;11#00FFFF;11.5#000000;16#000000
Tube08:0#000000;5#000000;5#FFFFFF;5.5#000000;10.5#000000;10.5#00FFFF;11#000000;16#000000
Tube09:0#000000;5.5#000000;5.5#FFFFFF;6#000000;10#000000;10#00FFFF;10.5#000000;16#000000
Tube10:0#000000;6#000000;6#FFFFFF;6.5#000000;9.5#000000;9.5#00FFFF;10#000000;16#000000
Spot4:0#000000;6.5#000000;6.5#FFFFFF;7#000000;9#000000;9#00FFFF;9.5#000000;16#000000
Spot5:0#000000;7#000000;7#FFFFFF;7.5#000000;8.5#000000;8.5#00FFFF;9#000000;16#000000
Spot6:0#000000;7.5#000000;7.5#FFFFFF;8#000000;8#00FFFF;8.5#000000;16#000000
Laser1:0#00FF80;4#00FF80;4#0080FF;8#0080FF;8#FF0055;12#FF0055;12#00FF80;16#00FF80
Laser1_Velocity:0#70;4#240;8#60;12#255;16#70
Laser1_Direction:0#R;4#L;8#R;12#L;16#R
Laser2:0#00FF80;4#00FF80;4#0080FF;8#0080FF;8#FF0055;12#FF0055;12#00FF80;16#00FF80
Laser2_Velocity:0#110;4#160;8#80;12#210;16#110
Laser2_Direction:0#L;4#R;8#L;12#R;16#L
Laser3:0#00FF80;4#00FF80;4#0080FF;8#0080FF;8#FF0055;12#FF0055;12#00FF80;16#00FF80
Laser3_Velocity:0#110;4#160;8#80;12#210;16#110
Laser3_Direction:0#R;4#L;8#R;12#L;16#R
Laser4:0#00FF80;4#00FF80;4#0080FF;8#0080FF;8#FF0055;12#FF0055;12#00FF80;16#00FF80
Laser4_Velocity:0#70;4#240;8#60;12#255;16#70
Laser4_Direction:0#L;4#R;8#L;12#R;16#L"""

# ==============================================================================
# TRACK KLASSEN & DSL-PARSER
# ==============================================================================
def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    hex_str = hex_str.strip().lstrip('#')
    if len(hex_str) != 6:
        return (0, 0, 0)
    try:
        return (
            int(hex_str[0:2], 16),
            int(hex_str[2:4], 16),
            int(hex_str[4:6], 16),
        )
    except ValueError:
        return (0, 0, 0)


class ColorTrack:
    """Verwaltet Stützpunkte mit linearer Farbinterpolation und Snap-Cut-Unterstützung."""
    def __init__(self, name: str, keyframes: list[tuple[float, tuple[int, int, int]]]):
        self.name = name
        self.keyframes = sorted(keyframes, key=lambda x: x[0])
        self.segments = []
        for i in range(len(self.keyframes) - 1):
            t1, c1 = self.keyframes[i]
            t2, c2 = self.keyframes[i + 1]
            if t1 < t2:
                self.segments.append((t1, c1, t2, c2))

    def get_color(self, beat: float) -> tuple[int, int, int]:
        if not self.keyframes:
            return (0, 0, 0)
        if beat <= self.keyframes[0][0]:
            return self.keyframes[0][1]
        if beat >= self.keyframes[-1][0]:
            return self.keyframes[-1][1]

        for t1, c1, t2, c2 in self.segments:
            if t1 <= beat < t2:
                factor = (beat - t1) / (t2 - t1)
                r = int(c1[0] + factor * (c2[0] - c1[0]))
                g = int(c1[1] + factor * (c2[1] - c1[1]))
                b = int(c1[2] + factor * (c2[2] - c1[2]))
                return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

        return self.keyframes[-1][1]


class VelocityTrack:
    """Verwaltet Laser-Geschwindigkeit (0–255) mit linearer Interpolation."""
    def __init__(self, name: str, keyframes: list[tuple[float, float]]):
        self.name = name
        self.keyframes = sorted(keyframes, key=lambda x: x[0])
        self.segments = []
        for i in range(len(self.keyframes) - 1):
            t1, v1 = self.keyframes[i]
            t2, v2 = self.keyframes[i + 1]
            if t1 < t2:
                self.segments.append((t1, v1, t2, v2))

    def get_value(self, beat: float) -> float:
        if not self.keyframes:
            return 0.0
        if beat <= self.keyframes[0][0]:
            return max(0.0, min(255.0, float(self.keyframes[0][1])))
        if beat >= self.keyframes[-1][0]:
            return max(0.0, min(255.0, float(self.keyframes[-1][1])))

        for t1, v1, t2, v2 in self.segments:
            if t1 <= beat < t2:
                factor = (beat - t1) / (t2 - t1)
                val = v1 + factor * (v2 - v1)
                return max(0.0, min(255.0, val))

        return max(0.0, min(255.0, float(self.keyframes[-1][1])))


class DirectionTrack:
    """Verwaltet Rotationsrichtung ('L', '0', 'R') als Sprungfunktion (keine Interpolation)."""
    def __init__(self, name: str, keyframes: list[tuple[float, str]]):
        self.name = name
        self.keyframes = sorted(keyframes, key=lambda x: x[0])

    def get_value(self, beat: float) -> str:
        if not self.keyframes:
            return '0'
        if beat < self.keyframes[0][0]:
            return '0'
        if beat >= self.keyframes[-1][0]:
            return self.keyframes[-1][1]

        val = '0'
        for b, d in self.keyframes:
            if b <= beat:
                val = d
            else:
                break
        return val


def parse_dsl_content(content: str):
    lines = content.splitlines()
    comment = 'Unbenanntes Programm'
    color_tracks = {}
    vel_tracks = {}
    dir_tracks = {}
    max_beat = 0.0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('//') or line.startswith('#'):
            if comment == 'Unbenanntes Programm':
                comment = line.lstrip('/#').strip()
            continue

        if ':' not in line:
            continue

        dev_name, data = line.split(':', 1)
        dev_name = dev_name.strip()
        tokens = data.split(';')

        # 1. Geschwindigkeits-Track (_Velocity)
        if dev_name.endswith('_Velocity'):
            laser_key = dev_name[:-9]
            keyframes = []
            for token in tokens:
                token = token.strip()
                if not token or '#' not in token:
                    continue
                b_str, v_str = token.split('#', 1)
                try:
                    beat = float(b_str.strip())
                    val = float(v_str.strip())
                    keyframes.append((beat, val))
                    if beat > max_beat:
                        max_beat = beat
                except ValueError:
                    continue
            if keyframes:
                vel_tracks[laser_key] = VelocityTrack(dev_name, keyframes)

        # 2. Richtungs-Track (_Direction)
        elif dev_name.endswith('_Direction'):
            laser_key = dev_name[:-10]
            keyframes = []
            for token in tokens:
                token = token.strip()
                if not token or '#' not in token:
                    continue
                b_str, d_str = token.split('#', 1)
                try:
                    beat = float(b_str.strip())
                    direction = d_str.strip().upper()
                    if direction in ('L', '0', 'R'):
                        keyframes.append((beat, direction))
                        if beat > max_beat:
                            max_beat = beat
                except ValueError:
                    continue
            if keyframes:
                dir_tracks[laser_key] = DirectionTrack(dev_name, keyframes)

        # 3. Farb-Track (SpotX, TubeXX, LaserX)
        else:
            keyframes = []
            for token in tokens:
                token = token.strip()
                if not token or '#' not in token:
                    continue
                b_str, h_str = token.split('#', 1)
                try:
                    beat = float(b_str.strip())
                    rgb = hex_to_rgb(h_str)
                    keyframes.append((beat, rgb))
                    if beat > max_beat:
                        max_beat = beat
                except ValueError:
                    continue
            if keyframes:
                color_tracks[dev_name] = ColorTrack(dev_name, keyframes)

    if max_beat <= 0:
        max_beat = 4.0

    return comment, color_tracks, vel_tracks, dir_tracks, max_beat


# ==============================================================================
# UI ELEMENTE (Slider & Buttons)
# ==============================================================================
class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label='', unit='', is_int=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.unit = unit
        self.is_int = is_int
        self.dragging = False

    def draw(self, screen, font):
        pygame.draw.rect(screen, (38, 42, 50), self.rect, border_radius=4)
        span = self.max_val - self.min_val
        ratio = (self.val - self.min_val) / span if span > 0 else 0
        fill_w = int(self.rect.width * ratio)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
        pygame.draw.rect(screen, (60, 125, 235), fill_rect, border_radius=4)
        pygame.draw.rect(screen, (85, 95, 110), self.rect, 1, border_radius=4)

        knob_x = self.rect.x + fill_w
        pygame.draw.circle(screen, (240, 240, 250), (knob_x, self.rect.centery), 8)
        pygame.draw.circle(screen, (20, 22, 28), (knob_x, self.rect.centery), 3)

        val_str = (f'{int(self.val)}' if self.is_int else f'{self.val:.2f}') + self.unit
        text = font.render(f'{self.label}: {val_str}', True, (210, 215, 225))
        screen.blit(text, (self.rect.x, self.rect.y - 20))

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_val(event.pos[0])
            return True
        return False

    def update_val(self, mouse_x):
        ratio = (mouse_x - self.rect.x) / self.rect.width
        ratio = max(0.0, min(1.0, ratio))
        self.val = self.min_val + ratio * (self.max_val - self.min_val)
        if self.is_int:
            self.val = round(self.val)


class Button:
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.active = False

    def draw(self, screen, font):
        color = (55, 105, 195) if self.active else (42, 46, 56)
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        pygame.draw.rect(screen, (75, 85, 100), self.rect, 1, border_radius=6)
        txt_surf = font.render(self.text, True, (240, 240, 245))
        screen.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.callback()


# ==============================================================================
# HAUPTPROGRAMM (STAGE PREVIEWER ENGINE)
# ==============================================================================
class LightingPreviewer:
    def __init__(self, initial_source=None):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption('Lichtanlagen Previewer – 16 RGB Pixel & 4 Laserworld EL-300')

        self.width = 1280
        self.height = 760
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()

        self.font_main = pygame.font.SysFont('Segoe UI', 14)
        self.font_bold = pygame.font.SysFont('Segoe UI', 14, bold=True)
        self.font_large = pygame.font.SysFont('Segoe UI', 20, bold=True)
        self.font_small = pygame.font.SysFont('Consolas', 11)
        self.font_mini = pygame.font.SysFont('Consolas', 10, bold=True)

        self.current_beat = 0.0
        self.playing = True
        self.loop = True

        # Rotationswinkel der 4 Laser (in Radiant)
        self.laser_angles = {'Laser1': 0.0, 'Laser2': 0.0, 'Laser3': 0.0, 'Laser4': 0.0}
        self.prev_scrub_beat = 0.0

        # UI Bedienelemente
        self.bpm_slider = Slider(
            x=50, y=690, w=180, h=14, min_val=40, max_val=220, initial_val=120, label='Tempo', unit=' BPM', is_int=True
        )
        self.timeline_slider = Slider(
            x=280, y=690, w=680, h=14, min_val=0, max_val=16.0, initial_val=0, label='Timeline (Scrubbing)', unit=' Beats', is_int=False
        )

        self.btn_play = Button(x=50, y=630, w=90, h=30, text='Pause', callback=self.toggle_play)
        self.btn_rewind = Button(x=150, y=630, w=80, h=30, text='Reset', callback=self.rewind)
        self.btn_loop = Button(x=240, y=630, w=90, h=30, text='Loop: An', callback=self.toggle_loop)
        self.btn_open = Button(x=1080, y=630, w=150, h=30, text='Datei laden...', callback=self.open_file_dialog)

        # Gerätebezeichnungen nach Setup-Spezifikation
        self.par_spots = ['Spot1', 'Spot2', 'Spot3', 'Spot4', 'Spot5', 'Spot6']
        self.tubes = [f'Tube{i:02d}' for i in range(1, 11)]
        self.lasers = ['Laser1', 'Laser2', 'Laser3', 'Laser4']

        # Hardware-Geometrie für Bühnenaufbau
        self.setup_geometry()

        # Daten laden
        if initial_source and os.path.exists(initial_source):
            with open(initial_source, 'r', encoding='utf-8') as f:
                self.raw_data = f.read()
        else:
            self.raw_data = DEFAULT_SCRIPT

        self.load_program_data(self.raw_data)

    def setup_geometry(self):
        """Konfiguriert die exakten X/Y-Positionen aller Elemente gemäß 'lichtanlage_aufbau.png'."""
        self.truss_y = 240
        self.floor_y = 560
        self.center_x = 640

        # PAR-Spots Koordinaten
        # Links: Spot1 oben (110), Spot2 unten (170), Spot3 oben (230)
        # Rechts: Spot4 oben (1050), Spot5 unten (1110), Spot6 oben (1170)
        self.spot_coords = {
            'Spot1': (110, 185, True),   # (cx, cy, is_above_truss)
            'Spot2': (170, 295, False),
            'Spot3': (230, 185, True),
            'Spot4': (1050, 185, True),
            'Spot5': (1110, 295, False),
            'Spot6': (1170, 185, True),
        }

        # 10 Tubes: 5 links der Mittelsäule, 5 rechts der Mittelsäule
        tube_x_left = [345, 405, 465, 525, 585]
        tube_x_right = [695, 755, 815, 875, 935]
        all_tube_x = tube_x_left + tube_x_right
        self.tube_coords = {f'Tube{i+1:02d}': all_tube_x[i] for i in range(10)}

        # 4 Laserworld EL-300 RGB (auf der Traverse sitzend)
        # Laser1 und 2 links, Laser3 und 4 rechts
        self.laser_coords = {
            'Laser1': 405,
            'Laser2': 525,
            'Laser3': 755,
            'Laser4': 875,
        }

    def load_program_data(self, content: str):
        self.comment, self.color_tracks, self.vel_tracks, self.dir_tracks, self.max_beat = parse_dsl_content(content)
        total_beats = math.ceil(self.max_beat)
        if total_beats % 4 != 0:
            total_beats = math.ceil(total_beats / 4) * 4

        self.timeline_length = max(4.0, float(total_beats))
        self.timeline_slider.max_val = self.timeline_length
        self.current_beat = 0.0
        self.prev_scrub_beat = 0.0

    def toggle_play(self):
        self.playing = not self.playing
        self.btn_play.text = 'Pause' if self.playing else 'Play'
        self.btn_play.active = not self.playing

    def rewind(self):
        self.current_beat = 0.0
        self.timeline_slider.val = 0.0
        self.prev_scrub_beat = 0.0
        for k in self.laser_angles:
            self.laser_angles[k] = 0.0

    def toggle_loop(self):
        self.loop = not self.loop
        self.btn_loop.text = 'Loop: An' if self.loop else 'Loop: Aus'

    def open_file_dialog(self):
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            filepath = filedialog.askopenfilename(
                title='Lichtsteuerungs-Textdatei wählen',
                filetypes=[('Textdateien', '*.txt'), ('Alle Dateien', '*.*')],
            )
            root.destroy()
            if filepath and os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.load_program_data(f.read())
        except Exception as e:
            print(f'Fehler beim Laden der Datei: {e}')

    def get_color(self, dev_name: str) -> tuple[int, int, int]:
        track = self.color_tracks.get(dev_name)
        return track.get_color(self.current_beat) if track else (0, 0, 0)

    def get_laser_state(self, laser_name: str):
        color = self.get_color(laser_name)
        vel_track = self.vel_tracks.get(laser_name)
        vel = vel_track.get_value(self.current_beat) if vel_track else 0.0

        dir_track = self.dir_tracks.get(laser_name)
        direction = dir_track.get_value(self.current_beat) if dir_track else '0'
        return color, vel, direction

    def update(self, dt: float):
        # Wenn der Nutzer nicht scrubbt, Timeline automatisch weiterschalten
        if not self.timeline_slider.dragging:
            if self.playing:
                beats_per_second = self.bpm_slider.val / 60.0
                d_beat = beats_per_second * dt
                self.current_beat += d_beat
                if self.current_beat >= self.timeline_length:
                    if self.loop:
                        self.current_beat = self.current_beat % self.timeline_length
                    else:
                        self.current_beat = self.timeline_length
                        self.playing = False
                        self.btn_play.text = 'Play'

                # Laser-Drehwinkel während der Wiedergabe fortschreiben
                for lname in self.lasers:
                    _, vel, direction = self.get_laser_state(lname)
                    dir_sign = 1.0 if direction == 'R' else (-1.0 if direction == 'L' else 0.0)
                    # Drehzahl: bei Velocity 255 ca. 1.8 Umdrehungen pro Sekunde
                    angular_speed = dir_sign * (vel / 255.0) * (2.0 * math.pi * 1.8)
                    self.laser_angles[lname] = (self.laser_angles[lname] + angular_speed * dt) % (2.0 * math.pi)

            self.timeline_slider.val = self.current_beat
            self.prev_scrub_beat = self.current_beat
        else:
            # Manuelles Scrubben der Timeline
            d_beat = self.timeline_slider.val - self.prev_scrub_beat
            self.current_beat = self.timeline_slider.val
            beats_per_second = self.bpm_slider.val / 60.0
            sim_dt = (d_beat / beats_per_second) if beats_per_second > 0 else 0.0

            for lname in self.lasers:
                _, vel, direction = self.get_laser_state(lname)
                dir_sign = 1.0 if direction == 'R' else (-1.0 if direction == 'L' else 0.0)
                angular_speed = dir_sign * (vel / 255.0) * (2.0 * math.pi * 1.8)
                self.laser_angles[lname] = (self.laser_angles[lname] + angular_speed * sim_dt) % (2.0 * math.pi)

            self.prev_scrub_beat = self.current_beat

    def draw_stage(self):
        # Dunkler Bühnenraum
        self.screen.fill((10, 11, 15))

        # Separate Surface für additive Lichtmischung (Glow, Beams, Halos)
        glow_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # -------------------------------------------------------------
        # 1. HARDWARE-STRUKTUR (Traverse, T-Kopplung und Mittelsäule)
        # -------------------------------------------------------------
        # Bühnenboden
        pygame.draw.line(self.screen, (25, 29, 36), (0, self.floor_y), (self.width, self.floor_y), 2)

        # Mittelsäule (Stativ)
        col_w = 18
        col_rect = pygame.Rect(self.center_x - col_w // 2, self.truss_y, col_w, self.floor_y - self.truss_y)
        pygame.draw.rect(self.screen, (30, 33, 40), col_rect)
        pygame.draw.rect(self.screen, (50, 55, 68), col_rect, 1)

        # Stativ-Bodenplatte
        pygame.draw.rect(self.screen, (40, 44, 54), (self.center_x - 35, self.floor_y - 6, 70, 8), border_radius=2)

        # Horizontale Truss (Doppelrohr-Traverse)
        truss_left, truss_right = 60, 1220
        pygame.draw.line(self.screen, (50, 54, 65), (truss_left, self.truss_y - 4), (truss_right, self.truss_y - 4), 3)
        pygame.draw.line(self.screen, (40, 44, 52), (truss_left, self.truss_y + 4), (truss_right, self.truss_y + 4), 3)
        # Truss-Gitterstreben (Zickzack)
        for tx in range(truss_left, truss_right, 24):
            pygame.draw.line(self.screen, (32, 36, 44), (tx, self.truss_y - 4), (tx + 12, self.truss_y + 4), 1)
            pygame.draw.line(self.screen, (32, 36, 44), (tx + 12, self.truss_y + 4), (tx + 24, self.truss_y - 4), 1)

        # T-Kopplung / Stativ-Kranz
        pygame.draw.rect(self.screen, (55, 60, 75), (self.center_x - 16, self.truss_y - 8, 32, 18), border_radius=3)

        # -------------------------------------------------------------
        # 2. TUBES (Hängend von der Traverse)
        # -------------------------------------------------------------
        tube_w = 16
        tube_h = 240
        tube_top_y = self.truss_y + 12

        for name, cx in self.tube_coords.items():
            color = self.get_color(name)
            r, g, b = color
            intensity = max(r, g, b) / 255.0

            # Halteklammer an der Traverse
            pygame.draw.rect(self.screen, (45, 50, 60), (cx - 4, self.truss_y, 8, 12))

            # Röhren-Glow (additiv)
            if intensity > 0.02:
                # Weicher Halo
                pygame.draw.ellipse(glow_surf, (r, g, b, int(22 * intensity)), (cx - 45, tube_top_y - 15, 90, tube_h + 30))
                pygame.draw.ellipse(glow_surf, (r, g, b, int(55 * intensity)), (cx - 24, tube_top_y - 5, 48, tube_h + 10))
                pygame.draw.ellipse(glow_surf, (r, g, b, int(90 * intensity)), (cx - 12, tube_top_y, 24, tube_h))
                # Bodenreflexion
                pygame.draw.ellipse(glow_surf, (r, g, b, int(40 * intensity)), (cx - 20, self.floor_y - 10, 40, 20))

            # Röhren-Diffusor
            tube_rect = pygame.Rect(cx - tube_w // 2, tube_top_y, tube_w, tube_h)
            if intensity > 0:
                pygame.draw.rect(self.screen, color, tube_rect, border_radius=tube_w // 2)
                # Weißer Glanzkern
                core_r = min(255, int(r * 0.4 + 255 * 0.6))
                core_g = min(255, int(g * 0.4 + 255 * 0.6))
                core_b = min(255, int(b * 0.4 + 255 * 0.6))
                pygame.draw.rect(self.screen, (core_r, core_g, core_b), (cx - 2, tube_top_y + 4, 4, tube_h - 8), border_radius=2)
            else:
                pygame.draw.rect(self.screen, (22, 25, 32), tube_rect, border_radius=tube_w // 2)
                pygame.draw.rect(self.screen, (38, 42, 52), tube_rect, 1, border_radius=tube_w // 2)

            # Endkappen
            pygame.draw.ellipse(self.screen, (45, 50, 60), (cx - tube_w // 2, tube_top_y - 2, tube_w, 5))
            pygame.draw.ellipse(self.screen, (45, 50, 60), (cx - tube_w // 2, tube_top_y + tube_h - 3, tube_w, 5))

            # Labels & Farbcode
            lbl_name = self.font_mini.render(name, True, (130, 140, 155))
            self.screen.blit(lbl_name, lbl_name.get_rect(center=(cx, tube_top_y + tube_h + 16)))
            hex_code = f'#{r:02X}{g:02X}{b:02X}'
            lbl_hex = self.font_mini.render(hex_code, True, color if intensity > 0.3 else (90, 95, 105))
            self.screen.blit(lbl_hex, lbl_hex.get_rect(center=(cx, tube_top_y + tube_h + 30)))

        # -------------------------------------------------------------
        # 3. PAR-SPOTS (Spot1 bis Spot6)
        # -------------------------------------------------------------
        for name, (cx, cy, is_above) in self.spot_coords.items():
            color = self.get_color(name)
            r, g, b = color
            intensity = max(r, g, b) / 255.0

            # Montage-Halterung zur Traverse
            if is_above:
                pygame.draw.line(self.screen, (50, 55, 65), (cx, cy + 20), (cx, self.truss_y - 4), 3)
            else:
                pygame.draw.line(self.screen, (50, 55, 65), (cx, cy - 20), (cx, self.truss_y + 4), 3)

            # Scheinwerfer-Lichtkegel nach unten
            if intensity > 0.02:
                # Kegel-Basis auf dem Boden
                cone_w = 160
                beam_poly = [
                    (cx - 10, cy + (15 if is_above else 18)),
                    (cx - cone_w // 2, self.floor_y),
                    (cx + cone_w // 2, self.floor_y),
                    (cx + 10, cy + (15 if is_above else 18)),
                ]
                pygame.draw.polygon(glow_surf, (r, g, b, int(20 * intensity)), beam_poly)
                # Boden-Ausleuchtung (Spot-Pool)
                pygame.draw.ellipse(glow_surf, (r, g, b, int(45 * intensity)), (cx - cone_w // 2, self.floor_y - 12, cone_w, 24))
                # Halo um den Scheinwerfer
                pygame.draw.circle(glow_surf, (r, g, b, int(85 * intensity)), (cx, cy), 38)
                pygame.draw.circle(glow_surf, (r, g, b, int(40 * intensity)), (cx, cy), 65)

            # PAR64 Gehäuse
            outer_r = 23
            inner_r = 18
            pygame.draw.circle(self.screen, (32, 36, 44), (cx, cy), outer_r)
            pygame.draw.circle(self.screen, (55, 60, 72), (cx, cy), outer_r, 2)

            if intensity > 0:
                pygame.draw.circle(self.screen, color, (cx, cy), inner_r)
                core_r = min(255, int(r * 0.4 + 255 * 0.6))
                core_g = min(255, int(g * 0.4 + 255 * 0.6))
                core_b = min(255, int(b * 0.4 + 255 * 0.6))
                pygame.draw.circle(self.screen, (core_r, core_g, core_b), (cx, cy), 7)
            else:
                pygame.draw.circle(self.screen, (18, 20, 25), (cx, cy), inner_r)
                pygame.draw.circle(self.screen, (35, 40, 50), (cx, cy), inner_r, 1)

            # Labels
            lbl_y = cy - 35 if is_above else cy + 28
            lbl_name = self.font_mini.render(name, True, (140, 150, 165))
            self.screen.blit(lbl_name, lbl_name.get_rect(center=(cx, lbl_y)))
            hex_code = f'#{r:02X}{g:02X}{b:02X}'
            lbl_hex = self.font_mini.render(hex_code, True, color if intensity > 0.3 else (90, 95, 105))
            self.screen.blit(lbl_hex, lbl_hex.get_rect(center=(cx, lbl_y + 12)))

        # -------------------------------------------------------------
        # 4. LASERWORLD EL-300 RGB (Laser1 bis Laser4) & BEAM-SIMULATION
        # -------------------------------------------------------------
        box_w = 82
        box_h = 44
        laser_tilt = {'Laser1': -35, 'Laser2': -12, 'Laser3': 12, 'Laser4': 35}

        for lname, lx in self.laser_coords.items():
            color, vel, direction = self.get_laser_state(lname)
            r, g, b = color
            intensity = max(r, g, b) / 255.0
            angle = self.laser_angles[lname]

            box_top = self.truss_y - box_h - 4
            box_rect = pygame.Rect(lx - box_w // 2, box_top, box_w, box_h)

            # Montage-Klammer
            pygame.draw.rect(self.screen, (45, 50, 60), (lx - 12, self.truss_y - 5, 24, 6))

            # Laser-Projektion (Strahlenfächer / Multi-Beam Gittereffekt)
            aperture_pt = (lx - 18, box_top + 22)
            if intensity > 0.02:
                # Apertur-Aura
                pygame.draw.circle(glow_surf, (r, g, b, int(120 * intensity)), aperture_pt, 25)

                # 8 rotierende Strahlen + 1 Zentralstrahl
                num_rays = 8
                spread_w = 110
                tilt = laser_tilt[lname]

                # Zentralstrahl
                target_center = (lx + tilt, self.floor_y)
                pygame.draw.line(glow_surf, (r, g, b, int(50 * intensity)), aperture_pt, target_center, 4)
                pygame.draw.line(self.screen, (255, 255, 255), aperture_pt, target_center, 1)

                # Rotierender Fächer
                for k in range(num_rays):
                    ray_phase = angle + k * (2.0 * math.pi / num_rays)
                    tx = lx + tilt + spread_w * math.cos(ray_phase)
                    ty = self.floor_y + 10 * math.sin(ray_phase)

                    # Volumetrischer Schleier auf glow_surf
                    pygame.draw.line(glow_surf, (r, g, b, int(35 * intensity)), aperture_pt, (tx, ty), 5)
                    pygame.draw.line(glow_surf, (r, g, b, int(75 * intensity)), aperture_pt, (tx, ty), 2)
                    # Boden-Lichtpunkt
                    pygame.draw.circle(glow_surf, (r, g, b, int(90 * intensity)), (int(tx), int(ty)), 6)
                    pygame.draw.circle(glow_surf, (255, 255, 255, int(160 * intensity)), (int(tx), int(ty)), 2)

                    # Scharfer Laser-Kernstrahl
                    core_col = (min(255, int(r * 0.5 + 130)), min(255, int(g * 0.5 + 130)), min(255, int(b * 0.5 + 130)))
                    pygame.draw.line(self.screen, core_col, aperture_pt, (int(tx), int(ty)), 1)

            # Laser-Gehäuse (Charcoal mit EL-300-typischer Farbblende)
            pygame.draw.rect(self.screen, (24, 27, 34), box_rect, border_radius=4)
            pygame.draw.rect(self.screen, (50, 55, 68), box_rect, 1, border_radius=4)
            # Grüne Akzentleiste (Iconic Laserworld-Design)
            pygame.draw.line(self.screen, (60, 200, 90), (box_rect.left + 3, box_rect.top + 3), (box_rect.right - 4, box_rect.top + 3), 2)

            # Laser-Apertur (Austrittsfenster)
            aperture_r = 12
            pygame.draw.circle(self.screen, (15, 17, 22), aperture_pt, aperture_r)
            pygame.draw.circle(self.screen, (70, 75, 90), aperture_pt, aperture_r, 1)

            if intensity > 0:
                pygame.draw.circle(self.screen, color, aperture_pt, aperture_r - 2)
                pygame.draw.circle(self.screen, (255, 255, 255), aperture_pt, 4)
            else:
                pygame.draw.circle(self.screen, (10, 12, 16), aperture_pt, aperture_r - 2)

            # Rotierendes Fadenkreuz im Austrittsfenster
            reticle_len = 8
            rx1 = aperture_pt[0] + reticle_len * math.cos(angle)
            ry1 = aperture_pt[1] + reticle_len * math.sin(angle)
            rx2 = aperture_pt[0] - reticle_len * math.cos(angle)
            ry2 = aperture_pt[1] - reticle_len * math.sin(angle)
            pygame.draw.line(self.screen, (220, 225, 235), (rx1, ry1), (rx2, ry2), 1)

            # Statusanzeige im Gehäuse
            status_x = lx + 16
            lbl_name = self.font_mini.render(lname, True, (190, 200, 215))
            self.screen.blit(lbl_name, lbl_name.get_rect(center=(status_x, box_top + 11)))

            # Drehrichtungs-Symbol & Geschwindigkeit
            if direction == 'R' and vel > 0:
                dir_sym = f'⟳ {int(vel)}'
                dir_col = (100, 220, 140)
            elif direction == 'L' and vel > 0:
                dir_sym = f'⟲ {int(vel)}'
                dir_col = (100, 180, 255)
            else:
                dir_sym = 'STOP'
                dir_col = (120, 125, 135)

            lbl_dir = self.font_mini.render(dir_sym, True, dir_col)
            self.screen.blit(lbl_dir, lbl_dir.get_rect(center=(status_x, box_top + 23)))

            # Hex-Farbcode
            hex_code = f'#{r:02X}{g:02X}{b:02X}'
            lbl_hex = self.font_mini.render(hex_code, True, color if intensity > 0.3 else (90, 95, 105))
            self.screen.blit(lbl_hex, lbl_hex.get_rect(center=(status_x, box_top + 34)))

        # Additive Lichteffekte über die Bühne legen
        self.screen.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_ADD)

    def draw_ui(self):
        # Bedienleiste unten
        panel_rect = pygame.Rect(0, 600, self.width, 160)
        pygame.draw.rect(self.screen, (18, 20, 26), panel_rect)
        pygame.draw.line(self.screen, (35, 40, 52), (0, 600), (self.width, 600), 1)

        # Titel & Programm-Metadaten
        title_surf = self.font_large.render(f'Programm: {self.comment}', True, (245, 245, 250))
        self.screen.blit(title_surf, (30, 18))

        current_bar = int(self.current_beat // 4) + 1
        beat_in_bar = (self.current_beat % 4) + 1
        time_info = (
            f'Position: Beat {self.current_beat:05.2f} / {self.timeline_length:.1f}  |  '
            f'Takt {current_bar}, Schlag {beat_in_bar:04.2f}'
        )
        info_surf = self.font_main.render(time_info, True, (160, 170, 185))
        self.screen.blit(info_surf, (30, 48))

        # Setup-Info
        setup_badge = self.font_mini.render(
            'Hardware: 6x PAR-Spots  |  10x Tubes  |  4x Laserworld EL-300 RGB', True, (100, 110, 130)
        )
        self.screen.blit(setup_badge, (30, 70))

        # Visueller Metronom-Puls
        beat_fract = self.current_beat % 1.0
        pulse_alpha = max(0, int(255 * (1.0 - beat_fract * 4.0)))
        if pulse_alpha > 0:
            pulse_dot = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(pulse_dot, (0, 220, 120, pulse_alpha), (6, 6), 6)
            self.screen.blit(pulse_dot, (info_surf.get_width() + 45, 52))

        # Takt-Markierungen auf der Timeline
        t_rect = self.timeline_slider.rect
        total = self.timeline_slider.max_val
        for b in range(int(total) + 1):
            px = t_rect.x + int((b / total) * t_rect.width)
            is_bar = b % 4 == 0
            h = 8 if is_bar else 4
            color = (130, 140, 160) if is_bar else (60, 65, 75)
            pygame.draw.line(self.screen, color, (px, t_rect.bottom + 2), (px, t_rect.bottom + 2 + h))
            if is_bar:
                bar_lbl = self.font_small.render(f'T{b//4 + 1}', True, (110, 120, 135))
                self.screen.blit(bar_lbl, bar_lbl.get_rect(center=(px, t_rect.bottom + 18)))

        # Buttons und Slider rendern
        self.btn_play.draw(self.screen, self.font_bold)
        self.btn_rewind.draw(self.screen, self.font_main)
        self.btn_loop.draw(self.screen, self.font_main)
        self.btn_open.draw(self.screen, self.font_bold)
        self.bpm_slider.draw(self.screen, self.font_main)
        self.timeline_slider.draw(self.screen, self.font_main)

        # Tastatur-Shortcuts Hilfe
        shortcuts = 'Shortcuts: Leertaste (Play/Pause) | R (Reset) | L (Loop) | Pfeile (BPM / Scrub)'
        sc_surf = self.font_small.render(shortcuts, True, (90, 95, 110))
        self.screen.blit(sc_surf, (self.width - sc_surf.get_width() - 30, 725))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.toggle_play()
                    elif event.key == pygame.K_r:
                        self.rewind()
                    elif event.key == pygame.K_l:
                        self.toggle_loop()
                    elif event.key == pygame.K_UP:
                        self.bpm_slider.val = min(220, self.bpm_slider.val + 5)
                    elif event.key == pygame.K_DOWN:
                        self.bpm_slider.val = max(40, self.bpm_slider.val - 5)
                    elif event.key == pygame.K_LEFT:
                        self.current_beat = max(0.0, self.current_beat - 1.0)
                        self.timeline_slider.val = self.current_beat
                    elif event.key == pygame.K_RIGHT:
                        self.current_beat = min(self.timeline_length, self.current_beat + 1.0)
                        self.timeline_slider.val = self.current_beat

                # UI Events verarbeiten
                self.bpm_slider.handle_event(event)
                self.timeline_slider.handle_event(event)
                self.btn_play.handle_event(event)
                self.btn_rewind.handle_event(event)
                self.btn_loop.handle_event(event)
                self.btn_open.handle_event(event)

            self.update(dt)
            self.draw_stage()
            self.draw_ui()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    # Dateipfad via Übergabeparameter möglich (z. B. `python previewer.py mein_programm.txt`)
    initial_file = sys.argv[1] if len(sys.argv) > 1 else None
    app = LightingPreviewer(initial_file)
    app.run()