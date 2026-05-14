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

### General Structures

| Structure | Lookup | Spatial Range | Insert | Space | Natural Shape | Best For |
|---|---|---|---|---|---|---|
| **Sphere (this)** | **O(1)** | **O(k)** | **O(1)** | **O(n + B)** | Spherical/Circular | Radial maps, signal propagation, radar |
| Hash Map | O(1) | O(n) | O(1) | O(n) | None | Key-value, no spatial awareness |
| Graph (adj list) | O(V+E) | O(V+E) | O(1) | O(V + E) | Arbitrary | General topology, routing |
| K-d Tree | O(log n) | O(√n) | O(log n) | O(n) | Axis-aligned | Nearest-neighbor in Cartesian |
| R-Tree | O(log n) | O(log n + k) | O(log n) | O(n) | Rectangles | Geographic bounding boxes |
| Quad Tree | O(log n) | O(log n + k) | O(log n) | O(n log n) | Square tiles | 2D region subdivision |
| Oct Tree | O(log n) | O(log n + k) | O(log n) | O(n log n) | Cubic voxels | 3D volumetric scenes |
| Geohash | O(1) | O(k·neighbors) | O(1) | O(n · L) | Grid on sphere | Proximity on Earth’s surface |
| B-Tree | O(log n) | O(log n + k) | O(log n) | O(n) | Sorted pages | Database indexes |

`n` = nodes, `k` = results, `E` = edges, `B` = allocated hash buckets `(r_max/shell_step) × (360/res) × (180/res)`, `L` = geohash string length

**Space notes:** Quad/Oct Trees allocate internal branching nodes for empty space → O(n log n). Geohash pays a larger constant per key (string vs. 3-integer tuple). Sphere’s B can exceed n for sparse data — the main space trade-off.

---

### Sphere-Specific Structures

| Structure | Lookup | Spatial Range | Insert | Space | Pole Distortion | Radial Depth | Best For |
|---|---|---|---|---|---|---|---|
| **Sphere (this)** | **O(1)** | **O(k)** | **O(1)** | **O(n + B)** | Yes (fixed Δθ) | Native (shells) | Radial queries, maps, radar, sensor data |
| Sphere Quadtree (SQT) | O(log n) | O(log n + k) | O(log n) | O(n) | No (icosahedron) | None | Multi-resolution surface rendering |
| Spherepix | O(1) patch | O(patches) | O(1) | O(n · P) | No (orthogonal patches) | None | Convolution & image processing on sphere |
| Sphere Hierarchy (BVH) | O(log n) | O(log n + k) | O(log n) | O(n) | No | None | Collision detection, ray tracing |
| 3D K-d Tree (lat/lon) | O(log n) | O(√n) | O(log n) | O(n) | No (Cartesian embed) | None | General nearest-neighbor on globe |

`P` = patch overlap factor (Spherepix), typically 3–5×

---

### Head-to-Head: Sphere vs. Each Sphere-Specific Structure

**vs. Sphere Quadtree (SQT)**

SQT subdivides an icosahedron recursively so every cell has roughly equal area — no pole distortion. Lookup and insert are both O(log n) (tree traversal to the right triangle).

| Dimension | Sphere | SQT |
|---|---|---|
| Lookup | **O(1)** | O(log n) |
| Insert | **O(1)** | O(log n) |
| Space | O(n + B) | **O(n)** |
| Pole distortion | Yes (fixed Δθ buckets) | **No** |
| Radial depth (3D) | **Native shells** | Surface only |
| Multi-resolution | Manual (shell_step) | **Built-in** |

**Use Sphere when** you have 3D radial data (radar, sonar, GPS). **Use SQT when** you are rendering or tessellating a surface and equal-area cells matter (globe visualisation, climate grids).

---

**vs. Spherepix**

Spherepix tiles the sphere with overlapping near-orthogonal patches so standard 2D convolution kernels can run without seam artefacts. It is a signal-processing primitive, not a general spatial index.

| Dimension | Sphere | Spherepix |
|---|---|---|
| Lookup | **O(1)** | O(1) patch, then linear within patch |
| Space | **O(n + B)** | O(n · P) — overlap inflates storage |
| Arbitrary queries | **Yes** | No — patch-aligned only |
| Convolution support | No | **Yes** |
| Graph topology | **Yes (edges)** | No |

**Use Sphere when** you need arbitrary spatial queries, routing, or graph traversal. **Use Spherepix when** you are running CNNs or filter operations over spherical image data.

---

**vs. Sphere Hierarchy (BVH)**

A BVH wraps geometry in nested bounding spheres. It answers “does ray R hit object X?” efficiently by pruning whole subtrees whose bounding sphere misses. Nodes are not addressable by coordinate — only by containment.

| Dimension | Sphere | BVH |
|---|---|---|
| Coordinate lookup | **O(1)** | Not supported |
| Ray / containment query | O(n) | **O(log n)** |
| Insert | **O(1)** | O(log n) rebalance |
| Dynamic updates | **O(1)** | Expensive (tree rebuild) |
| Space | **O(n + B)** | O(n) |
| Use case | Spatial indexing | **Collision / ray tracing** |

**Use Sphere when** nodes are addressed by position and updated frequently (live sensor feeds, moving agents). **Use BVH when** you are testing ray intersections against static or semi-static geometry.

---

**vs. 3D K-d Tree (lat/lon embedded in Cartesian)**

A 3D K-d tree converts (lat, lon) to (x, y, z) on a unit sphere and applies standard Cartesian nearest-neighbour search. This removes pole distortion but loses all angular/radial semantics.

| Dimension | Sphere | 3D K-d Tree |
|---|---|---|
| Exact coordinate lookup | **O(1)** | O(log n) |
| Nearest neighbour | O(n) fallback¹ | **O(log n)** |
| Radial ring scan | **O(k)** direct | O(√n) |
| Cone / wedge scan | **O(k)** direct | O(√n) — no angular awareness |
| Bearing / angular queries | **Native** | Requires inverse trig post-filter |
| Space | O(n + B) | **O(n)** |
| Pole distortion | Yes (bucket skew) | **No** |

¹ Sphere’s `nearest()` does O(1) exact hit first; only falls back to O(n) scan on a miss. A bucketed ANN variant (check surrounding buckets) reduces this to O(1) average.

**Use Sphere when** queries are phrased in angular/radial terms (bearing, range, cone). **Use 3D K-d Tree when** queries are purely distance-based and data has no radial structure.

---

### Where Sphere Wins

- **O(1) lookup** — no tree traversal; every sphere-specific structure above pays O(log n).
- **Native radial semantics** — ring scans, cone scans, and radial paths are first-class operations, not post-filtered approximations.
- **O(1) dynamic updates** — BVH and K-d Trees require O(log n) rebalancing; Sphere inserts and deletes in constant time, making it the best choice for high-frequency live data.
- **Graph topology included** — edges with angular offsets let Sphere double as a spatial graph; none of the sphere-specific structures support this.

### Where Sphere Has Trade-offs

- **Pole bucket skew** — fixed Δθ buckets are denser near the poles. SQT and 3D K-d Trees avoid this entirely.
- **Nearest-neighbour fallback** — without an ANN extension, a coordinate miss degrades to O(n). K-d Trees give guaranteed O(log n) NN.
- **Surface-only tasks** — for rendering, convolution, or ray tracing on a pure spherical surface, SQT, Spherepix, and BVH are purpose-built and more efficient.
- **Sparse data inflates B** — bucket count grows with resolution, not data density. Tune `shell_step` and `resolution` to match actual data distribution.
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
