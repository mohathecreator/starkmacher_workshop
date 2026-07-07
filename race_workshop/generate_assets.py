"""
generate_assets.py
===================

Hilfs-Werkzeug (KEIN Teil der Simulation).

Dieses Skript erzeugt einmalig die Streckendaten (tracks/*.json) und das
Auto-Bild (assets/car.png). Es muss normalerweise nie ausgeführt werden -
die fertigen Dateien liegen dem Projekt bereits bei.

Falls eine Datei verloren geht, kann man sie hiermit neu erzeugen:

    python generate_assets.py

Die Teilnehmer des Workshops müssen dieses Skript NICHT anfassen.
"""

import json
import math
import os

import numpy as np


# ---------------------------------------------------------------------------
# 1) Streckenberechnung
# ---------------------------------------------------------------------------
#
# Eine Strecke besteht aus einer geschlossenen Linie durch die Mitte der
# Fahrbahn ("Waypoints"). Aus dieser Mittellinie berechnen wir automatisch
# den linken und den rechten Fahrbahnrand, indem wir die Mittellinie um die
# halbe Streckenbreite nach links bzw. rechts verschieben.


def catmull_rom(control_points, points_per_segment=20):
    """Legt eine weiche, geschlossene Kurve durch die gegebenen Kontrollpunkte.

    Catmull-Rom ist eine einfache Methode, um aus wenigen Stützpunkten eine
    runde Linie zu machen (so entstehen die Kurven der Rennstrecke).
    """
    pts = np.array(control_points, dtype=float)
    n = len(pts)
    curve = []
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n]
        for t in np.linspace(0.0, 1.0, points_per_segment, endpoint=False):
            t2 = t * t
            t3 = t2 * t
            # Standard Catmull-Rom Formel
            point = 0.5 * (
                (2 * p1)
                + (-p0 + p2) * t
                + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
            )
            curve.append(point)
    return np.array(curve)


def resample_even(points, spacing=4.0):
    """Verteilt die Punkte gleichmaessig entlang der Linie (Abstand = spacing)."""
    pts = np.array(points, dtype=float)
    # Abstaende zwischen aufeinanderfolgenden Punkten (Ring geschlossen)
    diffs = np.roll(pts, -1, axis=0) - pts
    seg_len = np.hypot(diffs[:, 0], diffs[:, 1])
    total = seg_len.sum()
    n = max(8, int(round(total / spacing)))
    # kumulative Bogenlaenge
    cum = np.concatenate([[0.0], np.cumsum(seg_len)])
    targets = np.linspace(0.0, total, n, endpoint=False)
    out = []
    for d in targets:
        idx = np.searchsorted(cum, d) - 1
        idx = max(0, min(idx, len(pts) - 1))
        local = (d - cum[idx]) / max(seg_len[idx], 1e-9)
        p = pts[idx] + local * (pts[(idx + 1) % len(pts)] - pts[idx])
        out.append(p)
    return np.array(out)


def build_boundaries(center, width):
    """Erzeugt linken und rechten Rand aus Mittellinie + Streckenbreite."""
    n = len(center)
    left, right = [], []
    half = width / 2.0
    for i in range(n):
        # Fahrtrichtung an diesem Punkt (Vektor zum naechsten Punkt)
        nxt = center[(i + 1) % n]
        prv = center[(i - 1) % n]
        tangent = nxt - prv
        length = math.hypot(tangent[0], tangent[1])
        if length < 1e-9:
            length = 1e-9
        tx, ty = tangent[0] / length, tangent[1] / length
        # Normale (90 Grad gedreht) zeigt nach links
        nx, ny = -ty, tx
        left.append([center[i][0] + nx * half, center[i][1] + ny * half])
        right.append([center[i][0] - nx * half, center[i][1] - ny * half])
    return left, right


def save_track(filename, name, control_points, width, spacing=4.0):
    center = catmull_rom(control_points, points_per_segment=24)
    center = resample_even(center, spacing=spacing)
    left, right = build_boundaries(center, width)

    # Start-/Ziellinie quer zur Fahrbahn beim ersten Waypoint
    start_line = {"left": left[0], "right": right[0]}

    data = {
        "name": name,
        "track_width": width,
        "waypoints": [[float(x), float(y)] for x, y in center],
        "left_boundary": [[float(x), float(y)] for x, y in left],
        "right_boundary": [[float(x), float(y)] for x, y in right],
        "start_line": {
            "left": [float(start_line["left"][0]), float(start_line["left"][1])],
            "right": [float(start_line["right"][0]), float(start_line["right"][1])],
        },
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  {filename}: {len(center)} Waypoints geschrieben.")


def make_tracks():
    here = os.path.dirname(os.path.abspath(__file__))
    tracks_dir = os.path.join(here, "tracks")
    os.makedirs(tracks_dir, exist_ok=True)

    # --- Trainingsstrecke: einfaches, weiches Oval -----------------------
    training = [
        (30, 60), (60, 30), (140, 30), (170, 60),
        (170, 120), (140, 150), (60, 150), (30, 120),
    ]
    save_track(
        os.path.join(tracks_dir, "training_track.json"),
        "Training Track", training, width=14.0, spacing=4.0,
    )

    # --- Rennstrecke: anspruchsvoller Rundkurs mit mehreren Kurven -------
    race = [
        (40, 40), (120, 25), (200, 40), (230, 100),
        (200, 130), (150, 120), (130, 160), (180, 200),
        (150, 250), (80, 250), (40, 210), (70, 160),
        (40, 120), (25, 80),
    ]
    save_track(
        os.path.join(tracks_dir, "race_track.json"),
        "Race Track", race, width=12.0, spacing=4.0,
    )


# ---------------------------------------------------------------------------
# 2) Auto-Bild erzeugen
# ---------------------------------------------------------------------------
#
# Wir zeichnen ein einfaches Auto von oben (Draufsicht) und speichern es als
# PNG. Das Bild zeigt nach rechts (+X), weil die Simulation den Winkel 0 als
# "nach rechts" interpretiert.


def make_car_png():
    # pygame ohne echtes Fenster starten (nur zum Zeichnen ins Bild)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame

    pygame.init()
    w, h = 64, 32
    surface = pygame.Surface((w, h), pygame.SRCALPHA)

    body = (200, 30, 40)      # rote Karosserie
    dark = (30, 30, 40)       # Reifen / Scheiben
    glass = (120, 200, 230)   # Frontscheibe

    # Reifen (dunkle Rechtecke an den Ecken)
    for cx in (12, 50):
        for cy in (3, h - 9):
            pygame.draw.rect(surface, dark, (cx - 4, cy, 12, 6), border_radius=2)

    # Karosserie
    pygame.draw.rect(surface, body, (6, 6, w - 12, h - 12), border_radius=6)
    # Frontfluegel / Nase vorne (rechts)
    pygame.draw.rect(surface, dark, (w - 10, 8, 6, h - 16), border_radius=2)
    # Cockpit / Scheibe
    pygame.draw.rect(surface, glass, (26, 10, 16, h - 20), border_radius=3)

    here = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(here, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    out = os.path.join(assets_dir, "car.png")
    pygame.image.save(surface, out)
    pygame.quit()
    print(f"  {out} geschrieben.")


if __name__ == "__main__":
    print("Erzeuge Streckendaten...")
    make_tracks()
    print("Erzeuge Auto-Bild...")
    make_car_png()
    print("Fertig.")
