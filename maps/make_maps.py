"""Regenerate every map and the comparison chart from data/travel_times.csv.

Usage (from the repository root):   python maps/make_maps.py            # all eras
                                     python maps/make_maps.py 1914 today # selected eras
Outputs go to maps/output/. Requires numpy and matplotlib.
"""

import csv
import json
import os
import sys
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

import render

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(ROOT, "data", "known_world.json"), encoding="utf-8") as reach_file:
    REACH = json.load(reach_file)


def load():
    """Read the travel times, grouped by era."""
    eras = defaultdict(list)
    with open(os.path.join(ROOT, "data", "travel_times.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            eras[r["era"]].append(
                (
                    r["place"],
                    float(r["lon"]),
                    float(r["lat"]),
                    float(r["hours_from_paris"]),
                    "S" if r["basis"] == "sourced" else "E",
                )
            )
    return eras


# Per-era label placements. Eras deliberately repeat the same cities at the same
# offsets, which the copy-paste detector would otherwise report.
# jscpd:ignore-start
MOD_EU = [
    ("Paris", -7, 8),
    ("London", -7, 0),
    ("Brussels", 7, 4),
    ("Lyon", 7, 0),
    ("Marseille", 7, -6),
    ("Bordeaux", -7, 0),
    ("Madrid", 7, 0),
    ("Rome", 7, 4),
    ("Vienna", 7, 0),
    ("Berlin", 7, 0),
    ("Moscow", 7, 0),
    ("Istanbul", -7, -9),
    ("Stockholm", 7, 0),
]
MOD_W = [
    ("Paris", 6, 6),
    ("New York", 6, 0),
    ("Los Angeles", -6, 0),
    ("Rio de Janeiro", 6, 0),
    ("Johannesburg", 6, 0),
    ("Cairo", -6, -6),
    ("Bombay", -6, 0),
    ("Hong Kong", 6, -4),
    ("Tokyo", 6, 0),
    ("Sydney", 6, 0),
]
ROAD = "roads, rivers and ports"
MODERN = "airports, railways and roads"

# era: (europe title, europe subtitle, world title, world subtitle,
#       europe labels, world labels, render options)
ERAS = {
    "roman": (
        "Europe from Lutetia, c. AD 200",
        "Fastest journey from Roman Paris by road, river and summer sailing ship",
        "The world from Lutetia, c. AD 200",
        ("Fastest journey from Roman Paris; grey lands lay beyond regular travel from the Roman world"),
        [
            ("Lutetia", 7, 0),
            ("Londinium", -7, 0),
            ("Colonia Agrippina", 7, 0),
            ("Burdigala", -7, 0),
            ("Lugdunum", 7, 0),
            ("Roma", 7, 4),
            ("Carthago", 7, 0),
            ("Tarraco", 7, -4),
            ("Byzantium", -7, -9),
            ("Athenae", 7, 0),
            ("Vindobona", 7, 0),
            ("Emerita Augusta", 7, 0),
            ("Aquileia", 7, 4),
        ],
        [
            ("Lutetia", 6, -8),
            ("Roma", 6, -6),
            ("Alexandria", -6, -6),
            ("Byzantium", 6, 5),
            ("Muziris", 6, 0),
            ("Rhapta", 6, 0),
            ("Taxila", 6, 6),
            ("Londinium", -6, 8),
        ],
        {"v_max": 50 / 24, "off_kmd": 30, "reach": "roman", "beyond": ROAD},
    ),
    "medieval": (
        "Europe from Paris, c. 1300",
        "Fastest journey from Paris on horseback, by river and by ship",
        "The world from Paris, c. 1300",
        ("Fastest journey from Paris in the age of the Mongol empire; grey lands lay beyond regular travel"),
        [
            ("Paris", -7, 8),
            ("London", -7, -4),
            ("Bruges", 7, 4),
            ("Troyes", 7, -7),
            ("Avignon", -7, 0),
            ("Barcelona", 7, -4),
            ("Santiago", 7, 0),
            ("Rome", 7, 4),
            ("Venice", 7, 4),
            ("Lubeck", 7, 0),
            ("Constantinople", -7, -9),
            ("Vienna", 7, 0),
            ("Cologne", 7, 0),
        ],
        [
            ("Paris", 6, 6),
            ("Rome", 6, -6),
            ("Cairo", -6, -6),
            ("Tabriz", 6, -8),
            ("Samarkand", 6, 9),
            ("Khanbaliq", 6, 0),
            ("Calicut", 6, 0),
            ("Timbuktu", -6, 0),
            ("Kilwa", 6, 0),
        ],
        {"v_max": 50 / 24, "off_kmd": 35, "reach": "medieval", "beyond": ROAD},
    ),
    "1800": (
        "Europe from Paris, c. 1800",
        "Fastest public journey from Paris by diligence, mail coach and sailing ship",
        "The world from Paris, c. 1800",
        "Fastest public journey from Paris in the last age of sail",
        [
            ("Paris", -7, 8),
            ("London", -7, 0),
            ("Lille", 7, 4),
            ("Lyon", 7, 0),
            ("Bordeaux", -7, 0),
            ("Marseille", 7, -6),
            ("Madrid", 7, 0),
            ("Rome", 7, 4),
            ("Vienna", 7, 0),
            ("Berlin", 7, 0),
            ("St Petersburg", 7, 0),
            ("Constantinople", -7, -9),
            ("Amsterdam", 7, 4),
        ],
        [
            ("Paris", 6, 6),
            ("Cairo", -6, -6),
            ("New York", 6, 0),
            ("Rio de Janeiro", 6, 0),
            ("Cape Town", 6, 0),
            ("Madras", 6, 0),
            ("Canton", 6, 0),
            ("Sydney", 6, 0),
            ("Peking", 6, 8),
        ],
        {"v_max": 110 / 24, "off_kmd": 45, "beyond": "post roads and ports"},
    ),
    "1850": (
        "Europe from Paris, c. 1850",
        ("Fastest public journey from Paris by the first railways, mail coach and steamer"),
        "The world from Paris, c. 1850",
        "Fastest public journey from Paris at the dawn of rail and steam",
        [
            ("Paris", -7, 8),
            ("London", -7, 0),
            ("Brussels", 7, 4),
            ("Lyon", 7, 0),
            ("Marseille", 7, -6),
            ("Bordeaux", -7, 0),
            ("Madrid", 7, 0),
            ("Rome", 7, 4),
            ("Vienna", 7, 0),
            ("Berlin", 7, 0),
            ("St Petersburg", 7, 0),
            ("Constantinople", -7, -9),
            ("Amsterdam", 7, 4),
        ],
        [
            ("Paris", 6, 6),
            ("New York", 6, 0),
            ("San Francisco", -6, 0),
            ("Rio de Janeiro", 6, 0),
            ("Cape Town", 6, 0),
            ("Alexandria", -6, -6),
            ("Bombay", -6, 0),
            ("Hong Kong", 6, 0),
            ("Sydney", 6, 0),
            ("Peking", 6, 8),
        ],
        {"v_max": 40, "off_kmd": 60, "beyond": "railways, post roads and ports"},
    ),
    "1914": (
        "Europe from Paris, c. 1914",
        ("Fastest scheduled travel time from Paris by rail and steamer, on the eve of the First World War"),
        "The world from Paris, c. 1914",
        "Fastest scheduled travel time from Paris by rail and steamship",
        [
            ("Paris", 7, 0),
            ("London", -7, 0),
            ("Berlin", 7, 0),
            ("Madrid", 7, 0),
            ("Rome", 7, 4),
            ("Vienna", 7, 0),
            ("Constantinople", -7, -9),
            ("St Petersburg", 7, 0),
            ("Moscow", 7, 0),
            ("Stockholm", 7, 0),
            ("Lisbon", 7, -6),
            ("Athens", 7, 0),
            ("Algiers", 7, 0),
        ],
        [
            ("Paris", 6, 6),
            ("New York", 6, 0),
            ("San Francisco", -6, 0),
            ("Buenos Aires", 6, 0),
            ("Rio de Janeiro", 6, 0),
            ("Cape Town", 6, 0),
            ("Cairo", 6, -5),
            ("Bombay", -6, 0),
            ("Singapore", 6, 0),
            ("Peking", -6, 5),
            ("Tokyo", 6, 0),
            ("Sydney", 6, 0),
            ("Moscow", 6, 4),
            ("Dakar", -6, 0),
        ],
        {"v_max": 45, "off_kmd": 50, "beyond": "stations and ports"},
    ),
    "1950": (
        "Europe from Paris, c. 1950",
        "Fastest scheduled journey from Paris by piston airliner, train or car",
        "The world from Paris, c. 1950",
        "Fastest scheduled journey from Paris by piston airliner",
        MOD_EU,
        MOD_W,
        {"v_max": 60, "off_kmd": 250, "beyond": MODERN},
    ),
    "1975": (
        "Europe from Paris, c. 1975",
        "Fastest scheduled journey from Paris by jet, train or car",
        "The world from Paris, c. 1975",
        "Fastest scheduled journey from Paris in the jumbo-jet and Concorde era",
        MOD_EU,
        MOD_W,
        {"v_max": 100, "off_kmd": 500, "beyond": MODERN},
    ),
    "today": (
        "Europe from Paris, today",
        "Fastest scheduled journey from Paris by high-speed train or plane",
        "The world from Paris, today",
        "Fastest scheduled journey from Paris today",
        MOD_EU,
        MOD_W,
        {"v_max": 250, "off_kmd": 800, "beyond": MODERN},
    ),
}
# jscpd:ignore-end


def make_era(era, nodes):
    """Draw the Europe and world maps for one era."""
    et, es, wt, ws, eul, wl, opts = ERAS[era]
    opts = dict(opts)
    if "reach" in opts:
        opts["reach"] = [tuple(p) for p in REACH[opts["reach"]]]
    render.europe(nodes, eul, et, es, os.path.join(OUT, f"europe_{era}.png"), **opts)
    render.world(nodes, wl, wt, ws, os.path.join(OUT, f"world_{era}.png"), **opts)
    print("made", era)


# Comparison chart: which CSV place stands for each destination in each era
# (None = no regular route)
ORDER = ["roman", "medieval", "1800", "1850", "1914", "1950", "1975", "today"]
LABELS = ["c. 200", "c. 1300", "c. 1800", "c. 1850", "c. 1914", "c. 1950", "c. 1975", "Today"]
DEST = {
    "London": ["Londinium", "London", "London", "London", "London", "London", "London", "London"],
    "Rome": ["Roma", "Rome", "Rome", "Rome", "Rome", "Rome", "Rome", "Rome"],
    "Istanbul": [
        "Byzantium",
        "Constantinople",
        "Constantinople",
        "Constantinople",
        "Constantinople",
        "Istanbul",
        "Istanbul",
        "Istanbul",
    ],
    "Cairo": ["Memphis", "Cairo", "Cairo", "Cairo", "Cairo", "Cairo", "Cairo", "Cairo"],
    "New York": [None, None, "New York", "New York", "New York", "New York", "New York", "New York"],
    "Bombay": ["Barygaza", "Cambay", "Bombay", "Bombay", "Bombay", "Bombay", "Bombay", "Bombay"],
    "Tokyo": [None, None, None, None, "Tokyo", "Tokyo", "Tokyo", "Tokyo"],
}
# Where the chapter tables round differently from the map nodes,
# the chapter value is used
OVERRIDE = {("London", "today"): 2.25}


def make_chart(eras):
    """Draw the comparison chart of journey times across eras."""
    lookup = {e: {n[0]: n[3] for n in eras[e]} for e in ORDER}
    colors = ["#9e0142", "#f46d43", "#fdae61", "#66c2a5", "#3288bd", "#5e4fa2", "#2b2b2b"]
    offsets = {"Bombay": 7, "New York": -7, "Cairo": 7, "Istanbul": -7}
    fig, ax = plt.subplots(figsize=(11, 6.6), dpi=150)
    for (name, places), c in zip(DEST.items(), colors):
        xs, ys = [], []
        for i, (era, p) in enumerate(zip(ORDER, places)):
            v = OVERRIDE.get((name, era), lookup[era].get(p) if p else None)
            if v is not None:
                xs.append(i)
                ys.append(v)
        ax.plot(xs, ys, "-o", color=c, lw=2.2, ms=5)
        ax.annotate(
            name,
            (xs[-1], ys[-1]),
            xytext=(8, offsets.get(name, 0)),
            textcoords="offset points",
            va="center",
            fontsize=9,
            color=c,
        )
    ax.set_yscale("log")
    ticks = [1, 6, 24, 7 * 24, 30 * 24, 120 * 24]
    ax.set_yticks(ticks)
    ax.set_yticklabels(["1 hour", "6 hours", "1 day", "1 week", "1 month", "4 months"])
    ax.set_xticks(np.arange(len(ORDER)))
    ax.set_xticklabels(LABELS)
    ax.set_xlim(-0.3, len(ORDER) - 0.2)
    ax.grid(axis="y", color="#dddddd")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylabel("Fastest journey from Paris (log scale)", color="#555555")
    fig.text(
        0.07,
        0.96,
        "Two thousand years of shrinking distance",
        fontsize=16,
        fontweight="bold",
        color="#2b2b2b",
        va="top",
    )
    fig.text(
        0.07,
        0.91,
        ("Fastest journey from Paris to seven destinations, by era. Gaps mean no regular route existed."),
        fontsize=10,
        color="#6b6b6b",
        va="top",
    )
    fig.text(
        0.07,
        0.015,
        ("Values from data/travel_times.csv; most are estimates. Roman Bombay = Barygaza; medieval Bombay = Cambay."),
        fontsize=7.8,
        color="#6b6b6b",
    )
    plt.subplots_adjust(top=0.85, bottom=0.1, left=0.12, right=0.93)
    fig.savefig(os.path.join(OUT, "comparison.png"), facecolor="white")
    print("made comparison chart")


def main():
    """Draw the maps for the eras given as arguments (default: all), then the chart."""
    eras = load()
    wanted = sys.argv[1:] or ORDER
    for e in wanted:
        make_era(e, eras[e])
    make_chart(eras)


if __name__ == "__main__":
    main()
