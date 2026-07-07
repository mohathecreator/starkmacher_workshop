"""
main.py
=======

Aufgabe: Startpunkt des Programms ("Challenge Mode").

Ablauf:
  1. Ein Startmenue erscheint und fragt nach der Strecke:
        [1] Training Track
        [2] Race Track
  2. Danach startet die Simulation in Echtzeit.
  3. Am Ende jeder Runde wird die Rundenzeit gross angezeigt.
  4. Nach allen Runden erscheint eine Zusammenfassung.

Starten mit:   python main.py

Zum Optimieren: py aendern, dann neu starten.
"""

import os
import sys

import pygame

from track import Track
from controller import PurePursuitController
from simulator import Simulator
from visualization import (
    Visualization,
    WINDOW_WIDTH,
    COLOR_BACKGROUND,
    COLOR_TEXT,
    COLOR_START_LINE,
)


# Bilder pro Sekunde (feste Zeitschritte fuer stabile Physik).
FPS = 60


# Pfade zu den Streckendateien.
HERE = os.path.dirname(os.path.abspath(__file__))
TRACK_FILES = [
    os.path.join(HERE, "tracks", "training_track.json"),  # Auswahl 0 -> [1]
    os.path.join(HERE, "tracks", "race_track.json"),       # Auswahl 1 -> [2]
]


def run_menu(viz):
    """Zeigt das Startmenue und gibt die gewaehlte Strecken-Nummer zurueck.

    Rueckgabe: 0 (Training), 1 (Race) oder None (Fenster geschlossen).
    """
    selected = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,):
                    return None
                if event.key in (pygame.K_UP, pygame.K_LEFT):
                    selected = (selected - 1) % 2
                if event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                    selected = (selected + 1) % 2
                if event.key == pygame.K_1:
                    return 0
                if event.key == pygame.K_2:
                    return 1
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    return selected
        viz.draw_menu(selected)


def run_race(viz, track_file):
    """Fuehrt einen kompletten Lauf (mehrere Runden) auf einer Strecke durch."""
    track = Track(track_file)
    controller = PurePursuitController()
    sim = Simulator(track, controller)

    viz.set_track(track)

    clock = pygame.time.Clock()
    dt = 1.0 / FPS   # fester Zeitschritt fuer stabile Physik

    # Steuerung der grossen Rundenzeit-Anzeige.
    big_lap_result = None
    big_lap_timer = 0.0
    shown_laps = 0

    running = True
    while running:
        # --- Eingaben verarbeiten ---------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # Programm ganz beenden
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return True   # zurueck zum Menue

        # --- Simulation weiterrechnen -----------------------------------
        # Waehrend die grosse Rundenzeit angezeigt wird, pausieren wir kurz,
        # damit man die Zeit in Ruhe lesen kann.
        if big_lap_timer > 0.0:
            big_lap_timer -= dt
            if big_lap_timer <= 0.0:
                big_lap_result = None
        else:
            if not sim.finished:
                sim.step(dt)

            # Wurde gerade eine neue Runde beendet?
            if len(sim.lap_results) > shown_laps:
                shown_laps = len(sim.lap_results)
                big_lap_result = sim.just_finished_result()
                big_lap_timer = 2.5  # Sekunden anzeigen

        # --- Zeichnen ---------------------------------------------------
        viz.draw_frame(sim, big_lap_result)

        # --- Crash: Auto hat die Begrenzung beruehrt -> Game Over --------
        if sim.crashed:
            return show_crash(viz, sim)

        # --- Nach dem letzten Lauf: Zusammenfassung, dann warten ---------
        if sim.finished and big_lap_timer <= 0.0:
            wait = show_summary(viz, sim)
            return wait  # True = zurueck zum Menue, False = beenden

        clock.tick(FPS)  # auf Echtzeit begrenzen

    return True


def show_crash(viz, sim):
    """Zeigt den Crash-Bildschirm. Wartet auf Tastendruck.

    Rueckgabe: True (zurueck zum Menue) oder False (Programm beenden).
    """
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                return True  # beliebige Taste -> zurueck zum Menue

        viz.draw_frame(sim, crashed=True)


def show_summary(viz, sim):
    """Zeigt am Ende die Ergebnisse aller Runden. Wartet auf Tastendruck."""
    print("=" * 40)
    print("ZUSAMMENFASSUNG")
    best = min(r.lap_time for r in sim.lap_results) if sim.lap_results else 0.0
    total_score = sum(r.score for r in sim.lap_results)
    for r in sim.lap_results:
        print(f"  Runde {r.lap_number}: {r.lap_time:6.2f} s   Score {r.score:6.1f}")
    print(f"  Beste Runde: {best:.2f} s   Gesamt-Score: {total_score:.0f}")
    print("=" * 40)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                return True  # beliebige Taste -> zurueck zum Menue

        # Ergebnisbildschirm anzeigen.
        viz.screen.fill(COLOR_BACKGROUND)
        cx = WINDOW_WIDTH // 2
        title = viz.font_title.render("Ergebnis", True, COLOR_TEXT)
        viz.screen.blit(title, (cx - title.get_width() // 2, 80))

        y = 180
        for r in sim.lap_results:
            text = f"Runde {r.lap_number}:  {r.lap_time:6.2f} s   Score {r.score:6.0f}"
            label = viz.font_medium.render(text, True, COLOR_TEXT)
            viz.screen.blit(label, (cx - label.get_width() // 2, y))
            y += 50

        best_label = viz.font_medium.render(
            f"Beste Runde: {best:.2f} s", True, COLOR_START_LINE
        )
        viz.screen.blit(best_label, (cx - best_label.get_width() // 2, y + 20))

        hint = viz.font_small.render(
            "Taste druecken fuer Menue  -  ESC zum Beenden",
            True, (170, 180, 190),
        )
        viz.screen.blit(hint, (cx - hint.get_width() // 2, y + 90))
        pygame.display.flip()


def main():
    viz = Visualization()
    try:
        while True:
            choice = run_menu(viz)
            if choice is None:
                break  # Fenster geschlossen
            back_to_menu = run_race(viz, TRACK_FILES[choice])
            if not back_to_menu:
                break  # Programm beenden
    finally:
        viz.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
