# Formula Student Workshop – Autonomes Fahren

Ein Mini-Rennsimulator, mit dem Jugendliche (14–18) spielerisch lernen, wie
**Software das Fahrverhalten eines autonomen Rennwagens** beeinflusst.

Ihr programmiert **keinen** Algorithmus. Das Auto fährt schon von allein.
Eure Aufgabe: das Auto durch **Einstellen von Werten im Code** so schnell wie
möglich machen – ohne von der Strecke zu fliegen. Dabei lernt ihr ganz
nebenbei, **im Code zu lesen** und selbst zu finden, wo etwas eingestellt wird.

---

## Installation

Benötigt Python 3 sowie `pygame` und `numpy`.

```bash
pip install pygame numpy
```

> **Hinweis für Python 3.14:** Für pygame gibt es dort noch kein fertiges
> Paket. Nutzt stattdessen den kompatiblen Ersatz `pygame-ce`
> (gleicher Import `import pygame`):
>
> ```bash
> pip install pygame-ce numpy
> ```

---

## Starten

```bash
python main.py
```

Es erscheint das Startmenü (**Challenge Mode**):

```
==========================
   Formula Student Workshop
==========================
   [1] Training Track
   [2] Race Track
```

- Taste **1** oder **2** wählt die Strecke.
- Das Auto fährt automatisch. Am Ende jeder Runde wird die **Rundenzeit
  groß angezeigt**.
- **ESC** = zurück zum Menü, Fenster schließen = beenden.

---

## So optimiert ihr das Auto

Die Einstell-Werte sind **absichtlich im Code versteckt** – mitten in den
Methoden, dort wo sie wirken. Es gibt **keine** Datei mit einer fertigen
Werte-Liste. Ihr müsst den Code **lesen und verstehen**, um die richtige
Zahl zu finden. Sucht nach **Zahlen mit einem Kommentar daneben** (z.B.
`acceleration = 12.0  # Wie stark das Auto beschleunigt`).

Vorgehen:

