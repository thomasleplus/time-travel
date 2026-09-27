"""Draw the Europe and world isochrone maps."""

import matplotlib
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Polygon, Rectangle
from matplotlib.path import Path
from matplotlib.transforms import Bbox, TransformedBbox

import geo
import surface
from surface import haversine

matplotlib.use("Agg")

# One scale for every map in the document (hours)
BOUNDS = [0, 6, 12, 24, 48, 120, 240, 480, 960, 1920, 1e9]
LABELS = ["< 6 h", "6–12 h", "12 h–1 d", "1–2 d", "2–5 d", "5–10 d", "10–20 d", "20–40 d", "40–80 d", "> 80 d"]
COLORS = ["#9e0142", "#d53e4f", "#f46d43", "#fdae61", "#fee08b", "#e6f598", "#abdda4", "#66c2a5", "#3288bd", "#5e4fa2"]
CMAP = ListedColormap(COLORS)
NORM = BoundaryNorm(BOUNDS, CMAP.N)
SEA = "#eef2f5"
NOSERVICE = "#d4d4d4"
INK = "#2b2b2b"
QUIET = "#6b6b6b"
OFF_NETWORK_KM_PER_DAY = 50.0

plt.rcParams["font.family"] = "DejaVu Sans"


def travel_surface(nodes, LON, LAT, km_per_day=OFF_NETWORK_KM_PER_DAY):
    best = np.full(LON.shape, np.inf)
    for _, lon, lat, hours, _ in nodes:
        t = hours + haversine(lon, lat, LON, LAT) / km_per_day * 24.0
        np.minimum(best, t, out=best)
    return best


def land_mask(LON, LAT):
    pts = np.column_stack([LON.ravel(), LAT.ravel()])
    m = np.zeros(len(pts), bool)
    for p in geo.land_polygons():
        m |= Path(p).contains_points(pts)
    for p in geo.water_polygons():
        m &= ~Path(p).contains_points(pts)
    return m.reshape(LON.shape)


# Equal Earth projection (Šavrič, Patterson, Jenny 2018)
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = np.sqrt(3) / 2


def equal_earth(lon, lat):
    lam, phi = np.radians(lon), np.radians(lat)
    th = np.arcsin(M * np.sin(phi))
    th2 = th * th
    th6 = th2**3
    x = 2 * np.sqrt(3) * lam * np.cos(th) / (3 * (9 * A4 * th6 * th2 + 7 * A3 * th6 + 3 * A2 * th2 + A1))
    y = th * (A4 * th6 * th2 + A3 * th6 + A2 * th2 + A1)
    return x, y


def project(polygon):
    """Project a (lon, lat) polygon to Equal Earth coordinates."""
    a = np.array(polygon)
    px, py = equal_earth(a[:, 0], a[:, 1])
    return np.column_stack([px, py])


def legend(ax, x0, y0, w, h, fontsize):
    n = len(COLORS) + 1
    ax.add_patch(
        Rectangle(
            (x0 + (n - 1) * w / n, y0),
            w / n,
            h,
            transform=ax.transAxes,
            fc=NOSERVICE,
            ec="white",
            lw=0.8,
            clip_on=False,
        )
    )
    ax.text(
        x0 + (n - 0.5) * w / n,
        y0 - 0.012,
        "No regular\nservice",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=fontsize,
        color=QUIET,
    )
    for i, c in enumerate(COLORS):
        ax.add_patch(
            Rectangle((x0 + i * w / n, y0), w / n, h, transform=ax.transAxes, fc=c, ec="white", lw=0.8, clip_on=False)
        )
        ax.text(
            x0 + (i + 0.5) * w / n,
            y0 - 0.012,
            LABELS[i],
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=fontsize,
            color=QUIET,
        )


