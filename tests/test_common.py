import numpy as np
import pandas as pd

from kulturne_nagrade.analysis.common import bh_fdr, kaplan_meier, km_at, wilson


def test_wilson_contains_point_estimate():
    lo, hi = wilson(30, 100)
    assert lo < 0.3 < hi
    assert 0.2 < lo and hi < 0.4


def test_bh_fdr_monotone_and_bounded():
    p = pd.Series([0.01, 0.04, 0.03, 0.5], index=list("abcd"))
    q = bh_fdr(p)
    assert (q >= p).all() and (q <= 1).all()
    assert q["a"] == 0.04  # 0.01 * 4 / 1


def test_kaplan_meier_matches_hand_calculation():
    # 4 subjects: events at t=1 and t=3, censored at t=2 and t=4.
    km = kaplan_meier(pd.Series([1, 2, 3, 4]), pd.Series([True, False, True, False]))
    assert np.isclose(km_at(km, 1), 0.25)  # S = 3/4
    assert np.isclose(km_at(km, 3), 1 - 0.75 * 0.5)  # S = 3/4 * 1/2
    assert np.isclose(km_at(km, 0), 0.0)
