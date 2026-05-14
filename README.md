# Sphere — A Polar-Coordinate Graph Data Structure

## Concept

**Sphere** is a graph data structure rooted at a **center node** (the origin). Every other node is addressed by its **polar coordinates** — a radius `r` and an angle `θ` — rather than a flat array index or hash key. In three dimensions, a second angle `φ` (elevation) is added, giving full spherical coordinates `(r, θ, φ)`.

```
                    Node(r=2, θ=45°)
                   /
Center(0,0) ---- Node(r=1, θ=0°) ---- Node(r=2, θ=0°)
                   \
                    Node(r=2, θ=-45°)
```

The center holds a pointer. From it, any node can be reached in **O(1)** via coordinate-hashed lookup, or traversed angularly in **O(k)** where `k` is the number of nodes at that radius shell.

---

## Core Geometry

### 2D Polar Form
A node at `(r, θ)` maps to Cartesian position:
```
x = r · cos(θ)
y = r · sin(θ)
```

### 3D Spherical Form
A node at `(r, θ, φ)` maps to:
```
x = r · sin(φ) · cos(θ)
y = r · sin(φ) · sin(θ)
z = r · cos(φ)
```

θ = azimuth (0° to 360°), φ = elevation (-90° to +90°)

---

## Data Structure Definition

```python
class SphereNode:
    r: float          # distance from center
    theta: float      # azimuth angle in degrees [0, 360)
    phi: float        # elevation angle in degrees [-90, 90]  (0 for 2D)
    value: Any        # payload
    edges: list[tuple[SphereNode, float]]  # (neighbor, delta_theta)

class Sphere:
    center: SphereNode          # root at (0, 0, 0)
    index: dict[tuple, SphereNode]  # (r_bucket, theta_bucket, phi_bucket) → node
    resolution: float           # angular bucket size in degrees (e.g. 1.0)
    shell_step: float           # radial step size (e.g. 1.0)
```

### Coordinate Key (Bucketed Hash)
```python
def key(r, theta, phi, resolution=1.0, shell_step=1.0):
    return (
        round(r / shell_step),
        round(theta % 360 / resolution),
        round((phi + 90) / resolution)
    )
```

---

## Operations & Complexity

| Operation | Time | Description |
|---|---|---|
| `insert(r, θ, φ, value)` | **O(1)** avg | Hash coordinate key → store node |
| `lookup(r, θ, φ)` | **O(1)** avg | Direct key lookup in hash index |
| `neighbors(node, Δθ)` | **O(1)** avg | Lookup at `(r, θ+Δθ, φ)` |
| `ring_scan(r)` | **O(k)** | All nodes at radius `r` |
| `cone_scan(θ, width)` | **O(k)** | All nodes within angular band |
| `radial_path(θ, φ)` | **O(shells)** | Walk outward along a bearing |
| `nearest(r, θ, φ)` | **O(1)** avg | Quantized bucket lookup |
| `range_query(r1, r2, θ1, θ2)` | **O(k)** | Nodes in spherical wedge |
| `delete(r, θ, φ)` | **O(1)** avg | Remove from index + unlink edges |
| `edge(node_a, node_b, Δθ)` | **O(1)** | Attach two nodes with angular offset |

Space complexity: **O(n)** — one entry per node in the index.

---

## Fastest Lookup Path

```
lookup(r=5.0, θ=120°, φ=30°)
  │
  ▼
key = (5, 120, 120)          ← O(1) integer hash
  │
  ▼
index[key] → SphereNode      ← O(1) dict access
  │
  ▼
return node.value            ← done
```

Total: **2 arithmetic ops + 1 hash table access = O(1)**

For spatial range queries, iterate only over quantized buckets in the wedge — no distance comparisons needed beyond bucket arithmetic.

---

## Comparison with Existing Data Structures

| Structure | Lookup | Spatial Range | Insert | Space | Natural Shape | Best For |
|---|---|---|---|---|---|---|
| **Sphere (this)** | **O(1)** | **O(k)** | **O(1)** | **O(n + B)** | Spherical/Circular | Radial maps, signal propagation, radar |
| Hash Map | O(1) | O(n) | O(1) | O(n) | None | Key-value, no spatial awareness |
| Graph (adj list) | O(V+E) | O(V+E) | O(1) | O(V + E) | Arbitrary | General topology, routing |
| K-d Tree | O(log n) | O(√n) | O(log n) | O(n) | Axis-aligned | Nearest-neighbor in Cartesian |
| R-Tree | O(log n) | O(log n + k) | O(log n) | O(n) | Rectangles | Geographic bounding boxes |
| Quad Tree | O(log n) | O(log n + k) | O(log n) | O(n log n) | Square tiles | 2D region subdivision |
| Oct Tree | O(log n) | O(log n + k) | O(log n) | O(n log n) | Cubic voxels | 3D volumetric scenes |
| Geohash | O(1) | O(k·neighbors) | O(1) | O(n · L) | Grid on sphere | Proximity on Earth's surface |
| Skip List | O(log n) | O(log n + k) | O(log n) | O(n log n) | Linear | Ordered sequences |
| B-Tree | O(log n) | O(log n + k) | O(log n) | O(n) | Sorted pages | Database indexes |

