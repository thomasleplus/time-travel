"""Travel-time surface: a graph of known journeys spread over land by Dijkstra."""

import heapq

import numpy as np


def haversine(lon1, lat1, lon2, lat2):
    """Great-circle distance in km."""
    lon1, lat1, lon2, lat2 = map(np.radians, (lon1, lat1, lon2, lat2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def build_edges(nodes, k, max_km, v_max_kmh, land_fn):
    """Connect each node to its k nearest neighbours over land.

    Speed along an edge is inferred from the endpoints' times (never faster than
    v_max), so an edge never implies a better service than its ends.
    """
    P = np.array([(n[1], n[2]) for n in nodes])
    T = np.array([n[3] for n in nodes])
    edges = set()
    for i in range(len(nodes)):
        d = haversine(P[i, 0], P[i, 1], P[:, 0], P[:, 1])
        for j in np.argsort(d)[1 : k + 1]:
            if d[j] > max_km:
                continue
            s = np.linspace(0, 1, 9)
            lo = P[i, 0] + s * (P[j, 0] - P[i, 0])
            la = P[i, 1] + s * (P[j, 1] - P[i, 1])
            if land_fn(lo, la).mean() < 0.75:
                continue  # sea crossing: ships only link ports via node times
            edges.add((min(i, j), max(i, j)))
    return P, T, edges, v_max_kmh


def seeds_from(P, T, edges, v_max, step_km):
    """Seed points along each edge, timed from its faster end."""
    pts = [(p[0], p[1], t) for p, t in zip(P, T)]
    for i, j in edges:
        L = haversine(P[i, 0], P[i, 1], P[j, 0], P[j, 1])
        v = min(v_max, L / max(abs(T[i] - T[j]), 1e-6))
        n = max(2, int(L / step_km))
        for s in np.linspace(0, 1, n + 1)[1:-1]:
            t = min(T[i] + s * L / v, T[j] + (1 - s) * L / v)
            pts.append((P[i, 0] + s * (P[j, 0] - P[i, 0]), P[i, 1] + s * (P[j, 1] - P[i, 1]), t))
    return pts


def spread(lon, lat, seeds, km_per_day, LAND):
    """Dijkstra over land cells from seeded (time) cells.

    Off-network travel is at km_per_day.
    """
    ny, nx = LAND.shape
    dlon, dlat = lon[1] - lon[0], lat[1] - lat[0]
    T = np.full((ny, nx), np.inf)
    h = []
    for lo, la, t in seeds:
        ix = round((lo - lon[0]) / dlon)
        iy = round((la - lat[0]) / dlat)
        if 0 <= ix < nx and 0 <= iy < ny and t < T[iy, ix]:
            T[iy, ix] = t
            heapq.heappush(h, (t, iy, ix))
    kmx = 111.32 * np.cos(np.radians(lat)) * dlon
    kmy = 111.32 * dlat
    hpk = 24.0 / km_per_day
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    while h:
        t, iy, ix = heapq.heappop(h)
        if t > T[iy, ix]:
            continue
        for dy, dx in nb:
            y, x = iy + dy, ix + dx
            if x < 0 or x >= nx:
                x %= nx  # wrap longitude for world grids
            if y < 0 or y >= ny or not LAND[y, x]:
                continue
            dist = np.hypot(kmx[iy] * dx, kmy * dy)
            nt = t + dist * hpk
            if nt < T[y, x]:
                T[y, x] = nt
                heapq.heappush(h, (nt, y, x))
    return T
