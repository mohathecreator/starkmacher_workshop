"""
simulator.py
============

Aufgabe: Der "Spielleiter", der alles zusammenhaelt.

Der Simulator verbindet die einzelnen Teile:
  Vehicle (Auto)  +  Track (Strecke)  +  Controller (Gehirn)  +  LapRecorder

In jedem Zeitschritt (step) macht der Simulator:
  1. Den Controller fragen: Lenkung, Gas, Bremse?
  2. Das Auto mit diesen Befehlen bewegen (Physik).
  3. Pruefen: Ist das Auto von der Strecke ab? Crash?
  4. Statistik mitschreiben.
  5. Pruefen: Wurde eine Runde beendet?

Der Simulator kennt KEINE Grafik. Er rechnet nur. Die Anzeige uebernimmt
die Datei visualization.py. So bleibt Rechnen und Zeichnen sauber getrennt.
"""

from vehicle import Vehicle
from reward import LapRecorder


# Wie viele Runden ein Lauf hat.
TOTAL_LAPS = 3


class Simulator:
    """Fuehrt die Simulation eines Laufs (mehrere Runden) durch."""

    def __init__(self, track, controller):
        self.track = track
        self.controller = controller

        # Auto an die Startposition der Strecke setzen.
        start_x, start_y, heading = track.start_pose()
        self.vehicle = Vehicle(start_x, start_y, heading)

        # Statistik-Rekorder fuer die aktuelle Runde.
        self.recorder = LapRecorder()

        # Rundenzaehler und Zeiten.
        self.current_lap = 1
        self.total_laps = TOTAL_LAPS
        self.best_lap_time = None
        self.lap_results = []       # Liste aller fertigen Runden (LapResult)
        self.finished = False       # True, wenn der Lauf zu Ende ist
        self.crashed = False        # True, wenn das Auto die Begrenzung beruehrt hat

        # Fortschritt entlang der Strecke (fuer die Rundenerkennung).
        self._passed_midpoint = False
        self._last_index = 0

        # Spur (Trail) hinter dem Auto, nur fuer die Anzeige.
        self.trail = []

        # Letzte Steuerbefehle merken (fuer die Anzeige, z.B. Bremse).
        self.last_throttle = 0.0
        self.last_brake = 0.0

    # ------------------------------------------------------------------
    #  Ein Simulationsschritt
    # ------------------------------------------------------------------
    def step(self, dt):
        """Bewegt die Simulation um die Zeit dt weiter."""
        if self.finished:
            return

        # 1) Controller entscheiden lassen.
        steering, throttle, brake = self.controller.compute_controls(
            self.vehicle, self.track
        )
        self.last_throttle = throttle
        self.last_brake = brake

        # 2) Auto bewegen (Reihenfolge: Gas, Bremse, Lenkung, Zeit).
        self.vehicle.apply_controls(throttle, brake, steering, dt)

        # 3) Statistik mitschreiben.
        self.recorder.update(dt, self.vehicle.speed)

        # 4) Spur aktualisieren (nur die letzten Punkte behalten).
        self.trail.append(self.vehicle.position())
        if len(self.trail) > 200:
            self.trail.pop(0)

        # 5) Crash pruefen: Beruehrt das Auto die Begrenzung, ist der Lauf
        #    sofort vorbei. Danach nicht mehr weiterrechnen.
        self._check_crash()
        if self.finished:
            return

        # 6) Rundenerkennung.
        self._check_lap_completed()

    # ------------------------------------------------------------------
    #  Crash: Begrenzung beruehrt -> Lauf beenden
    # ------------------------------------------------------------------
    def _check_crash(self):
        """Beendet den Lauf, sobald eine Ecke des Autos die Begrenzung beruehrt.

        Wir pruefen alle vier Ecken der Karosserie. Liegt eine davon weiter
        aussen als der Fahrbahnrand (halbe Streckenbreite von der Mitte),
        hat das Auto die Begrenzung beruehrt.
        """
        for corner in self.vehicle.corners():
            if self.track.is_off_track(corner):
                self.crashed = True
                self.finished = True
                self.vehicle.speed = 0.0  # Auto steht nach dem Crash
                print("=" * 40)
                print(f"CRASH! Das Auto hat die Begrenzung beruehrt "
                      f"(Runde {self.current_lap}).")
                print("Lauf beendet.")
                return

    # ------------------------------------------------------------------
    #  Rundenerkennung
    # ------------------------------------------------------------------
    def _check_lap_completed(self):
        """Erkennt, wann das Auto die Start-/Ziellinie ueberquert.

        Idee: Wir merken uns den naechstgelegenen Waypoint (Index). Eine
        Runde ist komplett, wenn das Auto erst die zweite Streckenhaelfte
        erreicht hat (_passed_midpoint) und dann wieder ganz am Anfang
        (kleiner Index) ankommt.
        """
        index = self.track.nearest_index(self.vehicle.position())
        n = self.track.num_points

        # Zweite Streckenhaelfte erreicht?
        if index > n * 0.5:
            self._passed_midpoint = True

        # Zurueck am Anfang, nachdem die Haelfte passiert wurde -> Runde fertig.
        if self._passed_midpoint and index < n * 0.1:
            self._complete_lap()

        self._last_index = index

    def _complete_lap(self):
        """Schliesst die aktuelle Runde ab und startet die naechste."""
        result = self.recorder.finish_lap(self.current_lap)
        self.lap_results.append(result)

        # Beste Rundenzeit aktualisieren.
        if self.best_lap_time is None or result.lap_time < self.best_lap_time:
            self.best_lap_time = result.lap_time

        # Ergebnis auf der Konsole ausgeben.
        print("-" * 40)
        for line in result.as_lines():
            print(line)

        # Naechste Runde vorbereiten oder Lauf beenden.
        if self.current_lap >= self.total_laps:
            self.finished = True
            print("=" * 40)
            print("Lauf beendet! Alle Runden gefahren.")
        else:
            self.current_lap += 1
            self.recorder.reset()
            self._passed_midpoint = False

    # ------------------------------------------------------------------
    #  Hilfen fuer die Anzeige
    # ------------------------------------------------------------------
    def current_lap_time(self):
        """Zeit der laufenden Runde in Sekunden."""
        return self.recorder.time

    def just_finished_result(self):
        """Das zuletzt beendete Rundenergebnis (oder None)."""
        return self.lap_results[-1] if self.lap_results else None
