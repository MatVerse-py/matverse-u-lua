from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from sonora_open_tools.core import (
    ValidationError,
    analyze_wav,
    cross,
    doctor,
    generate_procedural,
    run_session,
)


PROJECT = Path(__file__).resolve().parents[1]


class SonoraCoreTests(unittest.TestCase):
    def test_doctor_exposes_all_backends(self):
        names = {item["name"] for item in doctor()["tools"]}
        self.assertEqual(
            names,
            {"stdlib", "procedural", "librosa", "mert", "clap", "demucs", "musicgen"},
        )

    def test_generate_and_analyze_wav(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "stimulus.wav"
            artifact = generate_procedural(
                output,
                "teste cognitivo",
                duration_seconds=2,
                sample_rate=16000,
                seed=7,
                vector={"t": .8, "s": .2},
            )
            analysis = analyze_wav(output)
            self.assertEqual(artifact["backend"], "procedural")
            self.assertEqual(analysis["sample_rate"], 16000)
            self.assertAlmostEqual(analysis["duration_seconds"], 2.0, places=3)
            self.assertGreater(analysis["rms"], 0)

    def test_generation_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.wav"
            second = Path(directory) / "second.wav"
            generate_procedural(first, "same", 1, 8000, 11)
            generate_procedural(second, "same", 1, 8000, 11)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_seed_changes_output(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.wav"
            second = Path(directory) / "second.wav"
            generate_procedural(first, "same", 1, 8000, 11)
            generate_procedural(second, "same", 1, 8000, 12)
            self.assertNotEqual(first.read_bytes(), second.read_bytes())

    def test_cross_is_deterministic(self):
        request = json.loads(
            (PROJECT / "examples" / "cognitive_request.json").read_text(encoding="utf-8")
        )
        first = cross(request)
        second = cross(request)
        self.assertEqual(first["trace_hash"], second["trace_hash"])
        self.assertEqual(first["cross_variants"], second["cross_variants"])
        self.assertEqual(len(first["selected_variants"]), 2)

    def test_custom_dimension_validation(self):
        request = json.loads(
            (PROJECT / "examples" / "cognitive_request.json").read_text(encoding="utf-8")
        )
        request["architectures"] = [
            {
                "id": "custom",
                "label": "Custom",
                "preset": "custom",
                "dimensions": {"t": 1.2},
            }
        ]
        with self.assertRaises(ValidationError):
            cross(request)

    def test_session_end_to_end(self):
        with tempfile.TemporaryDirectory() as directory:
            request = json.loads(
                (PROJECT / "examples" / "session_core.json").read_text(encoding="utf-8")
            )
            request["workspace"] = directory
            request["stimulus_duration_seconds"] = 1
            path = Path(directory) / "session.json"
            path.write_text(json.dumps(request), encoding="utf-8")
            result = run_session(path)
            self.assertEqual(len(result["stimuli"]), 2)
            self.assertTrue(Path(result["report_json"]).is_file())
            for stimulus in result["stimuli"]:
                self.assertTrue(Path(stimulus["artifact"]["path"]).is_file())
                self.assertGreater(stimulus["analysis"]["rms"], 0)

    def test_missing_wav_rejected(self):
        with self.assertRaises(ValidationError):
            analyze_wav("missing.wav")


if __name__ == "__main__":
    unittest.main()