1. Überlegt, *was* ihr ändern wollt (z.B. „schneller in Kurven").
2. Öffnet die passende Datei/Methode (siehe Tabelle) und **lest den Code**,
   bis ihr die passende Zahl gefunden habt.
3. Ändert **einen** Wert.
4. Startet neu: `python main.py`.
5. Vergleicht die Rundenzeit und den **Score**.
6. Wiederholt das, bis das Auto möglichst schnell **und sauber** fährt.

### Wo finde ich was? (Fundstellen im Code 🔎)

Jeder Parameter steht dort, wo er im Programm wirkt. Die Zeilennummern sind
Anhaltspunkte – wenn sich der Code ändert, können sie leicht verrutschen.
Sucht dann nach dem **Variablennamen** in der genannten Datei/Methode.

#### ✅ Diese Parameter SOLLT ihr verändern (das ist eure Aufgabe)

Das sind eure „Regler", um schneller zu werden. Spielt damit!

| Was will ich ändern? | Datei | Variable | Zeile | Methode / Ort |
|---|---|---|---|---|
| Höchstgeschwindigkeit (Geraden) | `physics.py` | `MAX_SPEED` | 36 | Klasse `Physics` (oben) |
| Maximaler Lenkeinschlag | `physics.py` | `MAX_STEERING_ANGLE` | 38 | Klasse `Physics` (oben) |
| Beschleunigung (Gas) | `physics.py` | `acceleration` | 55 | `Physics.update()` |
| Bremskraft | `physics.py` | `brake_force` | 57 | `Physics.update()` |
| Reibung / Ausrollen | `physics.py` | `friction` | 59 | `Physics.update()` |
| Wie weit vorausgeschaut wird | `controller.py` | `lookahead_distance` | 66 | `compute_controls()` |
| Wie aggressiv gelenkt wird | `controller.py` | `steering_gain` | 91 | `compute_controls()` |
| Wie früh vor Kurven gebremst wird | `controller.py` | `brake_distance` | 104 | `compute_controls()` |
| Wie stark in Kurven gebremst wird | `track.py` | `curve_speed_factor` | 69 | `_compute_speed_limits()` |
| Mindesttempo in Kurven | `track.py` | `safe_corner_speed` | 71 | `_compute_speed_limits()` |

#### ⛔ Diese Parameter besser NICHT verändern

Das sind feste Eigenschaften des Autos und der Simulation. Ändert man sie,
wird das Rennen unrealistisch oder zu einfach (Spaß-Killer!).

| Wert | Datei | Variable | Zeile | Warum nicht ändern? |
|---|---|---|---|---|
| Reifen-Grip | `physics.py` | `tire_grip` | 87 | Mehr Grip = man kann beliebig schnell durch Kurven → keine Herausforderung mehr |
| Radstand | `physics.py` | `WHEELBASE` | 37 | Feste Bauart des Autos |
| Auto-Länge / -Breite | `vehicle.py` | `self.length` / `self.width` | 38 / 39 | Feste Bauart des Autos |
| Anzahl der Runden | `simulator.py` | `TOTAL_LAPS` | 26 | Regel des Rennens |
| Bilder pro Sekunde | `main.py` | `FPS` | 38 | Technische Einstellung |
| Fenster & Farben | `visualization.py` | (oben in der Datei) | — | Nur die Optik |

> **Tipp:** Immer nur **einen** Wert aus der grünen Liste ändern und schauen,
> was passiert. So versteht ihr, was jeder Regler bewirkt – und lernt ganz
> nebenbei, Code zu lesen.

### Achtung: Begrenzung berühren = sofort vorbei! 🚧

Sobald das Auto die **Streckenbegrenzung berührt**, ist der Lauf sofort zu
Ende (**CRASH!**). Dann geht es zurück ins Menü – Werte anpassen und neu
versuchen. Ziel ist also: schnell fahren, aber **immer auf der Strecke bleiben**.

> **Merke:** Die Reifen (`TIRE_GRIP`) haben nur begrenzten Grip. Zu schnell in
> die Kurve = das Auto rutscht nach außen gegen die Begrenzung = CRASH. Genau
> deshalb lohnt sich vorausschauendes Bremsen.

### Der Score

Für jede **sauber beendete Runde** gibt es einen Score:

```
Score = 1000  −  Rundenzeit  −  Offtrack × 20  −  Kollisionen × 100
```

Je schneller die Runde, desto höher der Score. Der Trick ist die **richtige
Balance**: In Kurven rechtzeitig bremsen, auf Geraden Vollgas.

---

## Projektstruktur

```
race_workshop/
    main.py            Start + Menü (Challenge Mode)
    physics.py         Fahrphysik: Motor, Bremse, Reifen, Lenkung
    controller.py      "Gehirn" des Autos (Pure Pursuit + Tempo-Regelung)
    track.py           Strecke: Waypoints, Ränder, Kurven-Tempolimits
    vehicle.py         Das Fahrzeug (Zustand + Abmessungen)
    simulator.py       Spielleiter: hält alles zusammen, zählt Runden
    visualization.py   Grafik mit pygame (Fenster, Farben, Anzeige)
    reward.py          Rundenstatistik + Score-Berechnung
    generate_assets.py Werkzeug: erzeugt Strecken + Auto-Bild (einmalig)

    tracks/
        training_track.json    einfaches Oval (zum Üben)
        race_track.json        anspruchsvoller Rundkurs
    assets/
        car.png                Auto von oben
```

> Es gibt **bewusst keine zentrale `config.py`**. Die Fahr-Werte sind über die
> Klassen und Methoden verteilt, dort wo sie wirken – so lernt ihr, Code zu
> lesen und zu verstehen, statt nur an einer Liste zu drehen.

---

## Eigene Strecke als PNG verwenden (optional)

Habt ihr eine **vorgezeichnete Strecke als PNG**, könnt ihr sie als
Hintergrund einblenden:

1. Legt das Bild neben die Streckendatei, gleicher Name, z.B.
   `tracks/race_track.png`.
2. Setzt in `visualization.py`: `USE_TRACK_IMAGE = True`.

> Damit das Auto korrekt fährt, müssen die **Waypoints in der JSON zum Bild
> passen**. Das Bild ist nur die Optik – gefahren wird nach den Waypoints.

---

## Ausbaumöglichkeiten (für später)

Der Code ist so aufgebaut, dass sich leicht ergänzen lässt:

- **Neue Controller** (z.B. PID, Stanley, Reinforcement Learning):
  von `BaseController` in `controller.py` erben.
- **Andere Fahrzeuge/Reifen:** Werte in `physics.py` (z.B. `TIRE_GRIP`).
- **Neue Strecken:** JSON-Datei in `tracks/` ablegen (siehe
  `generate_assets.py`).
- **Regenmodus:** z.B. `TIRE_GRIP` und `FRICTION` verkleinern.
