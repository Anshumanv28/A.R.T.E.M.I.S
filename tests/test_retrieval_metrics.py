from artemis.eval.retrieval_metrics import mean_reciprocal_rank, reciprocal_rank, recall_at_k


def test_recall_at_k_full_hit():
    assert recall_at_k(["a", "b", "c"], {"a", "c"}, k=3) == 1.0


def test_recall_at_k_partial_hit_respects_k():
    assert recall_at_k(["a", "b", "c"], {"a", "z"}, k=1) == 0.5


def test_recall_at_k_no_relevant_docs_is_zero():
    assert recall_at_k(["a", "b"], set(), k=5) == 0.0


def test_recall_at_k_no_overlap_is_zero():
    assert recall_at_k(["a", "b"], {"z"}, k=5) == 0.0


def test_reciprocal_rank_first_position():
    assert reciprocal_rank(["a", "b", "c"], {"a"}) == 1.0


def test_reciprocal_rank_third_position():
    assert reciprocal_rank(["x", "y", "a"], {"a"}) == 1 / 3


def test_reciprocal_rank_not_found_is_zero():
    assert reciprocal_rank(["x", "y"], {"a"}) == 0.0


def test_mean_reciprocal_rank_averages_across_queries():
    ranked = [["a", "b"], ["x", "a"]]
    relevant = [{"a"}, {"a"}]
    assert mean_reciprocal_rank(ranked, relevant) == (1.0 + 0.5) / 2


def test_mean_reciprocal_rank_empty_input_is_zero():
    assert mean_reciprocal_rank([], []) == 0.0
