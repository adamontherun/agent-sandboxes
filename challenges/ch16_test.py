"""Tests for Chapter 16 challenge: a malware analysis pipeline."""

import hashlib

import pytest
from ch16 import AnalysisPipeline, Evidence, NetworkPolicy


class TestNetworkPolicy:
    def test_attempt_returns_false(self):
        policy = NetworkPolicy()
        assert policy.attempt_connection("192.0.2.1:443") is False

    def test_attempt_records_attempt(self):
        policy = NetworkPolicy()
        policy.attempt_connection("10.0.0.1:80")
        assert len(policy.attempts) == 1
        assert policy.attempts[0].destination == "10.0.0.1:80"
        assert policy.attempts[0].blocked is True

    def test_multiple_attempts_recorded(self):
        policy = NetworkPolicy()
        policy.attempt_connection("a.example:443")
        policy.attempt_connection("b.example:80")
        assert len(policy.attempts) == 2


class TestWriteFile:
    def test_stores_content(self):
        pipeline = AnalysisPipeline("s1", lambda: None)
        pipeline.write_file("payload.bin", b"data")
        assert pipeline.files == {"payload.bin": b"data"}

    def test_overwrites_existing(self):
        pipeline = AnalysisPipeline("s1", lambda: None)
        pipeline.write_file("f.txt", b"old")
        pipeline.write_file("f.txt", b"new")
        assert pipeline.files["f.txt"] == b"new"


class TestComputeHash:
    def test_empty_files(self):
        pipeline = AnalysisPipeline("s1", lambda: None)
        expected = hashlib.sha256(b"").hexdigest()
        assert pipeline.compute_hash() == expected

    def test_single_file(self):
        pipeline = AnalysisPipeline("s1", lambda: None)
        pipeline.write_file("a.txt", b"hello")
        expected = hashlib.sha256(b"hello").hexdigest()
        assert pipeline.compute_hash() == expected

    def test_multiple_files_sorted_order(self):
        pipeline = AnalysisPipeline("s1", lambda: None)
        pipeline.write_file("b.txt", b"second")
        pipeline.write_file("a.txt", b"first")
        expected = hashlib.sha256(b"first" + b"second").hexdigest()
        assert pipeline.compute_hash() == expected


class TestRunSuccess:
    def test_returns_evidence(self):
        def sample(p):
            p.write_file("marker.txt", b"found")
            p.network.attempt_connection("192.0.2.1:443")

        pipeline = AnalysisPipeline("sample-001", lambda: None)
        evidence = pipeline.run(sample)
        assert isinstance(evidence, Evidence)
        assert evidence.sample_id == "sample-001"

    def test_evidence_files_created(self):
        def sample(p):
            p.write_file("b.txt", b"B")
            p.write_file("a.txt", b"A")

        pipeline = AnalysisPipeline("s1", lambda: None)
        evidence = pipeline.run(sample)
        assert evidence.files_created == ["a.txt", "b.txt"]

    def test_evidence_network_attempts(self):
        def sample(p):
            p.network.attempt_connection("evil.example:443")

        pipeline = AnalysisPipeline("s1", lambda: None)
        evidence = pipeline.run(sample)
        assert len(evidence.network_attempts) == 1
        assert evidence.network_attempts[0].destination == "evil.example:443"

    def test_evidence_hash_matches_compute(self):
        def sample(p):
            p.write_file("x.bin", b"payload")

        pipeline = AnalysisPipeline("s1", lambda: None)
        evidence = pipeline.run(sample)
        assert evidence.artifact_hash == hashlib.sha256(b"payload").hexdigest()

    def test_teardown_called_on_success(self):
        called = []

        def sample(p):
            p.write_file("f.txt", b"x")

        pipeline = AnalysisPipeline("s1", lambda: called.append(True))
        evidence = pipeline.run(sample)
        assert called == [True]
        assert evidence.teardown_called is True


class TestRunSampleRaises:
    def test_teardown_called_on_exception(self):
        called = []

        def bad_sample(p):
            raise RuntimeError("crash")

        pipeline = AnalysisPipeline("s1", lambda: called.append(True))
        with pytest.raises(RuntimeError, match="crash"):
            pipeline.run(bad_sample)
        assert called == [True]

    def test_torn_down_flag_set_on_exception(self):
        def bad_sample(p):
            raise ValueError("boom")

        pipeline = AnalysisPipeline("s1", lambda: None)
        with pytest.raises(ValueError):
            pipeline.run(bad_sample)
        assert pipeline._torn_down is True
