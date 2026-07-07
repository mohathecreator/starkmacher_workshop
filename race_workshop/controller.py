"""
controller.py
=============

Aufgabe: Das "Gehirn" des autonomen Autos.

Der Controller schaut sich die Strecke und den Zustand des Autos an und
entscheidet in jedem Moment:
  - Lenkwinkel  (wohin lenken?)
  - Gas         (wie viel beschleunigen?)
  - Bremse      (wie stark bremsen?)

Er benutzt zwei bekannte Ideen aus dem echten autonomen Fahren:

  1) PURE PURSUIT (fuer die Lenkung)
     Das Auto sucht sich einen Zielpunkt ein Stueck vor sich auf der Strecke
     und lenkt genau dorthin - wie wenn man beim Autofahren nicht auf die
     Motorhaube schaut, sondern weiter nach vorne auf die Strasse.

  2) GESCHWINDIGKEITS-REGELUNG (fuer Gas & Bremse)
     Das Auto vergleicht seine aktuelle Geschwindigkeit mit der erlaubten
     Geschwindigkeit fuer die naechste Kurve und gibt Gas oder bremst.

Aufbau als Klasse mit einer Basisklasse (BaseController), damit man spaeter
einfach andere Controller (z.B. PID oder Reinforcement Learning) ergaenzen
kann, ohne den Rest des Programms zu aendern.

Hinweis: Die "Regler" fuer das Fahrverhalten sind mitten in der Methode
compute_controls() versteckt - lies den Code, um sie zu finden!
"""

import math

# Zwei feste Auto-Eigenschaften brauchen wir aus der Physik.
from physics import Physics


class BaseController:
    """Grundgeruest fuer jeden Controller.

    Ein Controller muss nur die Methode compute_controls() anbieten.
    So kann man spaeter verschiedene Controller austauschen.
    """

    def compute_controls(self, vehicle, track):
        """Muss (steering_angle, throttle, brake) zurueckgeben."""
        raise NotImplementedError

    # Der Controller merkt sich seinen zuletzt gewaehlten Zielpunkt,
    # damit die Visualisierung ihn anzeigen kann.
    target_point = None


class PurePursuitController(BaseController):
    """Der Standard-Controller des Workshops: Pure Pursuit + Tempo-Regelung."""

    def compute_controls(self, vehicle, track):
        # =============================================================
        #  TEIL 1: LENKUNG (Pure Pursuit)
        # =============================================================

        # 1a) Zielpunkt ein Stueck vor dem Auto suchen.
        #     Wie weit das Auto nach vorne "schaut" (m):
        #     klein = folgt der Linie eng, aber zittrig;
        #     gross = ruhiger, schneidet aber Kurven ab.
        lookahead_distance = 12.0

        car_pos = vehicle.position()
        target, target_index = track.lookahead_point(car_pos, lookahead_distance)
        self.target_point = target  # merken (fuer die Anzeige)

        # 1b) Richtung vom Auto zum Zielpunkt bestimmen.
        dx = target[0] - vehicle.x
        dy = target[1] - vehicle.y
        angle_to_target = math.atan2(dy, dx)

        # 1c) Wie stark weicht der Zielpunkt von der Blickrichtung ab?
        #     'alpha' ist der Winkel zwischen "wohin ich schaue" und
        #     "wohin ich fahren will".
        alpha = self._normalize_angle(angle_to_target - vehicle.heading)

        # 1d) Pure-Pursuit-Formel: aus dem Winkel alpha den Lenkwinkel
        #     berechnen. Je weiter der Zielpunkt, desto sanfter.
        steering = math.atan2(
            2.0 * Physics.WHEELBASE * math.sin(alpha), lookahead_distance
        )

        # 1e) Verstaerkung der Lenkung (1.0 = normal):
        #     groesser = aggressiver (kann schlingern);
        #     kleiner  = sanfter (kann Kurven verpassen).
        steering_gain = 1.0
        steering_deg = math.degrees(steering) * steering_gain

        # 1f) Lenkwinkel begrenzen (die Raeder koennen nicht beliebig einschlagen).
        limit = Physics.MAX_STEERING_ANGLE
        steering_deg = max(-limit, min(limit, steering_deg))

        # =============================================================
        #  TEIL 2: GAS & BREMSE (Geschwindigkeits-Regelung)
        # =============================================================

        # 2a) Wie weit das Auto vor einer Kurve nach vorne schaut, um
        #     rechtzeitig zu bremsen (m). Gross = frueher bremsen.
        brake_distance = 28.0

        # Welche Geschwindigkeit ist fuer die naechste Kurve erlaubt?
        desired_speed = track.target_speed(car_pos, brake_distance)

        # 2b) Vergleichen und entscheiden.
        throttle = 0.0
        brake = 0.0
        if vehicle.speed < desired_speed - 0.3:
            # Zu langsam -> Gas geben.
            throttle = 1.0
        elif vehicle.speed > desired_speed + 0.3:
            # Zu schnell -> bremsen. Je groesser der Ueberschuss, desto mehr.
            too_fast = vehicle.speed - desired_speed
            brake = min(1.0, too_fast / 5.0)
        else:
            # Passende Geschwindigkeit -> leicht Gas halten.
            throttle = 0.3

        return steering_deg, throttle, brake

    @staticmethod
    def _normalize_angle(angle):
        """Bringt einen Winkel in den Bereich -pi..pi."""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle
