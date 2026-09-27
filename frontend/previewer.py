import math
import os
import sys
import tkinter as tk
from tkinter import filedialog
import pygame

# ==============================================================================
# DEFAULT DEMO PROGRAMM (Wird geladen, wenn keine Datei übergeben wird)
# ==============================================================================

DEFAULT_SCRIPT ="""// Test-Fahrt 16 RGB-Pixel (Hin & Rueck)
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
Spot6:0#000000;7.5#000000;7.5#FFFFFF;8#000000;8#00FFFF;8.5#000000;16#000000"""

# ==============================================================================
# PARSER & FARB-INTERPOLATION
# ==============================================================================
def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
  hex_str = hex_str.strip().lstrip('#')
  if len(hex_str) != 6:
    return (0, 0, 0)
  return (
      int(hex_str[0:2], 16),
      int(hex_str[2:4], 16),
      int(hex_str[4:6], 16),
  )


class DeviceTrack:
  """Verwaltet Stützpunkte und die lineare Farbinterpolation mit Unterstützung

  für unendlich schnelle Farbwechsel (identische Beat-Positionen).
  """

  def __init__(self, name: str, keyframes: list[tuple[float, tuple[int, int, int]]]):
    self.name = name
    # Stützpunkte zeitlich sortieren
    self.keyframes = sorted(keyframes, key=lambda x: x[0])
    self.segments = []

    # Segmente mit echter Zeitdauer aufbauen
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

    # Das passende zeitliche Segment suchen
    for t1, c1, t2, c2 in self.segments:
      if t1 <= beat < t2:
        factor = (beat - t1) / (t2 - t1)
        r = int(c1[0] + factor * (c2[0] - c1[0]))
        g = int(c1[1] + factor * (c2[1] - c1[1]))
        b = int(c1[2] + factor * (c2[2] - c1[2]))
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    return self.keyframes[-1][1]


def parse_dsl_content(content: str):
  lines = content.splitlines()
  comment = 'Unbenannt'
  tracks = {}
  max_beat = 0.0

  for line in lines:
    line = line.strip()
    if not line:
      continue
    if line.startswith('//') or line.startswith('#'):
      comment = line.lstrip('/#').strip()
      continue

    if ':' not in line:
      continue

    dev_name, data = line.split(':', 1)
    dev_name = dev_name.strip()
    tokens = data.split(';')
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
      tracks[dev_name] = DeviceTrack(dev_name, keyframes)

  # Mindestens 4 Viertelnoten (1 Takt) als Standardumfang
  if max_beat <= 0:
    max_beat = 4.0

  return comment, tracks, max_beat


# ==============================================================================
# UI ELEMENTE
# ==============================================================================
class Slider:

  def __init__(
      self,
      x,
      y,
      w,
      h,
      min_val,
      max_val,
      initial_val,
      label='',
      unit='',
      is_int=True,
  ):
    self.rect = pygame.Rect(x, y, w, h)
    self.min_val = min_val
    self.max_val = max_val
    self.val = initial_val
    self.label = label
    self.unit = unit
    self.is_int = is_int
    self.dragging = False

  def draw(self, screen, font):
    pygame.draw.rect(screen, (40, 44, 52), self.rect, border_radius=4)
    # Füllung
    fill_ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
    fill_w = int(self.rect.width * fill_ratio)
    fill_rect = pygame.Rect(
        self.rect.x, self.rect.y, fill_w, self.rect.height
    )
    pygame.draw.rect(screen, (70, 130, 240), fill_rect, border_radius=4)
    pygame.draw.rect(screen, (90, 100, 115), self.rect, 1, border_radius=4)

    # Knob
    knob_x = self.rect.x + fill_w
    pygame.draw.circle(screen, (240, 240, 250), (knob_x, self.rect.centery), 8)
    pygame.draw.circle(screen, (20, 20, 30), (knob_x, self.rect.centery), 3)

    # Text
    val_str = (
        f'{int(self.val)}' if self.is_int else f'{self.val:.2f}'
    ) + self.unit
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
    color = (60, 110, 200) if self.active else (45, 50, 60)
    pygame.draw.rect(screen, color, self.rect, border_radius=6)
    pygame.draw.rect(screen, (80, 90, 105), self.rect, 1, border_radius=6)
    txt_surf = font.render(self.text, True, (240, 240, 245))
    screen.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

  def handle_event(self, event):
    if (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
        and self.rect.collidepoint(event.pos)
    ):
      self.callback()


