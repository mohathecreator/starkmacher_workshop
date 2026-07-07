"""
visualization.py
================

Aufgabe: Alles, was man auf dem Bildschirm sieht.

Diese Datei kuemmert sich NUR um die Grafik (mit pygame). Sie rechnet nichts
aus, sie zeigt nur an, was der Simulator berechnet hat. So sind "Rechnen"
und "Zeichnen" sauber getrennt.

Die Visualisierung zeigt:
  - die Strecke (Fahrbahn, Raender, Waypoints, Bremszonen)
  - das Auto (als Bild) mit Blickrichtung und Spur
  - den Zielpunkt des Controllers
  - eine Info-Anzeige (HUD): Geschwindigkeit, Rundenzeit, beste Zeit, Runde
  - ein Startmenue (Challenge Mode)
  - die grosse Rundenzeit-Anzeige am Ende jeder Runde

Wichtig: Die Weltkoordinaten der Strecke (in Metern) muessen in
Bildschirm-Pixel umgerechnet werden. Das macht world_to_screen().
"""

import math
import os

import pygame

# Die Hoechstgeschwindigkeit (fuer den Tacho-Balken) gehoert zum Auto.
from physics import Physics


# ===========================================================================
#  Anzeige-Einstellungen (Fenster, Farben, was gezeichnet wird).
#  Diese Werte betreffen nur die Optik - fuer schnellere Runden aendert man
#  sie NICHT. Die eigentlichen Fahr-Parameter stehen in physics.py,
#  controller.py und track.py.
# ===========================================================================

# --- Fenster ---------------------------------------------------------------
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 760

# --- Was soll angezeigt werden? --------------------------------------------
SHOW_WAYPOINTS = True     # Waypoints der Strecke anzeigen
SHOW_TRAIL = True         # Spur hinter dem Auto anzeigen
SHOW_TARGET = True        # Zielpunkt des Controllers anzeigen (Pure Pursuit)
SHOW_BRAKE_ZONES = True   # Bremszonen (rote Waypoints) anzeigen
USE_TRACK_IMAGE = False   # Eigenes Strecken-PNG als Hintergrund verwenden
#   Wenn True: liegt neben der Streckendatei eine gleichnamige PNG
#   (z.B. tracks/race_track.png), wird sie hinter der Strecke angezeigt.
#   WICHTIG: Die Waypoints in der JSON muessen zum Bild passen!

# --- Farben (R, G, B) ------------------------------------------------------
COLOR_BACKGROUND = (28, 32, 38)
COLOR_ASPHALT = (60, 64, 72)
COLOR_BOUNDARY = (235, 235, 235)
COLOR_WAYPOINT = (90, 130, 160)
COLOR_BRAKE_ZONE = (200, 80, 60)
COLOR_TRAIL = (90, 200, 255)
COLOR_TARGET = (255, 210, 60)
COLOR_TEXT = (240, 240, 240)
COLOR_START_LINE = (240, 220, 60)


