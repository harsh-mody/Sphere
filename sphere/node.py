from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SphereNode:
    r: float
    theta: float   # azimuth [0, 360)
    phi: float     # elevation [-90, 90]
    value: Any
    edges: list[tuple[SphereNode, float]] = field(default_factory=list, repr=False)

    def __post_init__(self):
        self.theta = self.theta % 360
        if not (-90 <= self.phi <= 90):
            raise ValueError(f"phi must be in [-90, 90], got {self.phi}")

    def cartesian(self) -> tuple[float, float, float]:
        """(r, θ, φ) → (x, y, z)"""
        phi_r = math.radians(self.phi)
        theta_r = math.radians(self.theta)
        x = self.r * math.cos(phi_r) * math.cos(theta_r)
        y = self.r * math.cos(phi_r) * math.sin(theta_r)
        z = self.r * math.sin(phi_r)
        return x, y, z

    def distance_to(self, other: SphereNode) -> float:
        """Euclidean distance between two nodes via Cartesian conversion."""
        x1, y1, z1 = self.cartesian()
        x2, y2, z2 = other.cartesian()
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

    def angular_distance(self, other: SphereNode) -> float:
        """Great-circle angular distance in degrees."""
        phi1 = math.radians(self.phi)
        phi2 = math.radians(other.phi)
        d_theta = math.radians(other.theta - self.theta)
        cos_angle = (
            math.sin(phi1) * math.sin(phi2)
            + math.cos(phi1) * math.cos(phi2) * math.cos(d_theta)
        )
        # Clamp to [-1, 1] to guard against float rounding
        return math.degrees(math.acos(max(-1.0, min(1.0, cos_angle))))

    def bearing_to(self, other: SphereNode) -> float:
        """Azimuth bearing from this node to another, in degrees [0, 360)."""
        d_theta = math.radians(other.theta - self.theta)
        phi1 = math.radians(self.phi)
        phi2 = math.radians(other.phi)
        x = math.sin(d_theta) * math.cos(phi2)
        y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_theta)
        return math.degrees(math.atan2(x, y)) % 360

    def __repr__(self) -> str:
        return f"SphereNode(r={self.r}, θ={self.theta}°, φ={self.phi}°, value={self.value!r})"

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other
