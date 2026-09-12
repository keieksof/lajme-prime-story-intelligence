from __future__ import annotations

from types import SimpleNamespace

from app.learning.adaptive_ranker import BASE_WEIGHTS, derive_adaptive_weights


class FakeSession:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, _query):
        return SimpleNamespace(all=lambda: self.rows)


def test_adaptive_weights_do_not_change_without_enough_samples():
    session = FakeSession([("semantic_similarity", 1.0, 4)])
    result = derive_adaptive_weights(session, minimum_samples=5)
    assert result.values == BASE_WEIGHTS
    assert result.samples["semantic_similarity"] == 4


def test_adaptive_weights_move_with_sustained_outcome():
    session = FakeSession([("semantic_similarity", 1.0, 10)])
    result = derive_adaptive_weights(session, minimum_samples=5)
    assert result.values["semantic_similarity"] > BASE_WEIGHTS["semantic_similarity"]
