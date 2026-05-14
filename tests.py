# -*- coding: utf-8 -*-
"""
Unit tests for the Sphere data structure.
Run with:  python3 tests.py  (or  python3 -m pytest tests.py -v)
"""
import math
import unittest
from sphere import Sphere, SphereNode


class TestSphereNode(unittest.TestCase):

    def test_theta_wrap(self):
        n = SphereNode(r=1, theta=370, phi=0, value=None)
        self.assertAlmostEqual(n.theta, 10.0)

    def test_phi_out_of_range(self):
        with self.assertRaises(ValueError):
            SphereNode(r=1, theta=0, phi=100, value=None)

    def test_cartesian_north(self):
        n = SphereNode(r=1, theta=0, phi=90, value=None)
        x, y, z = n.cartesian()
        self.assertAlmostEqual(x, 0, places=5)
        self.assertAlmostEqual(y, 0, places=5)
        self.assertAlmostEqual(z, 1, places=5)

    def test_cartesian_equator(self):
        n = SphereNode(r=1, theta=0, phi=0, value=None)
        x, y, z = n.cartesian()
        self.assertAlmostEqual(x, 1, places=5)
        self.assertAlmostEqual(y, 0, places=5)
        self.assertAlmostEqual(z, 0, places=5)

    def test_distance_to_same(self):
        n = SphereNode(r=5, theta=45, phi=30, value=None)
        self.assertAlmostEqual(n.distance_to(n), 0.0)

    def test_angular_distance_poles(self):
        north = SphereNode(r=1, theta=0, phi=90, value=None)
        south = SphereNode(r=1, theta=0, phi=-90, value=None)
        self.assertAlmostEqual(north.angular_distance(south), 180.0, places=5)

    def test_angular_distance_same(self):
        n = SphereNode(r=1, theta=45, phi=30, value=None)
        self.assertAlmostEqual(n.angular_distance(n), 0.0, places=5)

    def test_bearing_east(self):
        # From equator (phi=0), moving from theta=0 to theta=90 is eastward
        a = SphereNode(r=1, theta=0,  phi=0, value=None)
        b = SphereNode(r=1, theta=90, phi=0, value=None)
        bearing = a.bearing_to(b)
        self.assertAlmostEqual(bearing % 360, 90.0, places=1)


class TestSphereInsertLookup(unittest.TestCase):

    def setUp(self):
        self.s = Sphere(resolution=1.0, shell_step=1.0)

    def test_insert_and_lookup(self):
        self.s.insert(r=5, theta=45, value="alpha")
        node = self.s.lookup(r=5, theta=45)
        self.assertIsNotNone(node)
        self.assertEqual(node.value, "alpha")

    def test_lookup_miss(self):
        result = self.s.lookup(r=99, theta=99)
        self.assertIsNone(result)

    def test_theta_wrap_lookup(self):
        self.s.insert(r=3, theta=360, value="wrap")
        node = self.s.lookup(r=3, theta=0)
        self.assertIsNotNone(node)

    def test_delete(self):
        self.s.insert(r=2, theta=10, value="del")
        self.assertTrue(self.s.delete(r=2, theta=10))
        self.assertIsNone(self.s.lookup(r=2, theta=10))

    def test_delete_cleans_edges(self):
        a = self.s.insert(r=1, theta=0, value="a")
        b = self.s.insert(r=2, theta=0, value="b")
        self.s.connect(a, b)
        self.s.delete(r=2, theta=0)
        self.assertEqual(len(a.edges), 0)

    def test_len(self):
        self.s.insert(r=1, theta=0, value="x")
        self.s.insert(r=2, theta=90, value="y")
        self.assertEqual(len(self.s), 2)

    def test_contains(self):
        n = self.s.insert(r=3, theta=60, value="c")
        self.assertIn(n, self.s)

    def test_invalid_resolution(self):
        with self.assertRaises(ValueError):
            Sphere(resolution=0)

    def test_3d_insert_lookup(self):
        self.s.insert(r=10, theta=30, phi=45, value="3d")
        node = self.s.lookup(r=10, theta=30, phi=45)
        self.assertIsNotNone(node)
        self.assertEqual(node.value, "3d")