def label_city(ax, x, y, text, dx, dy, fs, bold=False):
    ax.plot(x, y, "o", ms=3.2, mfc="white", mec=INK, mew=0.9, zorder=6)
    t = ax.annotate(
        text,
        (x, y),
        xytext=(dx, dy),
        textcoords="offset points",
        fontsize=fs,
        color=INK,
        fontweight="bold" if bold else "normal",
        zorder=7,
        ha="left" if dx >= 0 else "right",
        va="center",
    )
    t.set_path_effects([pe.withStroke(linewidth=2.6, foreground="white")])


def fmt(hours):
    if hours < 48:
        h = round(hours * 2) / 2
        return f"{h:g} h".replace(".5 h", "½ h")
    d = hours / 24.0
    d = round(d * 2) / 2
    return f"{d:g} days".replace(".5 days", "½ days")


def _surface(nodes, lon, lat, k, max_km, v_max, step_km, off_kmd=None, reach=None):
    LON, LAT = np.meshgrid(lon, lat)
    LAND = land_mask(LON, LAT)
    if reach is not None:
        LAND = LAND & Path(reach).contains_points(np.column_stack([LON.ravel(), LAT.ravel()])).reshape(LON.shape)

    def lf(lo, la):
        return land_mask(np.asarray(lo), np.asarray(la))

    P, Tn, E, v = surface.build_edges(nodes, k, max_km, v_max, lf)
    seeds = surface.seeds_from(P, Tn, E, v, step_km)
    T = surface.spread(lon, lat, seeds, off_kmd or OFF_NETWORK_KM_PER_DAY, LAND)
    return LON, LAT, np.ma.masked_where(~LAND | ~np.isfinite(T), T)


def europe(
    nodes,
    labels,
    title,
    subtitle,
    out,
    v_max=45,
    off_kmd=50,
    reach=None,
    step_km=4,
    k=5,
    max_km=700,
    beyond="stations and ports",
):
    lon = np.arange(-12, 42.01, 0.08)
    lat = np.arange(33, 64.01, 0.08)
    LON, LAT, T = _surface(nodes, lon, lat, k, max_km, v_max, step_km, off_kmd, reach)
    k = 1 / np.cos(np.radians(48))
    fig = plt.figure(figsize=(11, 9.6), dpi=150)
    ax = fig.add_axes([0.03, 0.12, 0.94, 0.78])
    ax.set_facecolor(SEA)
    for p in geo.land_polygons():
        ax.add_patch(Polygon(p, closed=True, fc=NOSERVICE, ec="none", zorder=0.5))
    ax.pcolormesh(LON, LAT, T, cmap=CMAP, norm=NORM, shading="auto", rasterized=True, zorder=1)
    for p in geo.land_polygons():
        ax.add_patch(Polygon(p, closed=True, fill=False, ec="#555555", lw=0.5, zorder=3))
    for p in geo.water_polygons():
        ax.add_patch(Polygon(p, closed=True, fc=SEA, ec="#555555", lw=0.5, zorder=2))
    ax.set_xlim(-12, 42)
    ax.set_ylim(33, 64)
    ax.set_aspect(k)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#bbbbbb")
    by = {n[0]: n for n in nodes}
    for name, dx, dy in labels:
        _, lo, la, h, basis = by[name]
        txt = name if h == 0 else f"{name} {fmt(h)}" + ("" if basis == "S" else "*")
        label_city(ax, lo, la, txt, dx, dy, 9, bold=h == 0)
    fig.text(0.03, 0.965, title, fontsize=17, fontweight="bold", color=INK, va="top")
    fig.text(0.03, 0.93, subtitle, fontsize=10.5, color=QUIET, va="top")
    legend(ax, 0.0, -0.06, 1.0, 0.025, 8.5)
    fig.text(
        0.03,
        0.022,
        "Schematic map. Times are the fastest journey from Paris; "
        "* = estimate interpolated from sourced journeys. "
        f"Beyond {beyond},\ntravel is assumed at about {off_kmd:g} km per day. "
        "Coastlines simplified.",
        fontsize=7.8,
        color=QUIET,
        va="bottom",
    )
    fig.savefig(out, dpi=150, facecolor="white")
    plt.close(fig)


