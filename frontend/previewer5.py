import datetime
import math
import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import pygame

# ============================================================================== 
# DEFAULT DEMO PROGRAMM
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

    if not color_tracks and not vel_tracks and not dir_tracks:
        raise ValueError('Die Datei enthält keine gültigen Lichtsteuerungs-Befehle.')
    if max_beat <= 0:
        max_beat = 4.0
    return comment, color_tracks, vel_tracks, dir_tracks, max_beat


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
    def __init__(self, x, y, w, h, text, callback, font_type='main', is_danger=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.font_type = font_type
        self.is_danger = is_danger
        self.active = False

    def draw(self, screen, fonts):
        font = fonts.get(self.font_type, fonts['main'])
        mx, my = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint((mx, my))

        if self.is_danger:
            if self.active:
                color = (160, 45, 55)
            elif is_hover:
                color = (78, 30, 38)
            else:
                color = (52, 25, 30)
            border_color = (140, 50, 60)
        else:
            if self.active:
                color = (55, 105, 195)
            elif is_hover:
                color = (52, 58, 70)
            else:
                color = (42, 46, 56)
            border_color = (75, 85, 100)

        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, border_color, self.rect, 1, border_radius=5)
        txt_surf = font.render(self.text, True, (240, 240, 245))
        screen.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.callback()
            return True
        return False


class LightingPreviewer5:
    def __init__(self, initial_source=None):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption('Lichtanlagen Studio – Folder Browser Previewer')

        self.sidebar_w = 320
        self.stage_w = 1280
        self.width = self.sidebar_w + self.stage_w
        self.height = 760
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.stage_surf = pygame.Surface((self.stage_w, 600))
        self.clock = pygame.time.Clock()

        self.fonts = {
            'main': pygame.font.SysFont('Segoe UI', 13),
            'bold': pygame.font.SysFont('Segoe UI', 13, bold=True),
            'large': pygame.font.SysFont('Segoe UI', 19, bold=True),
            'header': pygame.font.SysFont('Segoe UI', 15, bold=True),
            'small': pygame.font.SysFont('Consolas', 11),
            'mini': pygame.font.SysFont('Consolas', 10, bold=True),
            'meta': pygame.font.SysFont('Segoe UI', 11),
            'icon': pygame.font.SysFont('Segoe UI Symbol', 12, bold=True),
        }

        self.current_beat = 0.0
        self.playing = True
        self.loop = True
        self.laser_angles = {'Laser1': 0.0, 'Laser2': 0.0, 'Laser3': 0.0, 'Laser4': 0.0}
        self.prev_scrub_beat = 0.0

        self.auto_refresh_timer = 0.0
        self.auto_refresh_interval = 0.5
        self.last_folder_snapshot = {}

        self.bpm_slider = Slider(x=self.sidebar_w + 40, y=695, w=180, h=14, min_val=40, max_val=220, initial_val=120, label='Tempo', unit=' BPM', is_int=True)
        self.timeline_slider = Slider(x=self.sidebar_w + 260, y=695, w=720, h=14, min_val=0, max_val=16.0, initial_val=0, label='Timeline (Scrubbing)', unit=' Beats', is_int=False)

        self.btn_play = Button(self.sidebar_w + 40, 635, 90, 30, 'Pause', self.toggle_play, 'bold')
        self.btn_rewind = Button(self.sidebar_w + 140, 635, 80, 30, 'Reset', self.rewind, 'main')
        self.btn_loop = Button(self.sidebar_w + 230, 635, 90, 30, 'Loop: An', self.toggle_loop, 'main')

        self.setup_geometry()

        self.entry_items = []
        self.scroll_y = 0.0
        self.list_y = 124
        self.item_h = 48
        self.active_file_path = None
        self.selected_path = None
        self.failed_files = set()
        self.inline_rename_target = None
        self.inline_rename_value = ''
        self.inline_rename_cursor = 0
        self.inline_rename_selection = (0, 0)

        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.root_dir = os.path.abspath(os.path.join(self.project_root, 'effects'))
        if not os.path.isdir(self.root_dir):
            os.makedirs(self.root_dir, exist_ok=True)
        self.current_dir = self.root_dir
        self.expanded_dirs = set()

        if initial_source and os.path.exists(initial_source):
            p = os.path.abspath(initial_source)
            if os.path.isdir(p):
                self.current_dir = p if os.path.commonpath([self.root_dir, p]) == self.root_dir else self.root_dir
            else:
                if os.path.commonpath([self.root_dir, os.path.dirname(p)]) == self.root_dir:
                    self.current_dir = os.path.dirname(p)
                    self.active_file_path = p
                    self.selected_path = p
                else:
                    self.current_dir = self.root_dir

        self.btn_choose_dir = Button(15, 52, 130, 26, 'Root', self.reset_to_root, 'main')
        self.btn_parent_dir = Button(155, 52, 130, 26, 'Up', self.go_to_parent_dir, 'main')
        self.btn_rename_item = Button(15, 84, 130, 26, 'Rename', self.rename_selected_item, 'main')
        self.btn_delete_item = Button(155, 84, 130, 26, 'Delete', self.delete_selected_item, 'main', is_danger=True)

        self.refresh_file_list()

        loaded_successfully = False
        if self.active_file_path and os.path.exists(self.active_file_path):
            loaded_successfully = self.load_file(self.active_file_path)

        if not loaded_successfully and self.entry_items:
            for item in self.entry_items:
                if item['kind'] == 'file':
                    if self.load_file(item['path']):
                        loaded_successfully = True
                        break

        if not loaded_successfully:
            self.load_program_data(DEFAULT_SCRIPT)

    def setup_geometry(self):
        self.truss_y = 240
        self.floor_y = 560
        self.center_x = 640

        self.spot_coords = {
            'Spot1': (110, 185, True),
            'Spot2': (170, 295, False),
            'Spot3': (230, 185, True),
            'Spot4': (1050, 185, True),
            'Spot5': (1110, 295, False),
            'Spot6': (1170, 185, True),
        }

        tube_x_left = [345, 405, 465, 525, 585]
        tube_x_right = [695, 755, 815, 875, 935]
        self.tube_coords = {f'Tube{i+1:02d}': tube_x_left[i] for i in range(5)}
        self.tube_coords.update({f'Tube{i+6:02d}': tube_x_right[i] for i in range(5)})

        self.laser_coords = {'Laser1': 405, 'Laser2': 525, 'Laser3': 755, 'Laser4': 875}
        self.lasers = ['Laser1', 'Laser2', 'Laser3', 'Laser4']

    def get_directory_snapshot(self) -> dict:
        if not os.path.exists(self.current_dir):
            return {}
        snapshot = {}
        try:
            for entry in os.scandir(self.current_dir):
                if entry.is_file() and entry.name.lower().endswith('.txt'):
                    try:
                        st = entry.stat()
                        snapshot[entry.name] = (st.st_mtime, st.st_size)
                    except OSError:
                        continue
                elif entry.is_dir():
                    try:
                        st = entry.stat()
                        snapshot[entry.name] = (st.st_mtime, 0)
                    except OSError:
                        continue
        except OSError:
            pass
        return snapshot

    def check_directory_changes(self):
        if not os.path.exists(self.current_dir):
            return
        current_snapshot = self.get_directory_snapshot()
        if current_snapshot != self.last_folder_snapshot:
            self.refresh_file_list()
            if self.active_file_path and not os.path.exists(self.active_file_path):
                self.active_file_path = None
                self.selected_path = None
                if self.entry_items:
                    for item in self.entry_items:
                        if item['kind'] == 'file' and self.load_file(item['path']):
                            break
                else:
                    self.load_program_data(DEFAULT_SCRIPT)

    def reset_to_root(self):
        self.current_dir = self.root_dir
        self.selected_path = None
        self.refresh_file_list()

    def choose_directory(self):
        self.reset_to_root()

    def go_to_parent_dir(self):
        if self.current_dir == self.root_dir:
            return
        parent = os.path.dirname(self.current_dir)
        if parent and os.path.isdir(parent):
            self.current_dir = parent
            self.refresh_file_list()
            self.selected_path = None
            self.active_file_path = None
            if self.entry_items:
                for item in self.entry_items:
                    if item['kind'] == 'file' and self.load_file(item['path']):
                        break

    def create_folder(self):
        try:
            root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
            name = simpledialog.askstring('Neuen Ordner anlegen', 'Name des neuen Unterordners:')
            root.destroy()
            if not name:
                return
            safe_name = name.strip().strip('/\\')
            if not safe_name:
                return
            new_path = os.path.join(self.current_dir, safe_name)
            if os.path.exists(new_path):
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
                messagebox.showerror('Fehler', f"Ein Ordner namens '{safe_name}' existiert bereits.")
                root.destroy()
                return
            os.makedirs(new_path)
            self.refresh_file_list()
        except Exception as e:
            print(f'Fehler beim Erstellen des Ordners: {e}')

    def _append_tree_entries(self, dir_path: str, depth: int = 0):
        try:
            entries = []
            for entry in os.scandir(dir_path):
                entries.append(entry)
        except OSError:
            return

        entries.sort(key=lambda e: (0 if e.is_dir() else 1, e.name.lower()))
        for entry in entries:
            if entry.is_dir():
                st = entry.stat()
                self.entry_items.append({
                    'kind': 'dir',
                    'name': entry.name,
                    'path': entry.path,
                    'mtime': st.st_mtime,
                    'size': 0,
                    'depth': depth,
                })
                if entry.path in self.expanded_dirs:
                    self._append_tree_entries(entry.path, depth + 1)
            elif entry.is_file() and entry.name.lower().endswith('.txt'):
                st = entry.stat()
                self.entry_items.append({
                    'kind': 'file',
                    'name': entry.name,
                    'path': entry.path,
                    'mtime': st.st_mtime,
                    'size': st.st_size,
                    'depth': depth,
                })

    def refresh_file_list(self):
        self.entry_items = []
        if not os.path.exists(self.root_dir):
            self.last_folder_snapshot = {}
            return

        self._append_tree_entries(self.root_dir, 0)
        self.last_folder_snapshot = {}

    def toggle_dir_expanded(self, dir_path: str):
        self.current_dir = dir_path
        if dir_path in self.expanded_dirs:
            self.expanded_dirs.remove(dir_path)
        else:
            self.expanded_dirs.add(dir_path)
        self.refresh_file_list()

    def begin_inline_rename(self, target_path=None):
        if target_path is None:
            target_path = self.selected_path or self.active_file_path
        if not target_path or not os.path.exists(target_path):
            return

        self.inline_rename_target = os.path.abspath(target_path)
        self.inline_rename_value = os.path.basename(self.inline_rename_target)
        self.selected_path = self.inline_rename_target
        self.inline_rename_cursor = 0
        self.inline_rename_selection = (0, len(self.inline_rename_value))

    def cancel_inline_rename(self):
        self.inline_rename_target = None
        self.inline_rename_value = ''
        self.inline_rename_cursor = 0
        self.inline_rename_selection = (0, 0)

    def commit_inline_rename(self):
        if not self.inline_rename_target:
            return

        target_path = self.inline_rename_target
        new_name = self.inline_rename_value.strip().strip('/\\')
        if not new_name:
            self.cancel_inline_rename()
            return

        if os.path.isdir(target_path):
            new_path = os.path.join(os.path.dirname(target_path), new_name)
        else:
            if not new_name.lower().endswith('.txt'):
                new_name += '.txt'
            new_path = os.path.join(os.path.dirname(target_path), new_name)

        if os.path.exists(new_path) and os.path.abspath(new_path) != os.path.abspath(target_path):
            self.inline_rename_value = os.path.basename(target_path)
            return

        try:
            os.rename(target_path, new_path)
            if self.active_file_path == target_path:
                self.active_file_path = new_path
            if self.selected_path == target_path:
                self.selected_path = new_path
            self.refresh_file_list()
        except Exception as e:
            print(f'Fehler beim Umbenennen: {e}')
        finally:
            self.cancel_inline_rename()

    def rename_selected_item(self):
        self.begin_inline_rename()

    def delete_selected_item(self):
        target_path = self.selected_path or self.active_file_path
        if not target_path or not os.path.exists(target_path):
            try:
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
                messagebox.showinfo('Hinweis', 'Bitte zuerst ein Element auswählen.')
                root.destroy()
            except Exception:
                pass
            return

        filename = os.path.basename(target_path)
        try:
            root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
            confirm = messagebox.askyesno('Löschen', f"Möchtest du '{filename}' wirklich löschen?", icon='warning')
            root.destroy()
            if not confirm:
                return
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)

            if self.active_file_path == target_path:
                self.active_file_path = None
            if self.selected_path == target_path:
                self.selected_path = None
            self.refresh_file_list()
            if not self.active_file_path and self.entry_items:
                for item in self.entry_items:
                    if item['kind'] == 'file' and self.load_file(item['path']):
                        break
                else:
                    self.load_program_data(DEFAULT_SCRIPT)
        except Exception as e:
            print(f'Fehler beim Löschen: {e}')

    def load_file(self, filepath: str) -> bool:
        abs_path = os.path.abspath(filepath)
        self.selected_path = abs_path
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            comment, color_tracks, vel_tracks, dir_tracks, max_beat = parse_dsl_content(content)
            self.failed_files.discard(abs_path)
            self.active_file_path = abs_path
            self.apply_parsed_program(comment, color_tracks, vel_tracks, dir_tracks, max_beat)
            self.playing = True
            self.btn_play.text = 'Pause'
            self.btn_play.active = False
            return True
        except Exception as e:
            print(f"Laufzeitfehler bei Datei '{os.path.basename(filepath)}': {e}")
            self.failed_files.add(abs_path)
            return False

    def load_program_data(self, content: str):
        try:
            comment, color_tracks, vel_tracks, dir_tracks, max_beat = parse_dsl_content(content)
            self.apply_parsed_program(comment, color_tracks, vel_tracks, dir_tracks, max_beat)
        except Exception as e:
            print(f'Fehler beim Laden des Standard-Programms: {e}')

    def apply_parsed_program(self, comment, color_tracks, vel_tracks, dir_tracks, max_beat):
        self.comment = comment
        self.color_tracks = color_tracks
        self.vel_tracks = vel_tracks
        self.dir_tracks = dir_tracks
        self.max_beat = max_beat
        total_beats = math.ceil(self.max_beat)
        if total_beats % 4 != 0:
            total_beats = math.ceil(total_beats / 4) * 4
        self.timeline_length = max(4.0, float(total_beats))
        self.timeline_slider.max_val = self.timeline_length
        self.current_beat = 0.0
        self.prev_scrub_beat = 0.0
        for k in self.laser_angles:
            self.laser_angles[k] = 0.0

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
        self.auto_refresh_timer += dt
        if self.auto_refresh_timer >= self.auto_refresh_interval:
            self.auto_refresh_timer = 0.0
            self.check_directory_changes()

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
                for lname in self.lasers:
                    _, vel, direction = self.get_laser_state(lname)
                    dir_sign = 1.0 if direction == 'R' else (-1.0 if direction == 'L' else 0.0)
                    angular_speed = dir_sign * (vel / 255.0) * (2.0 * math.pi * 1.8)
                    self.laser_angles[lname] = (self.laser_angles[lname] + angular_speed * dt) % (2.0 * math.pi)
            self.timeline_slider.val = self.current_beat
            self.prev_scrub_beat = self.current_beat
        else:
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
        self.stage_surf.fill((10, 11, 15))
        glow_surf = pygame.Surface((self.stage_w, 600), pygame.SRCALPHA)

        pygame.draw.line(self.stage_surf, (25, 29, 36), (0, self.floor_y), (self.stage_w, self.floor_y), 2)
        col_w = 18
        col_rect = pygame.Rect(self.center_x - col_w // 2, self.truss_y, col_w, self.floor_y - self.truss_y)
        pygame.draw.rect(self.stage_surf, (30, 33, 40), col_rect)
        pygame.draw.rect(self.stage_surf, (50, 55, 68), col_rect, 1)
        pygame.draw.rect(self.stage_surf, (40, 44, 54), (self.center_x - 35, self.floor_y - 6, 70, 8), border_radius=2)

        truss_left, truss_right = 60, 1220
        pygame.draw.line(self.stage_surf, (50, 54, 65), (truss_left, self.truss_y - 4), (truss_right, self.truss_y - 4), 3)
        pygame.draw.line(self.stage_surf, (40, 44, 52), (truss_left, self.truss_y + 4), (truss_right, self.truss_y + 4), 3)
        for tx in range(truss_left, truss_right, 24):
            pygame.draw.line(self.stage_surf, (32, 36, 44), (tx, self.truss_y - 4), (tx + 12, self.truss_y + 4), 1)
            pygame.draw.line(self.stage_surf, (32, 36, 44), (tx + 12, self.truss_y + 4), (tx + 24, self.truss_y - 4), 1)
        pygame.draw.rect(self.stage_surf, (55, 60, 75), (self.center_x - 16, self.truss_y - 8, 32, 18), border_radius=3)

        tube_w, tube_h = 16, 240
        tube_top_y = self.truss_y + 12
        for name, cx in self.tube_coords.items():
            color = self.get_color(name)
            r, g, b = color
            intensity = max(r, g, b) / 255.0

            pygame.draw.rect(self.stage_surf, (45, 50, 60), (cx - 4, self.truss_y, 8, 12))
            if intensity > 0.02:
                pygame.draw.ellipse(glow_surf, (r, g, b, int(22 * intensity)), (cx - 45, tube_top_y - 15, 90, tube_h + 30))
                pygame.draw.ellipse(glow_surf, (r, g, b, int(55 * intensity)), (cx - 24, tube_top_y - 5, 48, tube_h + 10))
                pygame.draw.ellipse(glow_surf, (r, g, b, int(90 * intensity)), (cx - 12, tube_top_y, 24, tube_h))
                pygame.draw.ellipse(glow_surf, (r, g, b, int(40 * intensity)), (cx - 20, self.floor_y - 10, 40, 20))

            tube_rect = pygame.Rect(cx - tube_w // 2, tube_top_y, tube_w, tube_h)
            if intensity > 0:
                pygame.draw.rect(self.stage_surf, color, tube_rect, border_radius=tube_w // 2)
                core_r = min(255, int(r * 0.4 + 255 * 0.6))
                core_g = min(255, int(g * 0.4 + 255 * 0.6))
                core_b = min(255, int(b * 0.4 + 255 * 0.6))
                pygame.draw.rect(self.stage_surf, (core_r, core_g, core_b), (cx - 2, tube_top_y + 4, 4, tube_h - 8), border_radius=2)
            else:
                pygame.draw.rect(self.stage_surf, (22, 25, 32), tube_rect, border_radius=tube_w // 2)
                pygame.draw.rect(self.stage_surf, (38, 42, 52), tube_rect, 1, border_radius=tube_w // 2)

            pygame.draw.ellipse(self.stage_surf, (45, 50, 60), (cx - tube_w // 2, tube_top_y - 2, tube_w, 5))
            pygame.draw.ellipse(self.stage_surf, (45, 50, 60), (cx - tube_w // 2, tube_top_y + tube_h - 3, tube_w, 5))

            lbl_name = self.fonts['mini'].render(name, True, (130, 140, 155))
            self.stage_surf.blit(lbl_name, lbl_name.get_rect(center=(cx, tube_top_y + tube_h + 16)))
            hex_code = f'#{r:02X}{g:02X}{b:02X}'
            lbl_hex = self.fonts['mini'].render(hex_code, True, color if intensity > 0.3 else (90, 95, 105))
            self.stage_surf.blit(lbl_hex, lbl_hex.get_rect(center=(cx, tube_top_y + tube_h + 30)))

        for name, (cx, cy, is_above) in self.spot_coords.items():
            color = self.get_color(name)
            r, g, b = color
            intensity = max(r, g, b) / 255.0
            if is_above:
                pygame.draw.line(self.stage_surf, (50, 55, 65), (cx, cy + 20), (cx, self.truss_y - 4), 3)
            else:
                pygame.draw.line(self.stage_surf, (50, 55, 65), (cx, cy - 20), (cx, self.truss_y + 4), 3)
            if intensity > 0.02:
                cone_w = 160
                beam_poly = [(cx - 10, cy + (15 if is_above else 18)), (cx - cone_w // 2, self.floor_y), (cx + cone_w // 2, self.floor_y), (cx + 10, cy + (15 if is_above else 18))]
                pygame.draw.polygon(glow_surf, (r, g, b, int(20 * intensity)), beam_poly)
                pygame.draw.ellipse(glow_surf, (r, g, b, int(45 * intensity)), (cx - cone_w // 2, self.floor_y - 12, cone_w, 24))
                pygame.draw.circle(glow_surf, (r, g, b, int(85 * intensity)), (cx, cy), 38)
                pygame.draw.circle(glow_surf, (r, g, b, int(40 * intensity)), (cx, cy), 65)
            outer_r, inner_r = 23, 18
            pygame.draw.circle(self.stage_surf, (32, 36, 44), (cx, cy), outer_r)
            pygame.draw.circle(self.stage_surf, (55, 60, 72), (cx, cy), outer_r, 2)
            if intensity > 0:
                pygame.draw.circle(self.stage_surf, color, (cx, cy), inner_r)
                core_r = min(255, int(r * 0.4 + 255 * 0.6))
                core_g = min(255, int(g * 0.4 + 255 * 0.6))
                core_b = min(255, int(b * 0.4 + 255 * 0.6))
                pygame.draw.circle(self.stage_surf, (core_r, core_g, core_b), (cx, cy), 7)
            else:
                pygame.draw.circle(self.stage_surf, (18, 20, 25), (cx, cy), inner_r)
                pygame.draw.circle(self.stage_surf, (35, 40, 50), (cx, cy), inner_r, 1)
            lbl_y = cy - 35 if is_above else cy + 28
            lbl_name = self.fonts['mini'].render(name, True, (140, 150, 165))
            self.stage_surf.blit(lbl_name, lbl_name.get_rect(center=(cx, lbl_y)))
            hex_code = f'#{r:02X}{g:02X}{b:02X}'
            lbl_hex = self.fonts['mini'].render(hex_code, True, color if intensity > 0.3 else (90, 95, 105))
            self.stage_surf.blit(lbl_hex, lbl_hex.get_rect(center=(cx, lbl_y + 12)))

        box_w, box_h = 82, 44
        laser_tilt = {'Laser1': -35, 'Laser2': -12, 'Laser3': 12, 'Laser4': 35}
        for lname, lx in self.laser_coords.items():
            color, vel, direction = self.get_laser_state(lname)
            r, g, b = color
            intensity = max(r, g, b) / 255.0
            angle = self.laser_angles[lname]
            box_top = self.truss_y - box_h - 4
            box_rect = pygame.Rect(lx - box_w // 2, box_top, box_w, box_h)
            pygame.draw.rect(self.stage_surf, (45, 50, 60), (lx - 12, self.truss_y - 5, 24, 6))
            aperture_pt = (lx - 18, box_top + 22)
            if intensity > 0.02:
                pygame.draw.circle(glow_surf, (r, g, b, int(120 * intensity)), aperture_pt, 25)
                num_rays = 8
                spread_w = 110
                tilt = laser_tilt[lname]
                target_center = (lx + tilt, self.floor_y)
                pygame.draw.line(glow_surf, (r, g, b, int(50 * intensity)), aperture_pt, target_center, 4)
                pygame.draw.line(self.stage_surf, (255, 255, 255), aperture_pt, target_center, 1)
                for k in range(num_rays):
                    ray_phase = angle + k * (2.0 * math.pi / num_rays)
                    tx = lx + tilt + spread_w * math.cos(ray_phase)
                    ty = self.floor_y + 10 * math.sin(ray_phase)
                    pygame.draw.line(glow_surf, (r, g, b, int(35 * intensity)), aperture_pt, (tx, ty), 5)
                    pygame.draw.line(glow_surf, (r, g, b, int(75 * intensity)), aperture_pt, (tx, ty), 2)
                    pygame.draw.circle(glow_surf, (r, g, b, int(90 * intensity)), (int(tx), int(ty)), 6)
                    pygame.draw.circle(glow_surf, (255, 255, 255, int(160 * intensity)), (int(tx), int(ty)), 2)
                    core_col = (min(255, int(r * 0.5 + 130)), min(255, int(g * 0.5 + 130)), min(255, int(b * 0.5 + 130)))
                    pygame.draw.line(self.stage_surf, core_col, aperture_pt, (int(tx), int(ty)), 1)
            pygame.draw.rect(self.stage_surf, (24, 27, 34), box_rect, border_radius=4)
            pygame.draw.rect(self.stage_surf, (50, 55, 68), box_rect, 1, border_radius=4)
            pygame.draw.line(self.stage_surf, (60, 200, 90), (box_rect.left + 3, box_rect.top + 3), (box_rect.right - 4, box_rect.top + 3), 2)
            aperture_r = 12
            pygame.draw.circle(self.stage_surf, (15, 17, 22), aperture_pt, aperture_r)
            pygame.draw.circle(self.stage_surf, (70, 75, 90), aperture_pt, aperture_r, 1)
            if intensity > 0:
                pygame.draw.circle(self.stage_surf, color, aperture_pt, aperture_r - 2)
                pygame.draw.circle(self.stage_surf, (255, 255, 255), aperture_pt, 4)
            else:
                pygame.draw.circle(self.stage_surf, (10, 12, 16), aperture_pt, aperture_r - 2)
            reticle_len = 8
            rx1 = aperture_pt[0] + reticle_len * math.cos(angle)
            ry1 = aperture_pt[1] + reticle_len * math.sin(angle)
            rx2 = aperture_pt[0] - reticle_len * math.cos(angle)
            ry2 = aperture_pt[1] - reticle_len * math.sin(angle)
            pygame.draw.line(self.stage_surf, (220, 225, 235), (rx1, ry1), (rx2, ry2), 1)

            status_x = lx + 16
            lbl_name = self.fonts['mini'].render(lname, True, (190, 200, 215))
            self.stage_surf.blit(lbl_name, lbl_name.get_rect(center=(status_x, box_top + 11)))
            if direction == 'R' and vel > 0:
                dir_sym, dir_col = f'⟳ {int(vel)}', (100, 220, 140)
            elif direction == 'L' and vel > 0:
                dir_sym, dir_col = f'⟲ {int(vel)}', (100, 180, 255)
            else:
                dir_sym, dir_col = 'STOP', (120, 125, 135)
            lbl_dir = self.fonts['mini'].render(dir_sym, True, dir_col)
            self.stage_surf.blit(lbl_dir, lbl_dir.get_rect(center=(status_x, box_top + 23)))
            hex_code = f'#{r:02X}{g:02X}{b:02X}'
            lbl_hex = self.fonts['mini'].render(hex_code, True, color if intensity > 0.3 else (90, 95, 105))
            self.stage_surf.blit(lbl_hex, lbl_hex.get_rect(center=(status_x, box_top + 34)))

        title_surf = self.fonts['large'].render(f'Programm: {self.comment}', True, (245, 245, 250))
        self.stage_surf.blit(title_surf, (30, 18))

        current_bar = int(self.current_beat // 4) + 1
        beat_in_bar = (self.current_beat % 4) + 1
        time_info = f'Position: Beat {self.current_beat:05.2f} / {self.timeline_length:.1f}  |  Takt {current_bar}, Schlag {beat_in_bar:04.2f}'
        info_surf = self.fonts['main'].render(time_info, True, (160, 170, 185))
        self.stage_surf.blit(info_surf, (30, 48))

        setup_badge = self.fonts['mini'].render('Hardware: 6x PAR-Spots  |  10x Tubes  |  4x Laserworld EL-300 RGB', True, (100, 110, 130))
        self.stage_surf.blit(setup_badge, (30, 70))

        beat_fract = self.current_beat % 1.0
        pulse_alpha = max(0, int(255 * (1.0 - beat_fract * 4.0)))
        if pulse_alpha > 0:
            pulse_dot = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(pulse_dot, (0, 220, 120, pulse_alpha), (6, 6), 6)
            self.stage_surf.blit(pulse_dot, (info_surf.get_width() + 45, 52))

        self.stage_surf.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_ADD)
        self.screen.blit(self.stage_surf, (self.sidebar_w, 0))

    def draw_sidebar(self):
        sidebar_rect = pygame.Rect(0, 0, self.sidebar_w, self.height)
        pygame.draw.rect(self.screen, (16, 18, 24), sidebar_rect)
        pygame.draw.line(self.screen, (35, 40, 52), (self.sidebar_w - 1, 0), (self.sidebar_w - 1, self.height), 1)

        head_lbl = self.fonts['header'].render('FILE EXPLORER', True, (230, 235, 245))
        self.screen.blit(head_lbl, (15, 14))

        folder_display = os.path.basename(self.current_dir) or self.current_dir
        if len(folder_display) > 28:
            folder_display = folder_display[:25] + '...'
        label = 'Root: ' + folder_display
        f_surf = self.fonts['meta'].render(label, True, (130, 140, 160))
        self.screen.blit(f_surf, (15, 33))

        self.btn_choose_dir.draw(self.screen, self.fonts)
        self.btn_parent_dir.draw(self.screen, self.fonts)
        self.btn_rename_item.draw(self.screen, self.fonts)
        self.btn_delete_item.draw(self.screen, self.fonts)

        pygame.draw.line(self.screen, (32, 36, 46), (15, 118), (self.sidebar_w - 15, 118), 1)

        list_y = self.list_y
        list_h = self.height - list_y - 15
        list_w = self.sidebar_w - 20
        total_h = len(self.entry_items) * self.item_h
        max_scroll = max(0, total_h - list_h)
        self.scroll_y = max(0.0, min(self.scroll_y, float(max_scroll)))

        clip_rect = pygame.Rect(10, list_y, list_w + 10, list_h)
        self.screen.set_clip(clip_rect)
        mx, my = pygame.mouse.get_pos()

        if not self.entry_items:
            empty_msg = self.fonts['main'].render('Keine Ordner / .txt Dateien', True, (110, 115, 130))
            self.screen.blit(empty_msg, (20, list_y + 30))
        else:
            for idx, item in enumerate(self.entry_items):
                iy = list_y + idx * self.item_h - int(self.scroll_y)
                if iy + self.item_h < list_y or iy > list_y + list_h:
                    continue

                depth = max(0, item.get('depth', 0))
                x_offset = 12 + depth * 16
                item_rect = pygame.Rect(x_offset, iy, list_w - x_offset - 4, self.item_h - 4)
                is_failed = item['path'] in self.failed_files
                is_active = (self.active_file_path == item['path']) and item['kind'] == 'file' and not is_failed
                is_selected = (self.selected_path == item['path']) and not is_active
                is_hover = item_rect.collidepoint((mx, my))

                if is_failed:
                    bg_color = (42, 22, 25) if not is_hover else (55, 26, 30)
                    border_color = (200, 60, 65)
                elif is_active:
                    bg_color = (30, 55, 95)
                    border_color = (65, 135, 240)
                elif is_selected:
                    bg_color = (28, 38, 55) if not is_hover else (35, 46, 68)
                    border_color = (90, 130, 185)
                elif is_hover:
                    bg_color = (26, 30, 40)
                    border_color = (55, 65, 80)
                else:
                    bg_color = (20, 23, 30)
                    border_color = (32, 36, 46)

                pygame.draw.rect(self.screen, bg_color, item_rect, border_radius=4)
                pygame.draw.rect(self.screen, border_color, item_rect, 1, border_radius=4)

                if item['kind'] == 'dir':
                    exp_symbol = 'v' if item['path'] in self.expanded_dirs else '>'
                    exp_surf = self.fonts['main'].render(exp_symbol, True, (170, 200, 255))
                    self.screen.blit(exp_surf, (x_offset + 8, iy + 7))
                    name_prefix = ''
                else:
                    name_prefix = ''
                    if is_failed:
                        pygame.draw.rect(self.screen, (220, 60, 65), (item_rect.x, item_rect.y, 4, item_rect.h), border_radius=2)
                    elif is_active:
                        pygame.draw.rect(self.screen, (60, 140, 255), (item_rect.x, item_rect.y, 4, item_rect.h), border_radius=2)
                    elif is_selected:
                        pygame.draw.rect(self.screen, (100, 150, 220), (item_rect.x, item_rect.y, 3, item_rect.h), border_radius=2)

                if self.inline_rename_target == item['path']:
                    input_rect = pygame.Rect(item_rect.x + 18, item_rect.y + 10, max(120, item_rect.w - 26), max(18, item_rect.h - 18))
                    pygame.draw.rect(self.screen, (18, 26, 42), input_rect, border_radius=4)
                    pygame.draw.rect(self.screen, (75, 130, 255), input_rect, 1, border_radius=4)

                    sel_start, sel_end = self.inline_rename_selection
                    sel_start = max(0, min(sel_start, len(self.inline_rename_value)))
                    sel_end = max(0, min(sel_end, len(self.inline_rename_value)))
                    if sel_start > sel_end:
                        sel_start, sel_end = sel_end, sel_start

                    before = self.inline_rename_value[:sel_start]
                    selected = self.inline_rename_value[sel_start:sel_end]
                    after = self.inline_rename_value[sel_end:]

                    before_surf = self.fonts['main'].render(before, True, (245, 248, 255))
                    selected_surf = self.fonts['main'].render(selected, True, (15, 18, 24))
                    after_surf = self.fonts['main'].render(after, True, (245, 248, 255))

                    text_x = input_rect.x + 8
                    text_y = input_rect.y + 2
                    self.screen.blit(before_surf, (text_x, text_y))
                    sel_box = pygame.Rect(text_x + before_surf.get_width(), text_y, max(selected_surf.get_width(), 6), selected_surf.get_height())
                    if sel_start != sel_end:
                        pygame.draw.rect(self.screen, (120, 180, 255), sel_box, border_radius=2)
                        self.screen.blit(selected_surf, (sel_box.x + 1, text_y))
                    else:
                        cursor_x = text_x + before_surf.get_width()
                        pygame.draw.line(self.screen, (220, 230, 255), (cursor_x, text_y + 1), (cursor_x, text_y + selected_surf.get_height() - 2), 1)
                    self.screen.blit(after_surf, (sel_box.x + max(sel_box.width, selected_surf.get_width()), text_y))
                else:
                    display_name = item['name']
                    if len(display_name) > 26:
                        display_name = display_name[:23] + '...'
                    t_color = (255, 255, 255) if is_active else (215, 220, 230)
                    if item['kind'] == 'dir':
                        t_color = (180, 210, 255)
                    name_surf = self.fonts['bold' if is_active else 'main'].render(name_prefix + display_name, True, t_color)
                    self.screen.blit(name_surf, (x_offset + 24, item_rect.y + 6))

                if self.inline_rename_target != item['path']:
                    if item['kind'] == 'dir':
                        meta = 'Ordner'
                    elif is_failed:
                        meta = 'Format ungültig / Fehler'
                    else:
                        dt_str = datetime.datetime.fromtimestamp(item['mtime']).strftime('%d.%m.%y %H:%M')
                        size_kb = item['size'] / 1024.0
                        size_str = f'{size_kb:.1f} KB' if size_kb >= 1.0 else f'{item["size"]} B'
                        meta = f'{dt_str}  •  {size_str}'
                    meta_surf = self.fonts['meta'].render(meta, True, (110, 120, 135))
                    self.screen.blit(meta_surf, (x_offset + 40, item_rect.y + 26))

        self.screen.set_clip(None)

        if total_h > list_h:
            bar_x = self.sidebar_w - 9
            bar_y = list_y
            bar_w = 4
            bar_h = list_h
            pygame.draw.rect(self.screen, (24, 28, 36), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
            thumb_h = max(25, int(bar_h * (bar_h / total_h)))
            thumb_y = bar_y + int((self.scroll_y / max_scroll) * (bar_h - thumb_h))
            pygame.draw.rect(self.screen, (70, 80, 100), (bar_x, thumb_y, bar_w, thumb_h), border_radius=2)

    def draw_ui(self):
        panel_rect = pygame.Rect(self.sidebar_w, 600, self.stage_w, 160)
        pygame.draw.rect(self.screen, (18, 20, 26), panel_rect)
        pygame.draw.line(self.screen, (35, 40, 52), (self.sidebar_w, 600), (self.width, 600), 1)

        t_rect = self.timeline_slider.rect
        total = self.timeline_slider.max_val
        for b in range(int(total) + 1):
            px = t_rect.x + int((b / total) * t_rect.width)
            is_bar = b % 4 == 0
            h = 8 if is_bar else 4
            color = (130, 140, 160) if is_bar else (60, 65, 75)
            pygame.draw.line(self.screen, color, (px, t_rect.bottom + 2), (px, t_rect.bottom + 2 + h))
            if is_bar:
                bar_lbl = self.fonts['small'].render(f'T{b//4 + 1}', True, (110, 120, 135))
                self.screen.blit(bar_lbl, bar_lbl.get_rect(center=(px, t_rect.bottom + 18)))

        self.btn_play.draw(self.screen, self.fonts)
        self.btn_rewind.draw(self.screen, self.fonts)
        self.btn_loop.draw(self.screen, self.fonts)
        self.bpm_slider.draw(self.screen, self.fonts['main'])
        self.timeline_slider.draw(self.screen, self.fonts['main'])

        shortcuts = 'Shortcuts: Leertaste (Play/Pause) | R (Reset) | L (Loop) | F2 (Rename) | Entf (Löschen) | Pfeiltasten'
        sc_surf = self.fonts['small'].render(shortcuts, True, (90, 95, 110))
        self.screen.blit(sc_surf, (self.width - sc_surf.get_width() - 30, 725))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEWHEEL:
                    mx, _ = pygame.mouse.get_pos()
                    if mx < self.sidebar_w:
                        self.scroll_y -= event.y * 28
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if mx < self.sidebar_w and my >= self.list_y:
                        clicked_idx = int((my - self.list_y + self.scroll_y) // self.item_h)
                        if 0 <= clicked_idx < len(self.entry_items):
                            item = self.entry_items[clicked_idx]
                            self.selected_path = item['path']
                            if self.inline_rename_target == item['path']:
                                continue
                            if item['kind'] == 'dir':
                                self.toggle_dir_expanded(item['path'])
                                self.selected_path = item['path']
                            else:
                                self.current_dir = os.path.dirname(item['path'])
                                self.load_file(item['path'])
                elif event.type == pygame.KEYDOWN:
                    if self.inline_rename_target:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            self.commit_inline_rename()
                        elif event.key == pygame.K_ESCAPE:
                            self.cancel_inline_rename()
                        elif event.key == pygame.K_BACKSPACE:
                            sel_start, sel_end = self.inline_rename_selection
                            if sel_start != sel_end:
                                self.inline_rename_value = self.inline_rename_value[:sel_start] + self.inline_rename_value[sel_end:]
                                self.inline_rename_cursor = sel_start
                                self.inline_rename_selection = (sel_start, sel_start)
                            elif self.inline_rename_cursor > 0:
                                self.inline_rename_value = self.inline_rename_value[:self.inline_rename_cursor - 1] + self.inline_rename_value[self.inline_rename_cursor:]
                                self.inline_rename_cursor = max(0, self.inline_rename_cursor - 1)
                                self.inline_rename_selection = (self.inline_rename_cursor, self.inline_rename_cursor)
                        elif event.key == pygame.K_LEFT:
                            self.inline_rename_cursor = max(0, self.inline_rename_cursor - 1)
                            self.inline_rename_selection = (self.inline_rename_cursor, self.inline_rename_cursor)
                        elif event.key == pygame.K_RIGHT:
                            self.inline_rename_cursor = min(len(self.inline_rename_value), self.inline_rename_cursor + 1)
                            self.inline_rename_selection = (self.inline_rename_cursor, self.inline_rename_cursor)
                        elif event.key == pygame.K_HOME:
                            self.inline_rename_cursor = 0
                            self.inline_rename_selection = (0, 0)
                        elif event.key == pygame.K_END:
                            self.inline_rename_cursor = len(self.inline_rename_value)
                            self.inline_rename_selection = (self.inline_rename_cursor, self.inline_rename_cursor)
                        elif event.unicode and event.unicode.isprintable() and event.unicode not in '\r\n\t':
                            sel_start, sel_end = self.inline_rename_selection
                            if sel_start != sel_end:
                                self.inline_rename_value = self.inline_rename_value[:sel_start] + event.unicode + self.inline_rename_value[sel_end:]
                                self.inline_rename_cursor = sel_start + 1
                            else:
                                self.inline_rename_value = self.inline_rename_value[:self.inline_rename_cursor] + event.unicode + self.inline_rename_value[self.inline_rename_cursor:]
                                self.inline_rename_cursor += 1
                            self.inline_rename_selection = (self.inline_rename_cursor, self.inline_rename_cursor)
                        continue

                    if event.key == pygame.K_SPACE:
                        self.toggle_play()
                    elif event.key == pygame.K_r:
                        self.rewind()
                    elif event.key == pygame.K_l:
                        self.toggle_loop()
                    elif event.key == pygame.K_F2:
                        self.rename_selected_item()
                    elif event.key == pygame.K_DELETE:
                        self.delete_selected_item()
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

                self.btn_choose_dir.handle_event(event)
                self.btn_parent_dir.handle_event(event)
                self.btn_rename_item.handle_event(event)
                self.btn_delete_item.handle_event(event)
                self.bpm_slider.handle_event(event)
                self.timeline_slider.handle_event(event)
                self.btn_play.handle_event(event)
                self.btn_rewind.handle_event(event)
                self.btn_loop.handle_event(event)

            self.update(dt)
            self.draw_stage()
            self.draw_sidebar()
            self.draw_ui()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    initial_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = LightingPreviewer5(initial_path)
    app.run()