class TestSphereScan(unittest.TestCase):

    def setUp(self):
        self.s = Sphere(resolution=1.0, shell_step=100)
        self.north = self.s.insert(r=500,  theta=0,   value="north")
        self.east  = self.s.insert(r=500,  theta=90,  value="east")
        self.ne    = self.s.insert(r=1000, theta=45,  value="ne")
        self.west  = self.s.insert(r=200,  theta=270, value="west")

    def test_ring_scan(self):
        ring = self.s.ring_scan(r=500)
        values = {n.value for n in ring}
        self.assertIn("north", values)
        self.assertIn("east", values)
        self.assertNotIn("ne", values)

    def test_cone_scan_quadrant(self):
        ne_nodes = self.s.cone_scan(theta_min=0, theta_max=90)
        values = {n.value for n in ne_nodes}
        self.assertIn("north", values)
        self.assertIn("east", values)
        self.assertIn("ne", values)
        self.assertNotIn("west", values)

    def test_cone_scan_wrap_around(self):
        # 350°–10° should hit north (0°)
        wrap = self.s.cone_scan(theta_min=350, theta_max=10)
        values = {n.value for n in wrap}
        self.assertIn("north", values)

    def test_range_query(self):
        nearby = self.s.range_query(r_min=100, r_max=600, theta_min=0, theta_max=360)
        values = {n.value for n in nearby}
        self.assertIn("north", values)
        self.assertIn("east", values)
        self.assertIn("west", values)
        self.assertNotIn("ne", values)

    def test_cone_scan_r_max(self):
        close = self.s.cone_scan(theta_min=0, theta_max=360, r_max=500)
        self.assertNotIn(self.ne, close)

    def test_radial_path(self):
        s = Sphere(resolution=1.0, shell_step=100)
        s.insert(r=100, theta=0, value="r1")
        s.insert(r=200, theta=0, value="r2")
        s.insert(r=300, theta=0, value="r3")
        path = s.radial_path(theta=0, r_max=300)
        values = [n.value for n in path]
        self.assertEqual(values[0], "origin")
        self.assertIn("r1", values)
        self.assertIn("r2", values)
        self.assertIn("r3", values)

    def test_nearest_exact(self):
        n = self.s.nearest(r=500, theta=0)
        self.assertEqual(n.value, "north")

    def test_nearest_approximate(self):
        n = self.s.nearest(r=490, theta=3)
        self.assertEqual(n.value, "north")


class TestSphereEdges(unittest.TestCase):

    def setUp(self):
        self.s = Sphere(resolution=1.0, shell_step=1.0)
        self.a = self.s.insert(r=1, theta=0,  value="a")
        self.b = self.s.insert(r=1, theta=90, value="b")

    def test_connect_bidirectional(self):
        self.s.connect(self.a, self.b)
        neighbors_a = [n for n, _ in self.a.edges]
        neighbors_b = [n for n, _ in self.b.edges]
        self.assertIn(self.b, neighbors_a)
        self.assertIn(self.a, neighbors_b)

    def test_connect_directed(self):
        self.s.connect(self.a, self.b, directed=True)
        neighbors_a = [n for n, _ in self.a.edges]
        neighbors_b = [n for n, _ in self.b.edges]
        self.assertIn(self.b, neighbors_a)
        self.assertNotIn(self.a, neighbors_b)

    def test_disconnect(self):
        self.s.connect(self.a, self.b)
        self.s.disconnect(self.a, self.b)
        self.assertEqual(len(self.a.edges), 0)
        self.assertEqual(len(self.b.edges), 0)

    def test_delta_theta_stored(self):
        self.s.connect(self.a, self.b)
        _, delta = self.a.edges[0]
        self.assertAlmostEqual(delta, 90.0)

    def test_neighbors_lookup(self):
        self.s.insert(r=1, theta=45, value="c")
        neighbor = self.s.neighbors(self.a, delta_theta=45)
        self.assertIsNotNone(neighbor)
        self.assertEqual(neighbor.value, "c")


class TestSphereTraversal(unittest.TestCase):

    def setUp(self):
        self.s = Sphere(resolution=45.0, shell_step=1.0)
        self.a = self.s.insert(r=1, theta=0,  value="A")
        self.b = self.s.insert(r=1, theta=90, value="B")
        self.c = self.s.insert(r=2, theta=0,  value="C")
        self.s.connect(self.s.center, self.a)
        self.s.connect(self.s.center, self.b)
        self.s.connect(self.a, self.c)

    def test_bfs_visits_all(self):
        visited = list(self.s.bfs(self.s.center))
        values = {n.value for n in visited}
        self.assertIn("origin", values)
        self.assertIn("A", values)
        self.assertIn("B", values)
        self.assertIn("C", values)

    def test_dfs_visits_all(self):
        visited = list(self.s.dfs(self.s.center))
        values = {n.value for n in visited}
        self.assertIn("origin", values)
        self.assertIn("A", values)
        self.assertIn("B", values)
        self.assertIn("C", values)

    def test_shortest_path_hops(self):
        path = self.s.shortest_path(self.s.center, self.c, weight="hops")
        self.assertIsNotNone(path)
        self.assertEqual(path[0].value, "origin")
        self.assertEqual(path[-1].value, "C")
        self.assertEqual(len(path), 3)  # origin → A → C

    def test_shortest_path_unreachable(self):
        isolated = self.s.insert(r=5, theta=180, value="island")
        path = self.s.shortest_path(self.s.center, isolated, weight="hops")
        self.assertIsNone(path)

    def test_shortest_path_distance(self):
        path = self.s.shortest_path(self.s.center, self.c, weight="distance")
        self.assertIsNotNone(path)
        self.assertEqual(path[-1].value, "C")


class TestSphereStats(unittest.TestCase):

    def test_shells(self):
        s = Sphere(shell_step=10)
        s.insert(r=10, theta=0,  value="a")
        s.insert(r=10, theta=90, value="b")
        s.insert(r=20, theta=0,  value="c")
        self.assertEqual(s.shells(), [10.0, 20.0])

    def test_stats_dict(self):
        s = Sphere()
        s.insert(r=1, theta=0, value="x")
        stats = s.stats()
        self.assertIn("nodes", stats)
        self.assertIn("shells", stats)
        self.assertIn("edges", stats)


if __name__ == "__main__":
    unittest.main(verbosity=2)
