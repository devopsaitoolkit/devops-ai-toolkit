"""Tests for the SignatureMatcher: matching, ranking, evidence, no false hits."""

from __future__ import annotations

import pytest

from devops_ai_toolkit.detectors.matcher import SignatureMatcher
from devops_ai_toolkit.knowledge.loader import load_default_knowledge_base
from devops_ai_toolkit.models.enums import Technology


@pytest.fixture(scope="module")
def matcher() -> SignatureMatcher:
    return SignatureMatcher(load_default_knowledge_base())


def _ids(matches) -> list[str]:
    return [m.signature.id for m in matches]


class TestKnownPatterns:
    def test_crashloopbackoff(self, matcher, crashloop_log):
        matches = matcher.match(crashloop_log, Technology.KUBERNETES)
        assert "k8s.crashloopbackoff" in _ids(matches)

    def test_imagepullbackoff(self, matcher, imagepull_log):
        matches = matcher.match(imagepull_log, Technology.KUBERNETES)
        assert "k8s.imagepullbackoff" in _ids(matches)

    def test_oomkilled(self, matcher, oomkilled_log):
        matches = matcher.match(oomkilled_log, Technology.KUBERNETES)
        assert "k8s.oomkilled" in _ids(matches)

    def test_terraform_state_lock(self, matcher, terraform_state_lock_log):
        matches = matcher.match(terraform_state_lock_log, Technology.TERRAFORM)
        assert "terraform.state_lock" in _ids(matches)

    def test_match_without_technology_hint(self, matcher, crashloop_log):
        # No technology hint -> evaluate everything; should still find the pattern.
        matches = matcher.match(crashloop_log)
        assert "k8s.crashloopbackoff" in _ids(matches)


class TestEvidenceAndScore:
    def test_evidence_captured(self, matcher, crashloop_log):
        match = next(
            m for m in matcher.match(crashloop_log) if m.signature.id == "k8s.crashloopbackoff"
        )
        assert match.evidence
        assert any("CrashLoopBackOff" in e for e in match.evidence)

    def test_score_within_bounds(self, matcher, crashloop_log):
        for m in matcher.match(crashloop_log):
            assert 0.0 <= m.score <= 1.0

    def test_multiple_signals_boosts_score(self, matcher):
        # Two distinct any_of patterns for imagepullbackoff should outscore one.
        single = matcher.match("ImagePullBackOff", Technology.KUBERNETES)
        double = matcher.match(
            "ImagePullBackOff\nErrImagePull\npull access denied", Technology.KUBERNETES
        )
        s_single = next(m.score for m in single if m.signature.id == "k8s.imagepullbackoff")
        s_double = next(m.score for m in double if m.signature.id == "k8s.imagepullbackoff")
        assert s_double >= s_single


class TestRanking:
    def test_matches_sorted_descending(self, matcher):
        text = "CrashLoopBackOff\nOOMKilled\nImagePullBackOff\nexit code 137"
        matches = matcher.match(text)
        scores = [m.score for m in matches]
        assert scores == sorted(scores, reverse=True)

    def test_limit_respected(self, matcher):
        text = "CrashLoopBackOff\nOOMKilled\nImagePullBackOff"
        assert len(matcher.match(text, limit=1)) <= 1
        assert len(matcher.match(text, limit=2)) <= 2


class TestNoFalseMatches:
    def test_empty_text(self, matcher):
        assert matcher.match("") == []

    def test_whitespace_only(self, matcher):
        assert matcher.match("   \n\t  ") == []

    def test_benign_text(self, matcher, benign_text):
        assert matcher.match(benign_text) == []
