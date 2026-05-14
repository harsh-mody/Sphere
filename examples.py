# -*- coding: utf-8 -*-
"""
Runnable examples for the Sphere data structure.
Run with:  python3 examples.py
"""
from sphere import Sphere, SphereNode


# ──────────────────────────────────────────────────────────────────────────────
# 1. Map Navigation
# ──────────────────────────────────────────────────────────────────────────────

def example_map():
    print("=" * 60)
    print("EXAMPLE 1: Map Navigation")
    print("=" * 60)

    # 100m shells, 1° angular resolution — center = current position
    sphere = Sphere(resolution=1.0, shell_step=100)

    north      = sphere.insert(r=500,  theta=0,   value="North Road")
    east       = sphere.insert(r=500,  theta=90,  value="East Road")
    northeast  = sphere.insert(r=1000, theta=45,  value="NE Highway")
    west_lane  = sphere.insert(r=200,  theta=270, value="West Lane")
    south_sq   = sphere.insert(r=300,  theta=180, value="South Square")

    # Connect roads
    sphere.connect(north, northeast)
    sphere.connect(east, northeast)

    # O(1) — what is 500m directly north?
    hit = sphere.lookup(r=500, theta=0)
    print(f"\nLookup (500m, 0°):  {hit}")

    # O(k) — all roads within 500m ring
    ring = sphere.ring_scan(r=500)
    print(f"Ring scan r=500m:   {[n.value for n in ring]}")

    # O(k) — roads in northeast quadrant
    ne = sphere.cone_scan(theta_min=0, theta_max=90, r_max=1000)
    print(f"NE cone (0–90°):    {[n.value for n in ne]}")

    # O(k) — range query: 200–600m in any direction
    nearby = sphere.range_query(r_min=200, r_max=600, theta_min=0, theta_max=360)
    print(f"Range 200–600m:     {[n.value for n in nearby]}")

    # Radial path northward
    path = sphere.radial_path(theta=0, r_max=1500)
    print(f"Radial path (N):    {[n.value for n in path]}")

    # Nearest to an approximate position
    near = sphere.nearest(r=480, theta=2)
    print(f"Nearest to (480m,2°): {near}")

    print(f"\nStats: {sphere.stats()}")


# ──────────────────────────────────────────────────────────────────────────────
# 2. Radar Tracking
# ──────────────────────────────────────────────────────────────────────────────

def example_radar():
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Radar Tracking")
    print("=" * 60)

    radar = Sphere(resolution=2.0, shell_step=10)  # 10km shells, 2° sweep steps

    # Detected contacts at various bearings and ranges (km)
    radar.insert(r=50,  theta=30,  value={"id": "A1", "type": "aircraft"})
    radar.insert(r=120, theta=145, value={"id": "B2", "type": "ship"})
    radar.insert(r=80,  theta=30,  value={"id": "A2", "type": "aircraft"})
    radar.insert(r=200, theta=270, value={"id": "C1", "type": "unknown"})
    radar.insert(r=60,  theta=32,  value={"id": "A3", "type": "aircraft"})

    # All contacts on the 50km ring
    close = radar.ring_scan(r=50)
    print(f"\nContacts at 50km:   {[n.value['id'] for n in close]}")

    # Contacts in northwest quadrant (270°–360°)
    nw = radar.cone_scan(theta_min=270, theta_max=360, r_max=250)
    print(f"NW quadrant:        {[n.value['id'] for n in nw]}")

    # All aircraft (filter post-scan)
    all_contacts = radar.all_nodes()
    aircraft = [n for n in all_contacts if n.value["type"] == "aircraft"]
    print(f"Aircraft count:     {len(aircraft)}")

    # Track cluster at bearing 30° (ring-30° to ring-35°)
    cluster = radar.cone_scan(theta_min=28, theta_max=35)
    print(f"Cluster at ~30°:    {[n.value['id'] for n in cluster]}")


# ──────────────────────────────────────────────────────────────────────────────
# 3. Star Catalog (3D spherical)
# ──────────────────────────────────────────────────────────────────────────────

