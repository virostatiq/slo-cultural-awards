"""Invariants of the typed awards graph (kulturne_nagrade.graph)."""

import pytest

from kulturne_nagrade import frames, graph


@pytest.fixture(scope="module")
def G():
    return graph.build()


def test_role_edges_match_the_data(G):
    roles = frames.roles(entity_types=None)
    sit = frames.jury_sittings(entity_types=None)
    counts = {"winner": 0, "jury": 0}
    for _, _, d in G.edges(data=True):
        if d["kind"] == "role":
            counts[d["role"]] += d["count"]
    assert counts["winner"] == (roles["role"] == "winner").sum()
    assert counts["jury"] == len(sit)


def test_co_jury_pairs_stored_once(G):
    pairs = [(u, v) for u, v, d in G.edges(data=True) if d["kind"] == "co_jury"]
    assert all(u < v for u, v in pairs)
    assert len(pairs) == len(set(pairs))


def test_no_self_judging(G):
    assert not any(u == v for u, v, d in G.edges(data=True) if d["kind"] == "judged")


def test_every_node_has_a_display_field(G):
    fields = set(graph.FIELD.values())
    assert all(d["field"] in fields for _, d in G.nodes(data=True))
