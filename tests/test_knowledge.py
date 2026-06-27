"""Tests for the knowledge base: loading, integrity, and query methods."""

from __future__ import annotations

import re

import pytest

from devops_ai_toolkit.knowledge.loader import KnowledgeBase, load_default_knowledge_base
from devops_ai_toolkit.models.enums import Technology
from devops_ai_toolkit.models.knowledge import Signature


@pytest.fixture(scope="module")
def kb() -> KnowledgeBase:
    return load_default_knowledge_base()


class TestLoading:
    def test_kb_loads_and_is_nonempty(self, kb):
        assert len(kb) > 0
        assert len(kb.signatures) == len(kb)

    def test_cached_singleton(self):
        assert load_default_knowledge_base() is load_default_knowledge_base()

    def test_all_signatures_are_signature_models(self, kb):
        assert all(isinstance(s, Signature) for s in kb.signatures)


class TestIntegrity:
    def test_all_ids_unique(self, kb):
        ids = [s.id for s in kb.signatures]
        assert len(ids) == len(set(ids)), "duplicate signature ids in knowledge base"

    def test_all_ids_nonempty(self, kb):
        assert all(s.id.strip() for s in kb.signatures)

    def test_all_regexes_compile(self, kb):
        for sig in kb.signatures:
            for pattern in [*sig.match.any_of, *sig.match.all_of]:
                re.compile(pattern)  # must not raise

    def test_every_signature_has_a_match_pattern(self, kb):
        for sig in kb.signatures:
            assert sig.match.any_of or sig.match.all_of, f"{sig.id} has no patterns"

    def test_every_signature_revalidates(self, kb):
        # Round-trip through the schema again to assert each entry is fully valid.
        for sig in kb.signatures:
            Signature.model_validate(sig.model_dump())

    def test_weights_in_range(self, kb):
        for sig in kb.signatures:
            assert 0.0 <= sig.match.weight <= 1.0

    def test_root_cause_confidences_in_range(self, kb):
        for sig in kb.signatures:
            for cause in sig.root_causes:
                assert 0.0 <= cause.confidence <= 1.0


class TestQueries:
    def test_get_known_id(self, kb):
        sig = kb.get("k8s.crashloopbackoff")
        assert sig is not None
        assert sig.technology is Technology.KUBERNETES

    def test_get_unknown_id_returns_none(self, kb):
        assert kb.get("does.not.exist") is None

    def test_for_technology(self, kb):
        k8s = kb.for_technology(Technology.KUBERNETES)
        assert k8s, "expected at least one kubernetes signature"
        assert all(s.technology is Technology.KUBERNETES for s in k8s)

    def test_for_technology_empty(self, kb):
        # A technology unlikely to have signatures returns an empty list, not error.
        result = kb.for_technology(Technology.VMWARE)
        assert isinstance(result, list)

    def test_candidates_unknown_returns_all(self, kb):
        assert len(kb.candidates(None)) == len(kb)
        assert len(kb.candidates(Technology.UNKNOWN)) == len(kb)

    def test_candidates_scoped(self, kb):
        scoped = kb.candidates(Technology.KUBERNETES)
        assert all(s.technology is Technology.KUBERNETES for s in scoped)

    def test_candidates_unknown_tech_falls_back_to_all(self, kb):
        # A technology with no signatures should fall back to evaluating all.
        empty_tech = Technology.LINSTOR
        if not kb.for_technology(empty_tech):
            assert len(kb.candidates(empty_tech)) == len(kb)

    def test_search_finds_by_title(self, kb):
        hits = kb.search("CrashLoopBackOff")
        assert any(s.id == "k8s.crashloopbackoff" for s in hits)

    def test_search_case_insensitive(self, kb):
        assert kb.search("crashloopbackoff") == kb.search("CRASHLOOPBACKOFF")

    def test_search_no_match(self, kb):
        assert kb.search("zzz-nonexistent-query-zzz") == []

    def test_technologies_sorted_and_nonempty(self, kb):
        techs = kb.technologies
        assert techs
        assert techs == sorted(techs, key=str)


class TestDuplicateGuard:
    def test_duplicate_ids_rejected(self):
        sig = load_default_knowledge_base().get("k8s.crashloopbackoff")
        assert sig is not None
        with pytest.raises(ValueError, match="duplicate signature id"):
            KnowledgeBase([sig, sig])
