import numpy as np
import pytest
from memory import HD, E8, Leech, rhc_encode, rhc_bind, rhc_bundle

def test_hd_sim():
    v1 = HD.random()
    v2 = HD.random()
    sim = HD.sim(v1, v2)
    assert -1 <= sim <= 1

def test_e8_closest_point():
    vec = np.array([0.6]*8)
    point = E8.closest_point(vec)
    assert np.allclose(point, np.ones(8))

def test_rhc_encode():
    val = 0.5
    vec = rhc_encode(val)
    assert vec.dtype == np.int8
    assert vec.shape == (np.sum([3,5,7,11,13,17,19,23]),)
