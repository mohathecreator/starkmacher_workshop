"""
physics.py
==========

Aufgabe: Die (bewusst einfache) Fahrphysik.

Die Klasse Physics bekommt den aktuellen Zustand des Autos und die
Steuerbefehle (Gas, Bremse, Lenkung) und rechnet aus, wo das Auto einen
kurzen Moment (dt) spaeter ist.

Wir benutzen ein einfaches "Fahrrad-Modell":
  - Das Auto hat eine Position, eine Blickrichtung und eine Geschwindigkeit.
  - Gas gibt Beschleunigung, Bremse und Reibung nehmen Geschwindigkeit weg.
  - Der Lenkwinkel bestimmt, wie schnell sich die Blickrichtung dreht.

Keine echte Physik, aber es fuehlt sich glaubwuerdig an.

--------------------------------------------------------------------------
HINWEIS FUER DEN WORKSHOP:
Die "Regler" fuer das Fahrverhalten sind absichtlich NICHT alle an einer
Stelle gesammelt, sondern stehen mitten im Code - genau dort, wo sie wirken.
Wer das Auto schneller machen will, muss den Code LESEN und VERSTEHEN, um die
richtige Stelle zu finden. Sucht nach Zahlen mit einem Kommentar daneben.
--------------------------------------------------------------------------
"""

import math


class Physics:
    """Berechnet die Bewegung des Autos Schritt fuer Schritt."""

    # Diese drei Eigenschaften des Autos werden an mehreren Stellen im
    # Programm gebraucht (nicht nur hier). Deshalb stehen sie oben bei der
    # Klasse - sie gehoeren zum Auto selbst.
    MAX_SPEED = 30.0            # Hoechstgeschwindigkeit auf Geraden (m/s) [TUNEN]
    WHEELBASE = 2.6            # Radstand (m): feste Bauart -> NICHT aendern
    MAX_STEERING_ANGLE = 35.0  # groesster Lenkeinschlag der Raeder (Grad) [TUNEN]

    def update(self, state, throttle, brake, steering_angle, dt):
        """Berechnet den neuen Zustand des Autos nach der Zeit dt.

        Parameter:
            state          : Objekt mit x, y, heading, speed (das Fahrzeug)
            throttle       : Gas,   Wert von 0 (kein Gas) bis 1 (Vollgas)
            brake          : Bremse, Wert von 0 (nicht) bis 1 (voll)
            steering_angle : Lenkwinkel in Grad (links positiv, rechts negativ)
            dt             : vergangene Zeit in Sekunden (z.B. 1/60)

        Diese Funktion veraendert 'state' direkt (Position, Winkel, Tempo).
        """

        # --- 1) Geschwindigkeit anpassen ---------------------------------
        # Wie stark das Auto bei Vollgas beschleunigt (m/s pro Sekunde):
        acceleration = 12.0
        # Wie stark das Auto bremsen kann (m/s pro Sekunde):
        brake_force = 25.0
        # Rollwiderstand: bremst das Auto immer leicht, wenn es kein Gas gibt:
        friction = 0.6

        # Beschleunigung durch Gas, minus Bremse, minus Reibung.
        accel = throttle * acceleration
        decel = brake * brake_force + friction
        state.speed = state.speed + accel * dt - decel * dt

        # Rueckwaerts fahren wollen wir nicht -> nie unter 0.
        if state.speed < 0.0:
            state.speed = 0.0
        # Nie schneller als die erlaubte Hoechstgeschwindigkeit.
        if state.speed > self.MAX_SPEED:
            state.speed = self.MAX_SPEED

        # --- 2) Blickrichtung (heading) drehen ---------------------------
        # Der Lenkwinkel wird in Radiant umgerechnet und begrenzt.
        max_angle = math.radians(self.MAX_STEERING_ANGLE)
        angle = math.radians(steering_angle)
        angle = max(-max_angle, min(max_angle, angle))

        # Fahrrad-Modell: Wie schnell sich das Auto dreht, haengt vom Tempo
        # und vom Radstand ab. Steht das Auto, dreht es sich nicht.
        turn_rate = (state.speed / self.WHEELBASE) * math.tan(angle)

        # Grip (Haftung) der Reifen: maximale Querbeschleunigung in Kurven
        # (m/s^2). Wer zu SCHNELL in eine Kurve faehrt, kann nicht scharf
        # genug lenken und rutscht nach aussen gegen die Begrenzung.
        # NICHT aendern: mehr Grip macht das Spiel zu einfach!
        tire_grip = 35.0
        if state.speed > 0.1:
            max_turn_rate = tire_grip / state.speed
            if turn_rate > max_turn_rate:
                turn_rate = max_turn_rate
            elif turn_rate < -max_turn_rate:
                turn_rate = -max_turn_rate

        state.heading += turn_rate * dt

        # --- 3) Position verschieben -------------------------------------
        # In Blickrichtung um (Geschwindigkeit * Zeit) weiterfahren.
        state.x += math.cos(state.heading) * state.speed * dt
        state.y += math.sin(state.heading) * state.speed * dt