# ==============================================================================
# HAUPTPROGRAMM (PREVIEWER ENGINE)
# ==============================================================================
class TubePreviewer:

  def __init__(self, initial_source=None):
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption('ApeLabs RGB-Stick Previewer')

    self.width = 1280
    self.height = 760
    self.screen = pygame.display.set_mode((self.width, self.height))
    self.clock = pygame.time.Clock()

    self.font_main = pygame.font.SysFont('Segoe UI', 15)
    self.font_bold = pygame.font.SysFont('Segoe UI', 15, bold=True)
    self.font_large = pygame.font.SysFont('Segoe UI', 22, bold=True)
    self.font_small = pygame.font.SysFont('Consolas', 12)

    self.current_beat = 0.0
    self.playing = True
    self.loop = True
    self.bpm_slider = Slider(
        x=50,
        y=690,
        w=180,
        h=14,
        min_val=40,
        max_val=220,
        initial_val=120,
        label='Tempo',
        unit=' BPM',
        is_int=True,
    )
    self.timeline_slider = Slider(
        x=280,
        y=690,
        w=680,
        h=14,
        min_val=0,
        max_val=8.0,
        initial_val=0,
        label='Timeline (Scrubbing)',
        unit=' Beats',
        is_int=False,
    )

    self.btn_play = Button(
        x=50, y=630, w=90, h=30, text='Pause', callback=self.toggle_play
    )
    self.btn_rewind = Button(
        x=150, y=630, w=80, h=30, text='Reset', callback=self.rewind
    )
    self.btn_loop = Button(
        x=240, y=630, w=90, h=30, text='Loop: An', callback=self.toggle_loop
    )
    self.btn_open = Button(
        x=1080,
        y=630,
        w=150,
        h=30,
        text='Datei laden...',
        callback=self.open_file_dialog,
    )

    # Standard-Geräte 01 bis 10
    self.default_device_names = [f'Tube{i:02d}' for i in range(1, 11)]

    # Dateiinhalt einlesen
    if initial_source and os.path.exists(initial_source):
      with open(initial_source, 'r', encoding='utf-8') as f:
        self.raw_data = f.read()
    else:
      self.raw_data = DEFAULT_SCRIPT

    self.load_program_data(self.raw_data)

  def load_program_data(self, content: str):
    self.comment, self.tracks, self.max_beat = parse_dsl_content(content)
    # Timeline-Länge anpassen (aufgerundet auf ganze Viertel/Takte)
    total_beats = math.ceil(self.max_beat)
    if total_beats % 4 != 0:
      total_beats = math.ceil(total_beats / 4) * 4

    self.timeline_length = max(4.0, float(total_beats))
    self.timeline_slider.max_val = self.timeline_length
    self.current_beat = 0.0

  def toggle_play(self):
    self.playing = not self.playing
    self.btn_play.text = 'Pause' if self.playing else 'Play'
    self.btn_play.active = not self.playing

  def rewind(self):
    self.current_beat = 0.0

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

  def update(self, dt: float):
    # Wenn der Nutzer nicht gerade die Timeline zieht, Beat fortschreiben
    if not self.timeline_slider.dragging:
      if self.playing:
        beats_per_second = self.bpm_slider.val / 60.0
        self.current_beat += beats_per_second * dt
        if self.current_beat >= self.timeline_length:
          if self.loop:
            self.current_beat = self.current_beat % self.timeline_length
          else:
            self.current_beat = self.timeline_length
            self.playing = False
            self.btn_play.text = 'Play'
      self.timeline_slider.val = self.current_beat
    else:
      self.current_beat = self.timeline_slider.val

  def draw_stage(self):
    # Dunkler Raum mit dezentem Bühnenverlauf
    self.screen.fill((10, 11, 14))

    # Bühnenboden-Horizontlinie
    floor_y = 515
    pygame.draw.line(self.screen, (25, 28, 35), (0, floor_y), (self.width, floor_y), 2)

    # Verfügbare Sticks ermitteln (entweder definierte 10 oder alle in der Datei)
    dev_names = (
        self.default_device_names
        if all(k in self.tracks for k in self.default_device_names)
        else sorted(self.tracks.keys())
    )
    if not dev_names:
      dev_names = self.default_device_names

    num_sticks = len(dev_names)
    margin_x = 90
    available_w = self.width - 2 * margin_x
    spacing = available_w / (num_sticks - 1) if num_sticks > 1 else available_w

    stick_w = 22
    stick_h = 340
    top_y = floor_y - stick_h - 15

    # Separate Oberfläche mit additiver Farbmischung für den Glow/Bloom
    glow_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

    for idx, name in enumerate(dev_names):
      cx = int(margin_x + idx * spacing)
      track = self.tracks.get(name)
      color = track.get_color(self.current_beat) if track else (0, 0, 0)
      r, g, b = color
      intensity = max(r, g, b) / 255.0

      # -------------------------------------------------------------
      # 1. REALISTISCHE AURA / GLOW (Mehrschichtig auf Glow-Surface)
      # -------------------------------------------------------------
      if intensity > 0.03:
        # Äußere weiche Streuung
        glow_r1 = pygame.Rect(cx - 50, top_y - 20, 100, stick_h + 40)
        pygame.draw.ellipse(
            glow_surf,
            (r, g, b, int(22 * intensity)),
            glow_r1,
        )
        # Mittlerer Halo
        glow_r2 = pygame.Rect(cx - 30, top_y - 10, 60, stick_h + 20)
        pygame.draw.ellipse(
            glow_surf,
            (r, g, b, int(50 * intensity)),
            glow_r2,
        )
        # Kern-Aura
        glow_r3 = pygame.Rect(cx - 18, top_y, 36, stick_h)
        pygame.draw.ellipse(
            glow_surf,
            (r, g, b, int(95 * intensity)),
            glow_r3,
        )

        # Bodenreflexion (spiegelt die Röhre nach unten)
        refl_rect = pygame.Rect(cx - 24, floor_y + 8, 48, 55)
        pygame.draw.ellipse(
            glow_surf,
            (r, g, b, int(45 * intensity)),
            refl_rect,
        )

      # -------------------------------------------------------------
      # 2. DIE Tube RÖHRE (Diffusor & Sockel)
      # -------------------------------------------------------------
      # Standfuß (Puck)
      pygame.draw.rect(
          self.screen,
          (35, 38, 45),
          (cx - 15, floor_y - 15, 30, 15),
          border_radius=3,
      )
      pygame.draw.rect(
          self.screen,
          (55, 60, 70),
          (cx - 15, floor_y - 15, 30, 15),
          1,
          border_radius=3,
      )

      # Röhrenkörper
      tube_rect = pygame.Rect(cx - stick_w // 2, top_y, stick_w, stick_h)
      if intensity > 0:
        # Aktiv leuchtender Diffusor
        pygame.draw.rect(
            self.screen, color, tube_rect, border_radius=stick_w // 2
        )

        # Weißer Glanzkern in der Mitte (simuliert starke LED-Emittersättigung)
        core_r = min(255, int(r * 0.4 + 255 * 0.6))
        core_g = min(255, int(g * 0.4 + 255 * 0.6))
        core_b = min(255, int(b * 0.4 + 255 * 0.6))
        core_w = max(4, stick_w // 4)
        core_rect = pygame.Rect(
            cx - core_w // 2, top_y + 4, core_w, stick_h - 8
        )
        pygame.draw.rect(
            self.screen,
            (core_r, core_g, core_b),
            core_rect,
            border_radius=core_w // 2,
        )
      else:
        # Ausgeschaltete Röhre (milchiges mattes Acrylglas)
        pygame.draw.rect(
            self.screen, (22, 25, 30), tube_rect, border_radius=stick_w // 2
        )
        pygame.draw.rect(
            self.screen,
            (38, 42, 50),
            tube_rect,
            1,
            border_radius=stick_w // 2,
        )

      # Röhren-Endkappe oben
      pygame.draw.ellipse(
          self.screen, (40, 44, 52), (cx - stick_w // 2, top_y - 2, stick_w, 6)
      )

      # -------------------------------------------------------------
      # 3. LABELS & FARB-HEXCODE
      # -------------------------------------------------------------
      lbl_name = self.font_small.render(name, True, (130, 140, 155))
      self.screen.blit(
          lbl_name, lbl_name.get_rect(center=(cx, floor_y + 24))
      )

      hex_code = f'#{r:02X}{g:02X}{b:02X}'
      col_indicator = (r, g, b) if intensity > 0.3 else (100, 105, 115)
      lbl_hex = self.font_small.render(hex_code, True, col_indicator)
      self.screen.blit(lbl_hex, lbl_hex.get_rect(center=(cx, floor_y + 40)))

    # Glow mit additiver Verblendung auf die Szene zeichnen
    self.screen.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_ADD)

  def draw_ui(self):
    # Bedienleisten-Hintergrund
    panel_rect = pygame.Rect(0, 600, self.width, 160)
    pygame.draw.rect(self.screen, (18, 20, 25), panel_rect)
    pygame.draw.line(self.screen, (35, 40, 50), (0, 600), (self.width, 600), 1)

    # Programmtitel & Metadaten oben links
    title_surf = self.font_large.render(
        f'Programm: {self.comment}', True, (245, 245, 250)
    )
    self.screen.blit(title_surf, (30, 20))

    # Takt- und Zeitberechnung
    current_bar = int(self.current_beat // 4) + 1
    beat_in_bar = (self.current_beat % 4) + 1
    time_info = (
        f'Position: Beat {self.current_beat:05.2f} /'
        f' {self.timeline_length:.1f}  |  Takt {current_bar}, Schlag'
        f' {beat_in_bar:04.2f}'
    )
    info_surf = self.font_main.render(time_info, True, (160, 170, 185))
    self.screen.blit(info_surf, (30, 50))

    # Visueller Metronom-Puls (leuchtet kurz auf jeder Viertelnote auf)
    beat_fract = self.current_beat % 1.0
    pulse_alpha = max(0, int(255 * (1.0 - beat_fract * 4.0)))
    if pulse_alpha > 0:
      pulse_dot = pygame.Surface((12, 12), pygame.SRCALPHA)
      pygame.draw.circle(
          pulse_dot, (0, 220, 120, pulse_alpha), (6, 6), 6
      )
      self.screen.blit(pulse_dot, (info_surf.get_width() + 45, 54))

    # Takt-Markierungen auf der Timeline einzeichnen
    t_rect = self.timeline_slider.rect
    total = self.timeline_slider.max_val
    for b in range(int(total) + 1):
      px = t_rect.x + int((b / total) * t_rect.width)
      is_bar = b % 4 == 0
      h = 8 if is_bar else 4
      color = (130, 140, 160) if is_bar else (65, 70, 80)
      pygame.draw.line(
          self.screen, color, (px, t_rect.bottom + 2), (px, t_rect.bottom + 2 + h)
      )
      if is_bar:
        bar_lbl = self.font_small.render(f'T{b//4 + 1}', True, (110, 120, 135))
        self.screen.blit(
            bar_lbl, bar_lbl.get_rect(center=(px, t_rect.bottom + 18))
        )

    # Buttons und Regler rendern
    self.btn_play.draw(self.screen, self.font_bold)
    self.btn_rewind.draw(self.screen, self.font_main)
    self.btn_loop.draw(self.screen, self.font_main)
    self.btn_open.draw(self.screen, self.font_bold)
    self.bpm_slider.draw(self.screen, self.font_main)
    self.timeline_slider.draw(self.screen, self.font_main)

    # Hotkey-Hilfe
    shortcuts = (
        'Shortcuts: Leertaste (Play/Pause) | R (Reset) | L (Loop) | Pfeile'
        ' (BPM / Scrub)'
    )
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
          elif event.key == pygame.K_RIGHT:
            self.current_beat = min(
                self.timeline_length, self.current_beat + 1.0
            )

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
  # Wenn eine Datei via Kommandozeile übergeben wird (z. B. `python previewer.py show.txt`)
  initial_file = sys.argv[1] if len(sys.argv) > 1 else None
  app = TubePreviewer(initial_file)
  app.run()