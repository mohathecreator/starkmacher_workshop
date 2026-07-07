"""
vehicle.py
==========

Aufgabe: Das Fahrzeug selbst.

Die Klasse Vehicle speichert den Zustand des Autos:
  - Position (x, y)
  - Blickrichtung (heading, in Radiant)
  - Geschwindigkeit (speed, in m/s)
  - aktueller Lenkwinkel (steering_angle, in Grad)

Das Auto weiss selbst NICHT, wie es faehrt - das entscheidet der Controller.
Das Auto weiss auch NICHT, wie sich Bewegung berechnet - das macht die Physik.
Es haelt nur seinen Zustand und bietet ein paar Hilfsfunktionen an
(z.B. die Ecken der Karosserie fuer die Kollisionspruefung).

So ist spaeter leicht ein zweites Fahrzeug mit anderen Werten moeglich.
"""

import math

from physics import Physics


class Vehicle:
    """Ein Rennwagen mit Position, Richtung und Geschwindigkeit."""

    def __init__(self, x, y, heading):
        # Zustand
        self.x = x
        self.y = y
        self.heading = heading      # Blickrichtung in Radiant (0 = nach rechts)
        self.speed = 0.0            # Startgeschwindigkeit
        self.steering_angle = 0.0   # aktueller Lenkwinkel in Grad

        # Abmessungen des Autos in Metern (fuer Anzeige und Kollision).
        self.length = 4.2
        self.width = 2.0

        # Die Physik-Engine, die die Bewegung berechnet.
        self.physics = Physics()

    def apply_controls(self, throttle, brake, steering_angle, dt):
        """Wendet die Steuerbefehle des Controllers fuer einen Zeitschritt an."""
        self.steering_angle = steering_angle
        self.physics.update(self, throttle, brake, steering_angle, dt)

    def position(self):
        """Gibt die aktuelle Position als (x, y) zurueck."""
        return (self.x, self.y)

    def corners(self):
        """Berechnet die vier Ecken der Karosserie (fuer Kollisionen).

        Wir brauchen die Ecken, um zu pruefen, ob das Auto eine Bande
        beruehrt. Wir drehen ein Rechteck (Laenge x Breite) in Blickrichtung.
        """
        half_len = self.length / 2.0
        half_wid = self.width / 2.0
        cos_a = math.cos(self.heading)
        sin_a = math.sin(self.heading)

        # Ecken relativ zur Fahrzeugmitte (vorne/hinten, links/rechts)
        local = [
            (half_len, half_wid),
            (half_len, -half_wid),
            (-half_len, -half_wid),
            (-half_len, half_wid),
        ]
        result = []
        for lx, ly in local:
            wx = self.x + lx * cos_a - ly * sin_a
            wy = self.y + lx * sin_a + ly * cos_a
            result.append((wx, wy))
        return result
