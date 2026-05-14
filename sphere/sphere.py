from __future__ import annotations
import math
from typing import Any, Iterator, Optional

from .node import SphereNode


class Sphere:
    """
    Polar-coordinate graph rooted at a center node.

    Nodes are addressed by (r, theta, phi) and stored in a bucketed hash
    index for O(1) insert/lookup. Edges between nodes carry angular offsets
    so both coordinate-addressed and topology-addressed traversal work.

    Args:
        resolution:  Angular bucket size in degrees. Smaller = more precise
                     but sparser index.
        shell_step:  Radial bucket size (same units as r). Controls how
                     thick each distance shell is.
    """

    def __init__(self, resolution: float = 1.0, shell_step: float = 1.0):
        if resolution <= 0 or shell_step <= 0:
            raise ValueError("resolution and shell_step must be positive")
        self.resolution = resolution
        self.shell_step = shell_step
        self.center = SphereNode(r=0.0, theta=0.0, phi=0.0, value="origin")
        self._index: dict[tuple[int, int, int], SphereNode] = {}

    # ------------------------------------------------------------------
    # Coordinate key
    # ------------------------------------------------------------------

    def _key(self, r: float, theta: float, phi: float) -> tuple[int, int, int]:
        return (
            round(r / self.shell_step),
            round((theta % 360) / self.resolution),
            round((phi + 90) / self.resolution),
        )

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def insert(
        self,
        r: float,
        theta: float,
        phi: float = 0.0,
        value: Any = None,
    ) -> SphereNode:
        """Insert a node. O(1) average. Returns the new SphereNode."""
        node = SphereNode(r=r, theta=theta, phi=phi, value=value)
        self._index[self._key(r, theta, phi)] = node
        return node

    def lookup(
        self, r: float, theta: float, phi: float = 0.0
    ) -> Optional[SphereNode]:
        """Exact coordinate lookup. O(1) average."""
        return self._index.get(self._key(r, theta, phi))

    def delete(self, r: float, theta: float, phi: float = 0.0) -> bool:
        """Remove node and clean up back-edges. O(degree) for edge cleanup."""
        node = self._index.pop(self._key(r, theta, phi), None)
        if node is None:
            return False
        for neighbor, _ in node.edges:
            neighbor.edges = [(n, d) for n, d in neighbor.edges if n is not node]
        return True

    def delete_node(self, node: SphereNode) -> bool:
        """Remove a node by reference instead of coordinates."""
        return self.delete(node.r, node.theta, node.phi)

    # ------------------------------------------------------------------
    # Edge management
    # ------------------------------------------------------------------

    def connect(
        self,
        node_a: SphereNode,
        node_b: SphereNode,
        directed: bool = False,
    ) -> None:
        """
        Connect two nodes. Stores Δθ on each edge so angular traversal
        is a direct attribute read, not a subtraction at query time.
        """
        delta = (node_b.theta - node_a.theta) % 360
        node_a.edges.append((node_b, delta))
        if not directed:
            node_b.edges.append((node_a, (360 - delta) % 360))

    def disconnect(self, node_a: SphereNode, node_b: SphereNode) -> None:
        """Remove edges between two nodes."""
        node_a.edges = [(n, d) for n, d in node_a.edges if n is not node_b]
        node_b.edges = [(n, d) for n, d in node_b.edges if n is not node_a]

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

    def neighbors(
        self,
        node: SphereNode,
        delta_theta: float,
        delta_phi: float = 0.0,
        delta_r: float = 0.0,
    ) -> Optional[SphereNode]:
        """
        Coordinate-addressed neighbor lookup.
        delta_theta / delta_phi / delta_r are angular/radial offsets.
        O(1) average.
        """
        return self.lookup(
            node.r + delta_r,
            node.theta + delta_theta,
            node.phi + delta_phi,
        )

    def ring_scan(self, r: float) -> list[SphereNode]:
        """All nodes on the shell at radius r. O(k)."""
        r_bucket = round(r / self.shell_step)
        return [n for (rb, _, _), n in self._index.items() if rb == r_bucket]

    def cone_scan(
        self,
        theta_min: float,
        theta_max: float,
        phi_min: float = -90.0,
        phi_max: float = 90.0,
        r_max: Optional[float] = None,
        r_min: float = 0.0,
    ) -> list[SphereNode]:
        """
        All nodes within an angular cone (wedge). Handles 0°/360° wrap.
        O(k).
        """
        full_circle = (theta_max - theta_min) >= 360
        tm = theta_min % 360
        tx = theta_max % 360
        results = []
        for node in self._index.values():
            t = node.theta
            if full_circle:
                in_theta = True
            elif tm > tx:  # wrap-around case (e.g. 350°–10°)
                in_theta = t >= tm or t <= tx
            else:
                in_theta = tm <= t <= tx
            if (
                in_theta
                and phi_min <= node.phi <= phi_max
                and r_min <= node.r
                and (r_max is None or node.r <= r_max)
            ):
                results.append(node)
        return results

    def range_query(
        self,
        r_min: float,
        r_max: float,
        theta_min: float,
        theta_max: float,
        phi_min: float = -90.0,
        phi_max: float = 90.0,
    ) -> list[SphereNode]:
        """Nodes inside a spherical wedge bounded by r, θ, φ ranges. O(k)."""
        return self.cone_scan(
            theta_min=theta_min,
            theta_max=theta_max,
            phi_min=phi_min,
            phi_max=phi_max,
            r_min=r_min,
            r_max=r_max,
        )

    def radial_path(
        self,
        theta: float,
        phi: float = 0.0,
        r_max: Optional[float] = None,
    ) -> list[SphereNode]:
        """
        Walk outward from center along bearing (theta, phi), collecting every
        node that exists on each shell. O(shells).
        """
        limit = r_max
        if limit is None:
            limit = max((n.r for n in self._index.values()), default=0.0)
        path: list[SphereNode] = [self.center]
        r = self.shell_step
        while r <= limit + 1e-9:
            node = self.lookup(r, theta, phi)
            if node:
                path.append(node)
            r += self.shell_step
        return path

    def nearest(
        self, r: float, theta: float, phi: float = 0.0
    ) -> Optional[SphereNode]:
        """
        Closest node to the given coordinates. Tries O(1) exact hit first,
        falls back to brute-force O(n) scan — use sparingly on large graphs.
        """
        exact = self.lookup(r, theta, phi)
        if exact:
            return exact
        target = SphereNode(r=r, theta=theta, phi=phi, value=None)
        best: Optional[SphereNode] = None
        best_dist = float("inf")
        for node in self._index.values():
            d = node.distance_to(target)
            if d < best_dist:
                best, best_dist = node, d
        return best

    def bfs(self, start: SphereNode) -> Iterator[SphereNode]:
        """Breadth-first traversal over topology edges from start."""
        visited: set[int] = {id(start)}
        queue = [start]
        while queue:
            current = queue.pop(0)
            yield current
            for neighbor, _ in current.edges:
                if id(neighbor) not in visited:
                    visited.add(id(neighbor))
                    queue.append(neighbor)

    def dfs(self, start: SphereNode) -> Iterator[SphereNode]:
        """Depth-first traversal over topology edges from start."""
        visited: set[int] = set()
        stack = [start]
        while stack:
            current = stack.pop()
            if id(current) in visited:
                continue
            visited.add(id(current))
            yield current
            for neighbor, _ in current.edges:
                if id(neighbor) not in visited:
                    stack.append(neighbor)

    def shortest_path(
        self,
        start: SphereNode,
        goal: SphereNode,
        weight: str = "distance",
    ) -> Optional[list[SphereNode]]:
        """
        Dijkstra shortest path over topology edges.
        weight='distance' uses Euclidean distance; 'hops' counts edges.
        Returns list of nodes from start to goal, or None if unreachable.
        """
        import heapq

        dist: dict[int, float] = {id(start): 0.0}
        prev: dict[int, Optional[SphereNode]] = {id(start): None}
        heap: list[tuple[float, int, SphereNode]] = [(0.0, id(start), start)]

        while heap:
            cost, _, current = heapq.heappop(heap)
            if current is goal:
                path: list[SphereNode] = []
                node: Optional[SphereNode] = goal
                while node is not None:
                    path.append(node)
                    node = prev[id(node)]
                return path[::-1]

            if cost > dist.get(id(current), float("inf")):
                continue

            for neighbor, _ in current.edges:
                edge_cost = 1.0 if weight == "hops" else current.distance_to(neighbor)
                new_cost = cost + edge_cost
                if new_cost < dist.get(id(neighbor), float("inf")):
                    dist[id(neighbor)] = new_cost
                    prev[id(neighbor)] = current
                    heapq.heappush(heap, (new_cost, id(neighbor), neighbor))

        return None

    # ------------------------------------------------------------------
    # Stats / helpers
    # ------------------------------------------------------------------

    def shells(self) -> list[float]:
        """Sorted list of distinct radii present in the index."""
        return sorted({n.r for n in self._index.values()})

    def all_nodes(self) -> list[SphereNode]:
        """All nodes in insertion-arbitrary order (does not include center)."""
        return list(self._index.values())

    def stats(self) -> dict:
        nodes = self.all_nodes()
        return {
            "nodes": len(nodes),
            "shells": len(self.shells()),
            "edges": sum(len(n.edges) for n in nodes) // 2,
            "resolution_deg": self.resolution,
            "shell_step": self.shell_step,
        }

    def __len__(self) -> int:
        return len(self._index)

    def __contains__(self, node: SphereNode) -> bool:
        return self._key(node.r, node.theta, node.phi) in self._index

    def __repr__(self) -> str:
        return (
            f"Sphere(nodes={len(self)}, resolution={self.resolution}°,"
            f" shell_step={self.shell_step})"
        )