def cover(eras, title, subtitle, author, outputs):
    """Draw the book cover: one stretch of Europe cut into a strip per era.

    eras lists (label, nodes, options) from the oldest era to the newest. Each
    output is (path, (width, height) in inches, dpi); the map widens or narrows
    to fill the page, so every strip keeps the same geography.
    """
    # Twice as fine as the Europe maps: the cover shows Europe larger
    lon = np.arange(-16, 42.01, 0.04)
    lat = np.arange(33, 64.01, 0.04)
    land = None
    surfaces = []
    for label, nodes, opts in eras:
        LON, LAT, T = _surface(nodes, lon, lat, 5, 700, opts["v_max"], 4, opts["off_kmd"], opts.get("reach"))
        if land is None:
            land = land_mask(LON, LAT)
        surfaces.append((label, _bleed(T, land)))
    for out, size, dpi in outputs:
        _cover_page(LON, LAT, surfaces, title, subtitle, author, out, size, dpi)


# Beyond every travel time, for land that the era's network does not reach
_NO_SERVICE = 2 * BOUNDS[-1]


def _bleed(T, land, cells=3):
    """Mark unreached land as no service, then carry the times a few cells out to sea.

    The cover clips its colours to the coastline, so they must reach past it:
    the grid's cells would otherwise leave gaps along the coast.
    """
    V = T.filled(np.inf)
    V[land & ~np.isfinite(V)] = _NO_SERVICE
    for _ in range(cells):
        near = V.copy()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            np.minimum(near, np.roll(V, (dy, dx), axis=(0, 1)), out=near)
        V = np.where(np.isinf(V), near, V)
    return np.ma.masked_invalid(V)


def _cover_page(LON, LAT, surfaces, title, subtitle, author, out, size, dpi):
    box = [0, 0.15, 1, 0.64]
    lat0, lat1 = 37.5, 56
    # Same aspect as the Europe maps, centred on Paris so that every strip crosses land
    k = 1 / np.cos(np.radians(48))
    span = (lat1 - lat0) * k * (size[0] * box[2]) / (size[1] * box[3])
    lon0 = 2.35 - span / 2
    n = len(surfaces)
    fig = plt.figure(figsize=size, dpi=dpi, facecolor=INK)

    def frame(ax, x0, x1):
        ax.set_xlim(x0, x1)
        ax.set_ylim(lat0, lat1)
        ax.set_aspect(k)
        ax.axis("off")

    # Filled contours rather than grid cells, clipped to the coastline, so the
    # colours have smooth edges (and are vector shapes in the PDF). Each strip
    # has its own axes, whose frame cuts it to its stretch of longitude.
    land = [Polygon(p, closed=True).get_path() for p in geo.land_polygons()]
    rows = (LAT[:, 0] > lat0 - 1) & (LAT[:, 0] < lat1 + 1)
    for i, (label, T) in enumerate(surfaces):
        a, b = lon0 + i * span / n, lon0 + (i + 1) * span / n
        ax = fig.add_axes([box[0] + box[2] * i / n, box[1], box[2] / n, box[3]])
        frame(ax, a, b)
        cols = (LON[0] > a - 1) & (LON[0] < b + 1)
        cs = ax.contourf(
            LON[np.ix_(rows, cols)],
            LAT[np.ix_(rows, cols)],
            T[np.ix_(rows, cols)],
            levels=BOUNDS + [2 * _NO_SERVICE],
            colors=COLORS + [NOSERVICE],
            zorder=1,
        )
        # A new path for each strip: Agg reuses the last clip mask when the path and transform are
        # the same, and neighbouring strips can have the same transform
        cs.set_clip_path(Path.make_compound_path(*land), ax.transData)
        # The sea is the page colour, so the land floats on the cover
        for p in geo.water_polygons():
            ax.add_patch(Polygon(p, closed=True, fc=INK, ec="none", zorder=2))
        fig.text(
            box[0] + box[2] * (i + 0.5) / n,
            box[1] - 0.012,
            label,
            ha="center",
            va="top",
            fontsize=size[0] * 1.4,
            color="white",
        )
    # Over the strips: the lines between them, and Paris
    ax = fig.add_axes(box)
    frame(ax, lon0, lon0 + span)
    for i in range(1, n):
        ax.axvline(lon0 + i * span / n, color=INK, lw=size[0] * 0.25, zorder=4)
    ax.plot(2.35, 48.86, "o", ms=size[0] * 1.1, mfc="white", mec=INK, mew=1.2, zorder=5)
    fig.text(0.07, 0.93, title, fontsize=size[0] * 5, fontweight="bold", color="white", va="top")
    fig.text(0.07, 0.855, subtitle, fontsize=size[0] * 2.6, color="#fee08b", va="top")
    fig.text(0.07, 0.045, author, fontsize=size[0] * 2.4, color="white", va="bottom")
    fig.savefig(out, dpi=dpi, facecolor=INK, metadata={"CreationDate": None} if out.endswith(".pdf") else None)
    plt.close(fig)