**Space complexity notes:**
- `n` = number of nodes, `k` = number of results returned, `E` = number of edges, `B` = number of allocated buckets in the coordinate hash (depends on `resolution` and `shell_step`), `L` = geohash string length (typically 12 bytes per entry)
- **Sphere O(n + B)**: Each node takes O(1) in the hash index (one entry per node = O(n)). The bucket count `B` is bounded by `(r_max / shell_step) × (360 / resolution) × (180 / resolution)`. For sparse data, B can exceed n — the primary trade-off vs. pure O(n) structures.
- **Quad/Oct Tree O(n log n)**: Internal branching nodes are allocated even for empty space; a tree of depth `d` over `n` points uses O(n·d) = O(n log n) nodes in the worst case.
- **Skip List O(n log n)**: Each element is duplicated across O(log n) levels on average.
- **Geohash O(n · L)**: Stores a fixed-length string key per node; constant per node but with a larger constant than a 3-integer tuple.

### Where Sphere Wins

- **Radial lookup beats K-d and R-Tree** when coordinates are naturally polar (GPS, radar, sonar). K-d/R-Tree add log-factor overhead from tree traversal that Sphere avoids with direct hashing.
- **Beats Geohash for directional queries** — Geohash encodes proximity poorly across cell boundaries at cardinal edges. Sphere's angle-bucket design handles wrap-around at 0°/360° cleanly.
- **Beats plain graphs for spatial routing** — Graphs have no spatial locality; adjacent-angle neighbors require edge traversal. Sphere's index makes "what is 10° to my left at this range?" a direct O(1) lookup.
- **Space-competitive with trees for dense polar data** — When data fills many shells uniformly (radar sweeps, LIDAR point clouds), `B ≈ n` and Sphere matches O(n) tree space while beating their O(log n) query time.

### Where Sphere Has Trade-offs

- **Sparse data inflates B** — If data clusters in one sector, the hash still allocates buckets proportional to the angular/radial resolution across the whole sphere. Tune `resolution` and `shell_step` to the actual data density.
- **Resolution sensitivity** — Bucket size `resolution` must be chosen carefully; too coarse loses precision, too fine degrades to sparse hash and wastes space.
- **Curved-surface distortion** — At high latitudes on a globe, fixed `Δθ` steps cover less physical distance. Adaptive shell weighting (`Δx = r·sin(φ)·Δθ`) compensates.

---

## Use Cases

### Maps & Navigation
- **Turn-by-turn GPS**: Center = current position. Shells = distance rings (100m, 500m, 1km…). Theta = compass bearing. Lookup nearest turn in O(1) per bearing.
- **Offline map tiles**: Tiles addressed by `(zoom_level=r, tile_x=θ, tile_y=φ)`. Instant tile fetch without tree traversal.
- **Helicopter/drone routing**: 3D spherical coordinates model altitude + bearing + range natively.

### Wireless & Signal
- **Cell tower coverage**: Each tower is the center; nodes = subscriber devices at `(distance, azimuth)`. Signal-strength queries are ring scans.
- **Radar tracking**: Sweep angle θ over time; objects appear at known `(r, θ)`. O(1) update and lookup per sweep tick.
- **Sonar/LIDAR point clouds**: Sensor is center; returns land at `(r, θ, φ)`. Sphere indexes each return in O(1) — faster ingestion than Octrees for rotating sensors.

### Astronomy & Space
- **Star catalogs**: Center = observer. Stars at `(distance, right_ascension, declination)`. Constellation queries = cone scans.
- **Satellite orbit tracking**: Shells = orbital altitudes; theta = longitude. Angular proximity queries for collision avoidance.
- **Telescope field-of-view indexing**: Rapidly find all cataloged objects within angular cone.

### Gaming & Simulation
- **Fog of war**: Player = center. Visibility radius = shell. Reveal tiles in O(k) per frame.
- **Explosion radius**: Damage nodes within shell `r < blast_radius` in one ring scan.
- **NPC patrol paths**: Define as angular waypoints; navigate by incrementing θ.