def example_stars():
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Star Catalog (3D)")
    print("=" * 60)

    # r = distance in light-years, theta = RA (0–360°), phi = declination (-90–90°)
    catalog = Sphere(resolution=0.5, shell_step=10)

    sirius    = catalog.insert(r=8.6,   theta=101.3, phi=-16.7, value="Sirius")
    canopus   = catalog.insert(r=310,   theta=95.9,  phi=-52.7, value="Canopus")
    rigel     = catalog.insert(r=860,   theta=78.6,  phi=-8.2,  value="Rigel")
    betelgeuse= catalog.insert(r=700,   theta=88.8,  phi=7.4,   value="Betelgeuse")
    proxima   = catalog.insert(r=4.2,   theta=217.4, phi=-62.7, value="Proxima Centauri")
    vega      = catalog.insert(r=25,    theta=279.2, phi=38.8,  value="Vega")

    # Stars within 30 light-years
    local = catalog.range_query(r_min=0, r_max=30, theta_min=0, theta_max=360)
    print(f"\nStars within 30 ly: {[n.value for n in local]}")

    # Stars in Orion's area: RA 75–95°, dec -15° to 10°
    orion_area = catalog.cone_scan(theta_min=75, theta_max=100, phi_min=-15, phi_max=10)
    print(f"Orion region:       {[n.value for n in orion_area]}")

    # Angular distance between Rigel and Betelgeuse
    angle = rigel.angular_distance(betelgeuse)
    print(f"Rigel–Betelgeuse angular distance: {angle:.2f}°")

    # Bearing from Vega to Sirius
    bearing = vega.bearing_to(sirius)
    print(f"Bearing Vega→Sirius: {bearing:.1f}°")


# ──────────────────────────────────────────────────────────────────────────────
# 4. Graph Traversal (BFS / Dijkstra)
# ──────────────────────────────────────────────────────────────────────────────

def example_traversal():
    print("\n" + "=" * 60)
    print("EXAMPLE 4: BFS + Shortest Path")
    print("=" * 60)

    g = Sphere(resolution=45.0, shell_step=1.0)

    a = g.insert(r=1, theta=0,   value="A")
    b = g.insert(r=1, theta=90,  value="B")
    c = g.insert(r=2, theta=0,   value="C")
    d = g.insert(r=2, theta=90,  value="D")
    e = g.insert(r=3, theta=45,  value="E")

    g.connect(g.center, a)
    g.connect(g.center, b)
    g.connect(a, c)
    g.connect(b, d)
    g.connect(c, e)
    g.connect(d, e)

    bfs_order = list(g.bfs(g.center))
    print(f"\nBFS from center:    {[n.value for n in bfs_order]}")

    path = g.shortest_path(g.center, e, weight="hops")
    print(f"Shortest path →E:   {[n.value for n in path]}")

    path_dist = g.shortest_path(g.center, e, weight="distance")
    print(f"Shortest path (dist):{[n.value for n in path_dist]}")


# ──────────────────────────────────────────────────────────────────────────────
# 5. Robotics — 360° LIDAR obstacle avoidance
# ──────────────────────────────────────────────────────────────────────────────

def example_lidar():
    print("\n" + "=" * 60)
    print("EXAMPLE 5: LIDAR Obstacle Avoidance")
    print("=" * 60)

    lidar = Sphere(resolution=1.0, shell_step=0.1)  # 10cm shells, 1° sweep

    # Simulated LIDAR returns (distance in meters, sweep angle)
    returns = [
        (1.5, 10),  (1.4, 11),  (1.3, 12),   # wall cluster
        (3.0, 90),                              # distant object
        (0.8, 175), (0.9, 176), (0.85, 177),  # close obstacle behind
        (5.0, 270),                             # open space left
    ]
    for r, theta in returns:
        lidar.insert(r=r, theta=theta, value=f"obstacle@{theta}°")

    # Danger zone: anything within 1m
    danger = lidar.range_query(r_min=0, r_max=1.0, theta_min=0, theta_max=360)
    print(f"\nDanger zone (<1m):  {[n.value for n in danger]}")

    # Nearest obstacle in forward arc (350°–10°, handle wrap)
    forward = lidar.cone_scan(theta_min=350, theta_max=10, r_max=5.0)
    print(f"Forward arc (±10°): {[n.value for n in forward]}")

    # Minimum clearance distance
    if lidar.all_nodes():
        min_r = min(n.r for n in lidar.all_nodes())
        print(f"Minimum clearance:  {min_r:.2f}m")


if __name__ == "__main__":
    example_map()
    example_radar()
    example_stars()
    example_traversal()
    example_lidar()