def world(
    nodes,
    labels,
    title,
    subtitle,
    out,
    v_max=45,
    off_kmd=50,
    reach=None,
    step_km=12,
    k=5,
    max_km=2500,
    beyond="stations and ports",
):
    lon = np.arange(-180, 180.0, 0.4)
    lat = np.arange(-56, 84.01, 0.4)
    LON, LAT, T = _surface(nodes, lon, lat, k, max_km, v_max, step_km, off_kmd, reach)
    X, Y = equal_earth(LON, LAT)
    fig = plt.figure(figsize=(13, 7.8), dpi=150)
    ax = fig.add_axes([0.02, 0.13, 0.96, 0.74])
    # ocean outline of the projection
    olat = np.linspace(-56, 84, 200)
    ex, ey = equal_earth(np.r_[np.full(200, -180), np.full(200, 180)], np.r_[olat, olat[::-1]])
    ax.fill(ex, ey, color=SEA, zorder=0)
    for p in geo.land_polygons():
        ax.add_patch(Polygon(project(p), closed=True, fc=NOSERVICE, ec="none", zorder=0.5))
    ax.pcolormesh(X, Y, T, cmap=CMAP, norm=NORM, shading="auto", rasterized=True, zorder=1)
    for p in geo.land_polygons():
        ax.add_patch(Polygon(project(p), closed=True, fill=False, ec="#555555", lw=0.45, zorder=3))
    for p in geo.water_polygons():
        ax.add_patch(Polygon(project(p), closed=True, fc=SEA, ec="#555555", lw=0.45, zorder=2))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(ex.min() * 1.01, ex.max() * 1.01)
    ax.set_ylim(ey.min() * 1.02, ey.max() * 1.02)
    by = {n[0]: n for n in nodes}
    for name, dx, dy in labels:
        _, lo, la, h, basis = by[name]
        x, y = equal_earth(lo, la)
        txt = name if h == 0 else f"{name} {fmt(h)}" + ("" if basis == "S" else "*")
        label_city(ax, x, y, txt, dx, dy, 8.5, bold=h == 0)
    fig.text(0.03, 0.965, title, fontsize=17, fontweight="bold", color=INK, va="top")
    fig.text(0.03, 0.925, subtitle, fontsize=10.5, color=QUIET, va="top")
    legend(ax, 0.02, -0.035, 0.96, 0.03, 8.5)
    fig.text(
        0.03,
        0.02,
        "Schematic map, Equal Earth projection. "
        "Times are the fastest journey from Paris; "
        "* = estimate interpolated from sourced journeys. "
        f"Beyond {beyond},\ntravel is assumed at about {off_kmd:g} km per day. "
        "Coastlines simplified.",
        fontsize=7.8,
        color=QUIET,
        va="bottom",
    )
    fig.savefig(out, dpi=150, facecolor="white")
    plt.close(fig)
