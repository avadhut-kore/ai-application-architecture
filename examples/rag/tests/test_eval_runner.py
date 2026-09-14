"""Unit tests for Gate D RAG Evaluation Runner."""

from __future__ import annotations

import asyncio
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
for p in (REPO_ROOT / "building-blocks" / "python", Path(__file__).resolve().parent.parent):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from eval_runner import (
    EvalScenario,
    RAGEvalSummary,
    evaluate_single_scenario,
    load_dataset,
    print_report,
    run_evaluation,
    save_report,
)
from rag.citation_validator import Citation, CitationValidationResult
from rag.context_builder import ContextBuildResult
from rag.document import Chunk
from rag.retriever import RetrievalResult
from rag.service import RAGResponse


class TestEvalRunner(unittest.TestCase):
    """Test suite verifying Gate D evaluation runner mechanics, dataset loading, and metrics."""

    def setUp(self) -> None:
        self.rag_dir = Path(__file__).resolve().parent.parent
        self.dataset_path = self.rag_dir / "eval_dataset.jsonl"
        self.corpus_dir = self.rag_dir / "corpus"

    def test_load_dataset_valid(self) -> None:
        scenarios = load_dataset(self.dataset_path)
        self.assertGreaterEqual(len(scenarios), 30)
        self.assertEqual(scenarios[0].scenario_id, "rag-01")
        self.assertEqual(scenarios[0].scenario_type, "factual_single")

    def test_load_dataset_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_dataset(Path("/nonexistent/path/eval_dataset.jsonl"))

    def test_load_dataset_insufficient_scenarios_raises_error(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl") as tf:
            tf.write('{"scenario_id": "rag-01", "scenario_type": "test", "query": "q", "expected_chunk_ids": []}\n')
            tf.flush()
            with self.assertRaises(ValueError):
                load_dataset(Path(tf.name))

    def test_evaluate_single_scenario_grounded(self) -> None:
        sc = EvalScenario(
            scenario_id="sc-01",
            scenario_type="factual",
            query="Audit retention?",
            expected_chunk_ids=["sec-01#c1"],
            expected_document_ids=["sec-01"],
            expected_facts=["7 years"],
            expected_abstention=False,
            metadata_filter=None,
            description="test",
        )
        chunk = Chunk(chunk_id="sec-01#c1", document_id="sec-01", chunk_index=1, text="Retention is 7 years.")
        ret_res = RetrievalResult(chunk=chunk, score=0.95, rank=1)
        cit = Citation(
            chunk_id="sec-01#c1",
            document_id="sec-01",
            section_title="Retention",
            source_title="Policy",
            source_uri="sec-01.md",
        )
        val_res = CitationValidationResult(is_valid=True, verified_citations=[cit], rejected_citation_ids=[])

        resp = RAGResponse(
            query="Audit retention?",
            answer="Audit logs must be kept for 7 years.",
            citations=[cit],
            retrieved_results=[ret_res],
            insufficient_evidence=False,
            context_build=ContextBuildResult("...", ["sec-01#c1"], 50, 1),
            citation_validation=val_res,
            latency_ms=10.0,
            raw_model_output='{"answer": "...", "citations": ["sec-01#c1"]}',
        )

        res = evaluate_single_scenario(sc, resp)
        self.assertTrue(res.hit)
        self.assertEqual(res.recall_at_k, 1.0)
        self.assertEqual(res.reciprocal_rank, 1.0)
        self.assertEqual(res.context_relevance, 1.0)
        self.assertTrue(res.grounded)
        self.assertTrue(res.schema_valid)
        self.assertTrue(res.abstention_accurate)

    def test_evaluate_single_scenario_abstention(self) -> None:
        sc = EvalScenario(
            scenario_id="sc-abstain",
            scenario_type="insufficient_evidence",
            query="Quantum flight upgrades?",
            expected_chunk_ids=[],
            expected_document_ids=[],
            expected_facts=[],
            expected_abstention=True,
            metadata_filter=None,
            description="test",
        )
        val_res = CitationValidationResult(is_valid=True, verified_citations=[], rejected_citation_ids=[], has_insufficient_evidence=True)
        resp = RAGResponse(
            query="Quantum flight upgrades?",
            answer="I do not have sufficient evidence.",
            citations=[],
            retrieved_results=[],
            insufficient_evidence=True,
            context_build=ContextBuildResult("[NO RELEVANT EVIDENCE FOUND]", [], 0, 0),
            citation_validation=val_res,
            latency_ms=2.0,
            raw_model_output="",
        )

        res = evaluate_single_scenario(sc, resp)
        self.assertTrue(res.hit)
        self.assertTrue(res.grounded)
        self.assertTrue(res.abstention_accurate)
        self.assertEqual(res.citation_accuracy, 1.0)

    def test_run_evaluation_fake_mode(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO):
            summary, results = asyncio.run(
                run_evaluation(
                    dataset_path=self.dataset_path,
                    corpus_dir=self.corpus_dir,
                    mode="fake",
                    top_k=2,
                )
            )
        self.assertIsNotNone(summary)
        self.assertGreaterEqual(summary.total_scenarios, 30)
        self.assertGreaterEqual(summary.groundedness_rate, 0.85)
        self.assertGreaterEqual(summary.mean_context_relevance, 0.80)
        self.assertGreaterEqual(summary.schema_adherence_rate, 0.98)
        self.assertTrue(summary.gate_d_passed)

    def test_save_and_print_report(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO):
            summary, results = asyncio.run(
                run_evaluation(
                    dataset_path=self.dataset_path,
                    corpus_dir=self.corpus_dir,
                    mode="fake",
                    top_k=2,
                )
            )
        with tempfile.TemporaryDirectory() as td:
            saved_path = save_report(summary, results, Path(td))
            self.assertTrue(saved_path.is_file())
            self.assertIn("eval_report_", saved_path.name)


        # Ensure print_report does not crash
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            print_report(summary)
            output = mock_stdout.getvalue()
            self.assertIn("GATE D VERDICT: PASS", output)


if __name__ == "__main__":
    unittest.main()