class Visualization:
    """Zeichnet die Simulation mit pygame."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        pygame.display.set_caption("Formula Student Workshop")

        # Schriftarten in verschiedenen Groessen.
        self.font_small = pygame.font.SysFont("consolas", 20)
        self.font_medium = pygame.font.SysFont("consolas", 28, bold=True)
        self.font_big = pygame.font.SysFont("consolas", 90, bold=True)
        self.font_title = pygame.font.SysFont("consolas", 46, bold=True)

        # Auto-Bild laden (oder Ersatz zeichnen, falls Datei fehlt).
        self.car_image = self._load_car_image()

        # Optionales Strecken-Hintergrundbild (wird in set_track gesetzt).
        self.track_image = None

        # Werte fuer die Koordinaten-Umrechnung (werden in set_track gesetzt).
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

    # ------------------------------------------------------------------
    #  Auto-Bild
    # ------------------------------------------------------------------
    def _load_car_image(self):
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "assets", "car.png")
        if os.path.exists(path):
            return pygame.image.load(path).convert_alpha()
        # Ersatz: einfaches rotes Rechteck, falls kein Bild vorhanden ist.
        surf = pygame.Surface((64, 32), pygame.SRCALPHA)
        pygame.draw.rect(surf, (200, 30, 40), (6, 6, 52, 20), border_radius=6)
        return surf

    # ------------------------------------------------------------------
    #  Koordinaten-Umrechnung: Weltkoordinaten (Meter) -> Bildschirm (Pixel)
    # ------------------------------------------------------------------
    def set_track(self, track):
        """Berechnet, wie die Strecke ins Fenster passt (Zoom + Verschiebung)."""
        # Optionales Hintergrundbild der Strecke laden.
        self.track_image = None
        if USE_TRACK_IMAGE and track.image_path and os.path.exists(track.image_path):
            self.track_image = pygame.image.load(track.image_path).convert_alpha()

        xs = list(track.left_boundary[:, 0]) + list(track.right_boundary[:, 0])
        ys = list(track.left_boundary[:, 1]) + list(track.right_boundary[:, 1])
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        margin = 60  # Pixel Rand um die Strecke herum
        usable_w = WINDOW_WIDTH - 2 * margin
        usable_h = WINDOW_HEIGHT - 2 * margin

        world_w = max(max_x - min_x, 1e-6)
        world_h = max(max_y - min_y, 1e-6)

        # Wir waehlen den kleineren Massstab, damit alles ins Fenster passt.
        self.scale = min(usable_w / world_w, usable_h / world_h)

        # Strecke im Fenster zentrieren.
        self.offset_x = margin + (usable_w - world_w * self.scale) / 2 - min_x * self.scale
        self.offset_y = margin + (usable_h - world_h * self.scale) / 2 - min_y * self.scale
        self._world_min_x = min_x
        self._world_max_x = max_x
        self._world_min_y = min_y
        self._world_max_y = max_y

    def world_to_screen(self, point):
        """Rechnet einen Weltpunkt (x, y in Metern) in Pixel um.

        Die y-Achse wird gespiegelt, damit "oben" in der Welt auch "oben"
        auf dem Bildschirm ist (Bildschirm zaehlt y von oben nach unten).
        """
        sx = point[0] * self.scale + self.offset_x
        # y spiegeln
        flipped = self._world_max_y - (point[1] - self._world_min_y)
        sy = flipped * self.scale + self.offset_y
        return int(sx), int(sy)

    # ------------------------------------------------------------------
    #  Startmenue (Challenge Mode)
    # ------------------------------------------------------------------
    def draw_menu(self, selected):
        """Zeichnet das Auswahlmenue. 'selected' ist 0 oder 1."""
        self.screen.fill(COLOR_BACKGROUND)
        cx = WINDOW_WIDTH // 2

        title = self.font_title.render(
            "Formula Student Workshop", True, COLOR_TEXT
        )
        self.screen.blit(title, (cx - title.get_width() // 2, 120))

        line = self.font_small.render(
            "Waehle eine Strecke  (Pfeiltasten + Enter oder Taste 1 / 2)",
            True, (170, 180, 190),
        )
        self.screen.blit(line, (cx - line.get_width() // 2, 210))

        options = ["[1]  Training Track", "[2]  Race Track"]
        for i, text in enumerate(options):
            highlighted = (i == selected)
            color = COLOR_START_LINE if highlighted else COLOR_TEXT
            label = self.font_medium.render(text, True, color)
            y = 300 + i * 70
            self.screen.blit(label, (cx - label.get_width() // 2, y))
            if highlighted:
                pygame.draw.rect(
                    self.screen, color,
                    (cx - label.get_width() // 2 - 20, y - 8,
                     label.get_width() + 40, label.get_height() + 16),
                    width=2, border_radius=8,
                )

        hint = self.font_small.render(
            "Tipp: Optimiere die Werte in py fuer die schnellste Runde!",
            True, (150, 160, 170),
        )
        self.screen.blit(hint, (cx - hint.get_width() // 2, 520))
        pygame.display.flip()

    # ------------------------------------------------------------------
    #  Die Strecke zeichnen
    # ------------------------------------------------------------------
    def _draw_track(self, track):
        # Falls vorhanden: vorgezeichnetes Strecken-PNG in den Hintergrund
        # legen (auf die Ausdehnung der Strecke skaliert).
        if self.track_image is not None:
            top_left = self.world_to_screen(
                (self._world_min_x, self._world_max_y)
            )
            bottom_right = self.world_to_screen(
                (self._world_max_x, self._world_min_y)
            )
            rect = pygame.Rect(
                top_left[0], top_left[1],
                bottom_right[0] - top_left[0],
                bottom_right[1] - top_left[1],
            )
            scaled = pygame.transform.smoothscale(
                self.track_image, (max(1, rect.width), max(1, rect.height))
            )
            self.screen.blit(scaled, rect)
            return  # Bei eigenem Bild kein Asphalt-Band zeichnen.

        # Asphalt: Flaeche zwischen linkem und rechtem Rand fuellen.
        left = [self.world_to_screen(p) for p in track.left_boundary]
        right = [self.world_to_screen(p) for p in track.right_boundary]
        polygon = left + right[::-1]  # ein geschlossenes Band
        pygame.draw.polygon(self.screen, COLOR_ASPHALT, polygon)

        # Fahrbahnraender als weisse Linien.
        pygame.draw.lines(self.screen, COLOR_BOUNDARY, True, left, 3)
        pygame.draw.lines(self.screen, COLOR_BOUNDARY, True, right, 3)

        # Waypoints (Mittellinie). Bremszonen werden rot markiert.
        if SHOW_WAYPOINTS:
            for i, wp in enumerate(track.waypoints):
                pos = self.world_to_screen(wp)
                if SHOW_BRAKE_ZONES and track.is_brake_zone(i):
                    pygame.draw.circle(self.screen, COLOR_BRAKE_ZONE, pos, 3)
                else:
                    pygame.draw.circle(self.screen, COLOR_WAYPOINT, pos, 2)

        # Start-/Ziellinie.
        a = self.world_to_screen(track.start_line["left"])
        b = self.world_to_screen(track.start_line["right"])
        pygame.draw.line(self.screen, COLOR_START_LINE, a, b, 4)

    # ------------------------------------------------------------------
    #  Das Auto (und Extras) zeichnen
    # ------------------------------------------------------------------
    def _draw_vehicle(self, sim):
        vehicle = sim.vehicle

        # Spur (Trail) hinter dem Auto.
        if SHOW_TRAIL and len(sim.trail) > 1:
            points = [self.world_to_screen(p) for p in sim.trail]
            pygame.draw.lines(self.screen, COLOR_TRAIL, False, points, 2)

        # Zielpunkt des Controllers (wohin das Auto lenkt).
        if SHOW_TARGET and sim.controller.target_point is not None:
            target = self.world_to_screen(sim.controller.target_point)
            car = self.world_to_screen(vehicle.position())
            pygame.draw.line(self.screen, COLOR_TARGET, car, target, 1)
            pygame.draw.circle(self.screen, COLOR_TARGET, target, 5)

        # Blickrichtung als kurze Linie nach vorne.
        car = self.world_to_screen(vehicle.position())
        look_len = vehicle.length * 1.5
        front = (
            vehicle.x + math.cos(vehicle.heading) * look_len,
            vehicle.y + math.sin(vehicle.heading) * look_len,
        )
        pygame.draw.line(self.screen, (255, 255, 255), car,
                         self.world_to_screen(front), 1)

        # Das Auto-Bild passend zur Autolaenge skalieren und drehen.
        target_px = max(12, int(vehicle.length * self.scale))
        ratio = self.car_image.get_height() / self.car_image.get_width()
        scaled = pygame.transform.smoothscale(
            self.car_image, (target_px, int(target_px * ratio))
        )
        rotated = pygame.transform.rotate(scaled, math.degrees(vehicle.heading))
        rect = rotated.get_rect(center=car)
        self.screen.blit(rotated, rect)

    # ------------------------------------------------------------------
    #  Info-Anzeige (HUD)
    # ------------------------------------------------------------------
    def _draw_hud(self, sim):
        # Halbtransparenter Kasten oben links.
        panel = pygame.Surface((280, 170), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 130))
        self.screen.blit(panel, (15, 15))

        best = "--" if sim.best_lap_time is None else f"{sim.best_lap_time:5.2f} s"
        lines = [
            f"Strecke : {sim.track.name}",
            f"Runde   : {sim.current_lap} / {sim.total_laps}",
            f"Speed   : {sim.vehicle.speed:5.1f} m/s",
            f"Zeit    : {sim.current_lap_time():5.2f} s",
            f"Beste   : {best}",
        ]
        y = 28
        for text in lines:
            label = self.font_small.render(text, True, COLOR_TEXT)
            self.screen.blit(label, (30, y))
            y += 28

        # Kleiner Tacho-Balken fuer die Geschwindigkeit.
        frac = min(1.0, sim.vehicle.speed / max(Physics.MAX_SPEED, 1e-6))
        bar_x, bar_y, bar_w, bar_h = 30, y + 4, 240, 12
        pygame.draw.rect(self.screen, (70, 70, 80), (bar_x, bar_y, bar_w, bar_h),
                         border_radius=6)
        pygame.draw.rect(self.screen, (90, 200, 255),
                         (bar_x, bar_y, int(bar_w * frac), bar_h), border_radius=6)

    # ------------------------------------------------------------------
    #  Grosse Rundenzeit-Anzeige am Ende einer Runde
    # ------------------------------------------------------------------
    def _draw_big_lap_time(self, result):
        # Abdunkeln.
        overlay = pygame.Surface(
            (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2

        head = self.font_medium.render(
            f"Runde {result.lap_number} beendet!", True, COLOR_TEXT
        )
        self.screen.blit(head, (cx - head.get_width() // 2, cy - 130))

        time_text = self.font_big.render(
            f"{result.lap_time:.2f} s", True, COLOR_START_LINE
        )
        self.screen.blit(time_text, (cx - time_text.get_width() // 2, cy - 60))

        score = self.font_medium.render(
            f"Score: {result.score:.0f}", True, COLOR_TEXT
        )
        self.screen.blit(score, (cx - score.get_width() // 2, cy + 50))

    # ------------------------------------------------------------------
    #  Crash-Anzeige (Auto hat die Begrenzung beruehrt)
    # ------------------------------------------------------------------
    def _draw_crash(self, sim):
        # Rot abdunkeln.
        overlay = pygame.Surface(
            (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((60, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2

        crash = self.font_big.render("CRASH!", True, (255, 80, 70))
        self.screen.blit(crash, (cx - crash.get_width() // 2, cy - 90))

        info = self.font_medium.render(
            "Auto hat die Begrenzung beruehrt.", True, COLOR_TEXT
        )
        self.screen.blit(info, (cx - info.get_width() // 2, cy + 20))

        hint = self.font_small.render(
            "Werte anpassen (z.B. langsamer in Kurven), dann neu versuchen.",
            True, (230, 200, 200),
        )
        self.screen.blit(hint, (cx - hint.get_width() // 2, cy + 70))

        key = self.font_small.render(
            "Taste druecken fuer Menue  -  ESC zum Beenden",
            True, (200, 200, 210),
        )
        self.screen.blit(key, (cx - key.get_width() // 2, cy + 110))

    # ------------------------------------------------------------------
    #  Ein komplettes Bild zeichnen
    # ------------------------------------------------------------------
    def draw_frame(self, sim, big_lap_result=None, crashed=False):
        """Zeichnet ein vollstaendiges Bild der Simulation."""
        self.screen.fill(COLOR_BACKGROUND)
        self._draw_track(sim.track)
        self._draw_vehicle(sim)
        self._draw_hud(sim)
        if big_lap_result is not None:
            self._draw_big_lap_time(big_lap_result)
        if crashed:
            self._draw_crash(sim)
        pygame.display.flip()

    def quit(self):
        pygame.quit()
