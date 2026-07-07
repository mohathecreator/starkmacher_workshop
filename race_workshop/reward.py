"""
reward.py
=========

Aufgabe: Punkte und Statistik pro Runde.

Waehrend einer Runde sammelt der LapRecorder Daten:
  - Top-Speed (hoechste Geschwindigkeit)
  - Durchschnittsgeschwindigkeit
  - wie oft das Auto von der Strecke abkam (Offtrack)
  - wie oft es die Bande beruehrte (Kollision)

Am Ende einer Runde wird daraus ein Ergebnis (LapResult) mit einem
Gesamt-Score gemacht. Der Score belohnt schnelle, saubere Runden.

    Score = 1000 - Rundenzeit - Offtrack * 20 - Kollisionen * 100

Ziel der Teilnehmer: einen moeglichst hohen Score erreichen.
"""


class LapResult:
    """Das Ergebnis einer einzelnen Runde (nur Daten, keine Logik)."""

    def __init__(self, lap_number, lap_time, top_speed,
                 average_speed, offtrack_events, collisions):
        self.lap_number = lap_number
        self.lap_time = lap_time
        self.top_speed = top_speed
        self.average_speed = average_speed
        self.offtrack_events = offtrack_events
        self.collisions = collisions
        self.score = self._compute_score()

    def _compute_score(self):
        """Berechnet den Gesamt-Score der Runde."""
        score = 1000.0
        score -= self.lap_time            # schneller = besser
        score -= self.offtrack_events * 20   # sauber fahren lohnt sich
        score -= self.collisions * 100       # Crashs kosten viel
        return score

    def as_lines(self):
        """Gibt das Ergebnis als Liste von Textzeilen zurueck (zum Ausdrucken)."""
        return [
            f"Runde {self.lap_number}",
            f"  Lap Time      : {self.lap_time:6.2f} s",
            f"  Top Speed     : {self.top_speed:6.2f} m/s",
            f"  Average Speed : {self.average_speed:6.2f} m/s",
            f"  Offtrack      : {self.offtrack_events}",
            f"  Collisions    : {self.collisions}",
            f"  SCORE         : {self.score:6.1f}",
        ]


class LapRecorder:
    """Sammelt waehrend einer Runde die Statistik und erstellt das Ergebnis."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Setzt alle Zaehler auf Anfang (Start einer neuen Runde)."""
        self.time = 0.0
        self.top_speed = 0.0
        self.speed_sum = 0.0
        self.samples = 0
        self.offtrack_events = 0
        self.collisions = 0

    def update(self, dt, speed):
        """Wird in jedem Simulationsschritt aufgerufen."""
        self.time += dt
        self.speed_sum += speed
        self.samples += 1
        if speed > self.top_speed:
            self.top_speed = speed

    def add_offtrack(self):
        self.offtrack_events += 1

    def add_collision(self):
        self.collisions += 1

    def finish_lap(self, lap_number):
        """Erstellt aus den gesammelten Daten das Rundenergebnis."""
        average = self.speed_sum / self.samples if self.samples > 0 else 0.0
        return LapResult(
            lap_number=lap_number,
            lap_time=self.time,
            top_speed=self.top_speed,
            average_speed=average,
            offtrack_events=self.offtrack_events,
            collisions=self.collisions,
        )