### Networking & Distributed Systems
- **Consistent hashing ring** (extended): Nodes on ring at θ positions; virtual replicas as inner shells. Adds radial replication depth absent in standard Chord/ring DHTs.
- **Latency-aware topology**: Latency = radius; region = theta. Route to nearest (lowest-r) healthy node in a sector.

### Biology & Medicine
- **MRI/CT scan slices**: Center = anatomical landmark; slices at radius shells; angular sectors = anatomical regions. Anomaly detection via ring scan.
- **Neural connectivity maps**: Neuron = center; axon reach = radius; synaptic angle = theta. Models dendritic fan-out naturally.

### Robotics
- **360° obstacle avoidance**: Robot = center; LIDAR returns = `(r, θ)` nodes. Nearest obstacle = `min_r` ring scan.
- **Arm kinematics workspace**: Reachable positions are naturally spherical; IK lookup becomes a coordinate hash.

---

## Example: Map Navigation

```python
sphere = Sphere(resolution=1.0, shell_step=100)  # 100m shells, 1° resolution

# Insert road nodes
sphere.insert(r=500,  theta=0,   phi=0, value="North Road")
sphere.insert(r=500,  theta=90,  phi=0, value="East Road")
sphere.insert(r=1000, theta=45,  phi=0, value="NE Highway")
sphere.insert(r=200,  theta=270, phi=0, value="West Lane")

# O(1): What is 500m directly north?
node = sphere.lookup(r=500, theta=0, phi=0)   # → "North Road"

# O(k): All roads within 500m
nearby = sphere.ring_scan(r=500)              # → [North Road, East Road]

# O(k): Roads in northeast quadrant (0°–90°)
ne_roads = sphere.cone_scan(theta_min=0, theta_max=90, r_max=1000)
```

---

## Implementation Sketch

```python
import math
from collections import defaultdict

class SphereNode:
    def __init__(self, r, theta, phi, value):
        self.r, self.theta, self.phi = r, theta, phi
        self.value = value
        self.edges = []  # list of (SphereNode, delta_theta)

class Sphere:
    def __init__(self, resolution=1.0, shell_step=1.0):
        self.resolution = resolution
        self.shell_step = shell_step
        self.center = SphereNode(0, 0, 0, "origin")
        self.index = {}

    def _key(self, r, theta, phi):
        return (
            round(r / self.shell_step),
            round((theta % 360) / self.resolution),
            round((phi + 90) / self.resolution),
        )

    def insert(self, r, theta, phi, value):
        node = SphereNode(r, theta, phi, value)
        self.index[self._key(r, theta, phi)] = node
        return node

    def lookup(self, r, theta, phi):
        return self.index.get(self._key(r, theta, phi))

    def ring_scan(self, r):
        r_bucket = round(r / self.shell_step)
        return [n for k, n in self.index.items() if k[0] == r_bucket]

    def cone_scan(self, theta_min, theta_max, r_max=None):
        results = []
        for (r_b, t_b, p_b), node in self.index.items():
            if theta_min / self.resolution <= t_b <= theta_max / self.resolution:
                if r_max is None or node.r <= r_max:
                    results.append(node)
        return results

    def connect(self, node_a, node_b):
        delta_theta = (node_b.theta - node_a.theta) % 360
        node_a.edges.append((node_b, delta_theta))
        node_b.edges.append((node_a, (360 - delta_theta) % 360))

    def radial_path(self, theta, phi, r_max):
        path = [self.center]
        r = self.shell_step
        while r <= r_max:
            node = self.lookup(r, theta, phi)
            if node:
                path.append(node)
            r += self.shell_step
        return path
```

---

## Design Decisions

**Why hash over tree?**
Polar coordinates quantize naturally into integer buckets. A hash gives O(1) vs O(log n) for trees. The trade-off — no guaranteed neighbor adjacency — is solved by the angular-offset edge list on each node.

**Why center as explicit pointer?**
The center is special: it has no `(r, θ)` — it is the reference frame. Keeping it as a named pointer avoids special-casing r=0 in the hash and makes "navigate from origin" a direct pointer dereference.

**Why store edges separately from the index?**
The hash index gives coordinate-addressed lookup. Edges give topology-addressed traversal. Both are needed: maps need "what is at bearing 045°, 2km?" (index) and "what roads connect here?" (edges).

---

## Name

**Sphere** — because the structure's natural geometry is a sphere of shells expanding from a center, each shell divided into angular sectors, forming a coordinate-addressed graph that lives on and within a sphere.
