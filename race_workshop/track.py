"""
track.py
========

Aufgabe: Die Rennstrecke.

Die Klasse Track laedt eine Strecke aus einer JSON-Datei und stellt alles
bereit, was Controller und Simulation ueber die Strecke wissen muessen:

  - die Mittellinie (Waypoints)
  - linker und rechter Fahrbahnrand
  - Start-/Ziellinie
  - fuer jeden Waypoint eine erlaubte Kurvengeschwindigkeit
    (in engen Kurven kleiner als auf Geraden)

Ausserdem beantwortet der Track Fragen wie:
  - "Welcher Waypoint ist meinem Auto am naechsten?"
  - "Wie weit bin ich von der Ideallinie (Mitte) entfernt?"  -> Offtrack?
  - "Wo ist mein Zielpunkt ein Stueck vor mir?"               -> Pure Pursuit
"""

import json
import math

import numpy as np

# Die Hoechstgeschwindigkeit gehoert zum Auto und steht in physics.py.
from physics import Physics


class Track:
    """Repraesentiert eine geschlossene Rennstrecke aus Waypoints."""

    def __init__(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Optionales Hintergrundbild der Strecke: liegt neben der JSON-Datei
        # eine gleichnamige PNG (z.B. race_track.png), kann sie als
        # vorgezeichnete Strecke im Hintergrund angezeigt werden.
        self.image_path = filepath[:-5] + ".png" if filepath.endswith(".json") else None

        self.name = data["name"]
        self.width = float(data["track_width"])

        # numpy-Arrays, weil sich damit Abstaende schnell berechnen lassen.
        self.waypoints = np.array(data["waypoints"], dtype=float)
        self.left_boundary = np.array(data["left_boundary"], dtype=float)
        self.right_boundary = np.array(data["right_boundary"], dtype=float)
        self.start_line = data["start_line"]

        self.num_points = len(self.waypoints)

        # Fuer jeden Waypoint einmalig die erlaubte Geschwindigkeit ausrechnen.
        self.speed_limits = self._compute_speed_limits()

    # ------------------------------------------------------------------
    #  Geschwindigkeits-Limits pro Waypoint (abhaengig von der Kurve)
    # ------------------------------------------------------------------
    def _compute_speed_limits(self):
        """Berechnet fuer jeden Waypoint eine erlaubte Geschwindigkeit.

        In engen Kurven ist das Limit klein, auf Geraden gross.
        Grundlage ist die "Kruemmung": Wie stark aendert sich die Richtung
        der Strecke an diesem Punkt?
        """
        # Wie stark das Auto in Kurven abbremst:
        # gross = vorsichtiger (langsamer); klein = mutiger (schneller).
        curve_speed_factor = 4.0
        # Mindest-Zielgeschwindigkeit in engen Kurven (m/s):
        safe_corner_speed = 9.0

        limits = []
        for i in range(self.num_points):
            prev_p = self.waypoints[(i - 1) % self.num_points]
            curr_p = self.waypoints[i]
            next_p = self.waypoints[(i + 1) % self.num_points]

            # Richtung vor dem Punkt und nach dem Punkt
            dir_in = curr_p - prev_p
            dir_out = next_p - curr_p

            angle_in = math.atan2(dir_in[1], dir_in[0])
            angle_out = math.atan2(dir_out[1], dir_out[0])

            # Richtungsaenderung (Kruemmung), immer positiv, 0..pi
            turn = abs(self._normalize_angle(angle_out - angle_in))

            # Je groesser die Kruemmung, desto langsamer.
            limit = Physics.MAX_SPEED / (1.0 + curve_speed_factor * turn)
            limit = max(safe_corner_speed, limit)
            limits.append(limit)
        return np.array(limits)

    @staticmethod
    def _normalize_angle(angle):
        """Bringt einen Winkel in den Bereich -pi..pi."""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    # ------------------------------------------------------------------
    #  Fragen ueber die Position des Autos
    # ------------------------------------------------------------------
    def nearest_index(self, point):
        """Index des Waypoints, der 'point' am naechsten ist."""
        dx = self.waypoints[:, 0] - point[0]
        dy = self.waypoints[:, 1] - point[1]
        dist_squared = dx * dx + dy * dy
        return int(np.argmin(dist_squared))

    def lateral_offset(self, point):
        """Abstand des Autos von der Mittellinie (Ideallinie).

        Klein  = das Auto faehrt schoen mittig.
        Gross  = das Auto ist weit aussen -> evtl. Offtrack.
        """
        idx = self.nearest_index(point)
        nearest = self.waypoints[idx]
        dx = point[0] - nearest[0]
        dy = point[1] - nearest[1]
        return math.hypot(dx, dy)

    def is_off_track(self, point):
        """True, wenn das Auto die Fahrbahn verlassen hat."""
        return self.lateral_offset(point) > (self.width / 2.0)

    def is_collision(self, point):
        """True, wenn das Auto weit hinter die Bande geraten ist (Crash)."""
        # Ein bisschen Spielraum ueber den Rand hinaus = harte Kollision.
        return self.lateral_offset(point) > (self.width / 2.0 + self.width * 0.25)

    # ------------------------------------------------------------------
    #  Fuer den Controller: Zielpunkt und Zielgeschwindigkeit
    # ------------------------------------------------------------------
    def lookahead_point(self, point, distance):
        """Ein Zielpunkt auf der Mittellinie, ca. 'distance' Meter voraus.

        Der Pure-Pursuit-Controller lenkt immer auf diesen Punkt zu.
        """
        start = self.nearest_index(point)
        travelled = 0.0
        idx = start
        # Wir laufen die Waypoints entlang, bis wir weit genug voraus sind.
        for _ in range(self.num_points):
            nxt = (idx + 1) % self.num_points
            seg = self.waypoints[nxt] - self.waypoints[idx]
            seg_len = math.hypot(seg[0], seg[1])
            travelled += seg_len
            idx = nxt
            if travelled >= distance:
                break
        return self.waypoints[idx], idx

    def target_speed(self, point, brake_distance):
        """Erlaubte Geschwindigkeit unter Beruecksichtigung kommender Kurven.

        Wir schauen ein Stueck (brake_distance) nach vorne und nehmen das
        KLEINSTE Geschwindigkeits-Limit in diesem Bereich. So bremst das
        Auto rechtzeitig vor einer Kurve.
        """
        start = self.nearest_index(point)
        travelled = 0.0
        idx = start
        limit = self.speed_limits[idx]
        for _ in range(self.num_points):
            nxt = (idx + 1) % self.num_points
            seg = self.waypoints[nxt] - self.waypoints[idx]
            travelled += math.hypot(seg[0], seg[1])
            idx = nxt
            limit = min(limit, self.speed_limits[idx])
            if travelled >= brake_distance:
                break
        return limit

    def is_brake_zone(self, index):
        """True, wenn an diesem Waypoint langsamer als Vollspeed gefahren wird."""
        return self.speed_limits[index] < Physics.MAX_SPEED - 0.5

    # ------------------------------------------------------------------
    #  Startposition fuer das Auto
    # ------------------------------------------------------------------
    def start_pose(self):
        """Startposition (x, y) und Startrichtung (heading) fuer das Auto."""
        start = self.waypoints[0]
        nxt = self.waypoints[1 % self.num_points]
        heading = math.atan2(nxt[1] - start[1], nxt[0] - start[0])
        return start[0], start[1], heading
