from __future__ import annotations

from array import array
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import sys
import wave
from typing import Any, Mapping, Sequence


VERSION = "3.0.0"
SCOPE = "internal_cognitive_training"
DIMS = ("t", "p", "d", "v", "a", "b", "o", "r", "e", "s")

PRESETS: dict[str, dict[str, float]] = {
    "intimate_confessional": {
        "t": .58, "p": .68, "d": .32, "v": .22, "a": .62,
        "b": .72, "o": .18, "r": .38, "e": .66, "s": .78,
    },
    "soul_expansive": {
        "t": .64, "p": .78, "d": .86, "v": .72, "a": .58,
        "b": .42, "o": .84, "r": .82, "e": .92, "s": .40,
    },
    "spoken_narrative": {
        "t": .72, "p": .82, "d": .52, "v": .08, "a": .92,
        "b": .38, "o": .10, "r": .28, "e": .68, "s": .62,
    },
    "theatrical_dramatic": {
        "t": .54, "p": .76, "d": .94, "v": .66, "a": .82,
        "b": .28, "o": .62, "r": .92, "e": .96, "s": .70,
    },
    "minimalist_tension": {
        "t": .46, "p": .42, "d": .28, "v": .06, "a": .54,
        "b": .48, "o": .04, "r": .24, "e": .76, "s": .90,
    },
    "rhythmic_confrontation": {
        "t": .90, "p": .70, "d": .78, "v": .10, "a": .94,
        "b": .20, "o": .22, "r": .54, "e": .82, "s": .36,
    },
}

PROFILES: dict[str, dict[str, Any]] = {
    "focused": {
        "exploration_level": .25,
        "crossing_depth": 2,
        "variation_count": 3,
        "constraint_strength": .80,
        "output_selection_count": 2,
    },
    "expansive": {
        "exploration_level": .60,
        "crossing_depth": 3,
        "variation_count": 5,
        "constraint_strength": .55,
        "output_selection_count": 2,
    },
    "frontier": {
        "exploration_level": .90,
        "crossing_depth": 5,
        "variation_count": 8,
        "constraint_strength": .30,
        "output_selection_count": 3,
    },
}

TOOLS = {
    "stdlib": ("analysis", None, None, "PCM WAV analysis"),
    "procedural": ("generation", None, None, "deterministic stimulus synthesis"),
    "librosa": ("analysis", "librosa", "analysis", "musical descriptors"),
    "mert": ("embedding", "transformers", "semantic", "m-a-p/MERT-v1-95M"),
    "clap": ("embedding", "transformers", "semantic", "laion/clap-htsat-unfused"),
    "demucs": ("separation", "demucs", "separation", "htdemucs"),
    "musicgen": ("generation", "transformers", "generation", "facebook/musicgen-small"),
}


class SonoraError(Exception):
    pass


class ValidationError(SonoraError):
    pass


class ToolUnavailableError(SonoraError):
    pass


class ExecutionError(SonoraError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _bounded(value: Any, path: str) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{path} must be numeric")
    number = float(value)
    _require(math.isfinite(number) and 0.0 <= number <= 1.0, f"{path} must be in [0,1]")
    return round(number, 6)


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha3_256(encoded).hexdigest()


def doctor() -> dict[str, Any]:
    tools = []
    for name, (kind, module, extra, description) in TOOLS.items():
        available = module is None or importlib.util.find_spec(module) is not None
        tools.append({
            "name": name,
            "kind": kind,
            "available": available,
            "install_extra": extra,
            "description_or_model": description,
            "reason": "ready" if available else f"missing module: {module}",
        })
    return {"version": VERSION, "scope": SCOPE, "tools": tools}


def _decode_pcm(raw: bytes, sample_width: int) -> list[float]:
    if sample_width == 1:
        return [(value - 128) / 128.0 for value in raw]
    if sample_width == 2:
        values = array("h")
        values.frombytes(raw)
        return [value / 32768.0 for value in values]
    if sample_width == 4:
        values = array("i")
        values.frombytes(raw)
        return [value / 2147483648.0 for value in values]
    raise ValidationError(f"unsupported WAV sample width: {sample_width}")


def _downmix(samples: list[float], channels: int) -> list[float]:
    if channels == 1:
        return samples
    return [
        sum(samples[index:index + channels]) / channels
        for index in range(0, len(samples), channels)
    ]


def _estimate_tempo(samples: list[float], sample_rate: int) -> float | None:
    if len(samples) < sample_rate * 2:
        return None
    hop = 1024
    envelope = []
    for start in range(0, len(samples) - hop, hop):
        block = samples[start:start + hop]
        envelope.append(math.sqrt(sum(value * value for value in block) / len(block)))
    onset = [max(0.0, envelope[index] - envelope[index - 1]) for index in range(1, len(envelope))]
    if not onset or max(onset) <= 1e-9:
        return None
    rate = sample_rate / hop
    minimum = max(1, int(rate * 60.0 / 220.0))
    maximum = min(len(onset) - 1, int(rate * 60.0 / 40.0))
    if maximum <= minimum:
        return None
    best_lag = None
    best_score = -1.0
    for lag in range(minimum, maximum + 1):
        score = sum(onset[index] * onset[index - lag] for index in range(lag, len(onset)))
        if score > best_score:
            best_score = score
            best_lag = lag
    if best_lag is None or best_score <= 0:
        return None
    return round(60.0 * rate / best_lag, 3)


def analyze_wav(path: str | Path, max_seconds: int = 120) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    _require(source.is_file(), f"audio file not found: {source}")
    _require(source.suffix.lower() == ".wav", "stdlib backend supports PCM WAV only")
    with wave.open(str(source), "rb") as handle:
        channels = handle.getnchannels()
        sample_rate = handle.getframerate()
        frames = handle.getnframes()
        sample_width = handle.getsampwidth()
        raw = handle.readframes(min(frames, sample_rate * max_seconds))
    samples = _downmix(_decode_pcm(raw, sample_width), channels)
    _require(bool(samples), "empty audio file")
    rms = math.sqrt(sum(value * value for value in samples) / len(samples))
    peak = max(abs(value) for value in samples)
    dc_offset = sum(samples) / len(samples)
    crossings = sum(
        1 for left, right in zip(samples, samples[1:])
        if (left < 0 <= right) or (left >= 0 > right)
    )
    return {
        "backend": "stdlib",
        "path": str(source),
        "sample_rate": sample_rate,
        "channels": channels,
        "frames": frames,
        "duration_seconds": round(frames / sample_rate, 6),
        "rms": round(rms, 8),
        "peak": round(peak, 8),
        "zero_crossing_rate": round(crossings / max(1, len(samples) - 1), 8),
        "dc_offset": round(dc_offset, 8),
        "tempo_bpm": _estimate_tempo(samples, sample_rate),
        "features": {
            "analyzed_seconds": round(len(samples) / sample_rate, 6),
            "sample_width_bytes": sample_width,
        },
    }


def analyze_librosa(path: str | Path, max_seconds: int = 120) -> dict[str, Any]:
    try:
        import librosa
        import numpy as np
    except ImportError as exc:
        raise ToolUnavailableError('install analysis backend with: pip install -e ".[analysis]"') from exc
    source = Path(path).expanduser().resolve()
    _require(source.is_file(), f"audio file not found: {source}")
    y, sample_rate = librosa.load(str(source), sr=None, mono=True, duration=max_seconds)
    _require(y.size > 0, "empty audio file")
    tempo, beats = librosa.beat.beat_track(y=y, sr=sample_rate)
    tempo_value = float(np.asarray(tempo).reshape(-1)[0])
    rms = librosa.feature.rms(y=y)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sample_rate)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sample_rate)[0]
    chroma = librosa.feature.chroma_stft(y=y, sr=sample_rate)
    mfcc = librosa.feature.mfcc(y=y, sr=sample_rate, n_mfcc=13)
    return {
        "backend": "librosa",
        "path": str(source),
        "sample_rate": int(sample_rate),
        "channels": 1,
        "frames": int(y.size),
        "duration_seconds": round(float(librosa.get_duration(y=y, sr=sample_rate)), 6),
        "rms": round(float(np.mean(rms)), 8),
        "peak": round(float(np.max(np.abs(y))), 8),
        "zero_crossing_rate": round(float(np.mean(zcr)), 8),
        "dc_offset": round(float(np.mean(y)), 8),
        "tempo_bpm": round(tempo_value, 3),
        "features": {
            "beat_count": int(len(beats)),
            "spectral_centroid_mean": round(float(np.mean(centroid)), 6),
            "spectral_bandwidth_mean": round(float(np.mean(bandwidth)), 6),
            "chroma_mean": [round(float(value), 6) for value in np.mean(chroma, axis=1)],
            "mfcc_mean": [round(float(value), 6) for value in np.mean(mfcc, axis=1)],
        },
    }


def analyze(path: str | Path, backend: str = "auto", max_seconds: int = 120) -> dict[str, Any]:
    if backend == "stdlib":
        return analyze_wav(path, max_seconds)
    if backend == "librosa":
        return analyze_librosa(path, max_seconds)
    if backend == "auto":
        if importlib.util.find_spec("librosa") is not None:
            try:
                return analyze_librosa(path, max_seconds)
            except Exception:
                pass
        return analyze_wav(path, max_seconds)
    raise ValidationError(f"unsupported analysis backend: {backend}")


def _beat_random(seed: int, beat_index: int) -> float:
    return random.Random((seed + 1) * 1_000_003 + beat_index * 97_409).random()


def generate_procedural(
    output_path: str | Path,
    prompt: str,
    duration_seconds: float = 8.0,
    sample_rate: int = 32000,
    seed: int = 0,
    vector: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    _require(bool(prompt.strip()), "prompt cannot be empty")
    _require(1.0 <= duration_seconds <= 120.0, "duration_seconds must be in [1,120]")
    _require(8000 <= sample_rate <= 96000, "sample_rate must be in [8000,96000]")
    values = {key: .5 for key in DIMS}
    values.update({"v": .2, "b": .3, "o": .3, "s": .3})
    if vector:
        for key, value in vector.items():
            _require(key in values, f"unknown vector dimension: {key}")
            values[key] = _bounded(value, f"vector.{key}")

    tempo = 55.0 + 145.0 * values["t"]
    beat_duration = 60.0 / tempo
    base_frequency = 110.0 * (2.0 ** (2.2 * values["r"]))
    amplitude = .18 + .52 * values["d"]
    vibrato_depth = .002 + .025 * values["v"]
    vibrato_rate = 3.0 + 5.0 * values["v"]
    silence_probability = .04 + .44 * values["s"]
    articulation = .12 + .82 * values["a"]
    phrase_beats = max(2, round(2 + 6 * values["p"]))
    harmonic_count = 1 + round(4 * values["o"])
    rng = random.Random(seed)
    pcm = bytearray()

    for index in range(int(duration_seconds * sample_rate)):
        time = index / sample_rate
        beat_position = time / beat_duration
        beat_index = int(beat_position)
        local_beat = beat_position - beat_index
        silent = _beat_random(seed, beat_index) < silence_probability
        envelope = 0.0
        if not silent:
            attack = min(1.0, local_beat / max(.01, .08 * (1.1 - articulation)))
            release_start = .18 + .72 * articulation
            release = 1.0 if local_beat <= release_start else max(
                0.0, 1.0 - (local_beat - release_start) / max(.01, 1.0 - release_start)
            )
            envelope = attack * release
        phrase_index = beat_index // phrase_beats
        phrase_mod = .88 + .12 * math.sin(2 * math.pi * phrase_index / max(2.0, 3.0 + 5.0 * values["e"]))
        micro_shift = (_beat_random(seed + 31, beat_index) - .5) * .025 * values["t"]
        frequency = base_frequency * (1.0 + micro_shift)
        frequency *= 1.0 + vibrato_depth * math.sin(2 * math.pi * vibrato_rate * time)
        sample = 0.0
        for harmonic in range(1, harmonic_count + 1):
            gain = 1.0 / (harmonic ** (1.1 + 1.5 * (1.0 - values["o"])))
            sample += gain * math.sin(2 * math.pi * frequency * harmonic * time)
        sample += (rng.random() * 2.0 - 1.0) * .008 * values["b"]
        sample = max(-.98, min(.98, sample * amplitude * envelope * phrase_mod))
        pcm.extend(struct.pack("<h", int(sample * 32767.0)))

    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(bytes(pcm))
    return {
        "backend": "procedural",
        "path": str(output),
        "duration_seconds": round(duration_seconds, 6),
        "sample_rate": sample_rate,
        "seed": seed,
        "prompt": prompt,
        "metadata": {
            "tempo_bpm": round(tempo, 3),
            "base_frequency_hz": round(base_frequency, 3),
            "harmonic_count": harmonic_count,
            "vector": values,
        },
    }


def _architecture_vector(architecture: Mapping[str, Any]) -> dict[str, float]:
    preset = architecture.get("preset")
    _require(preset in set(PRESETS) | {"custom"}, f"unsupported preset: {preset}")
    vector = {key: .5 for key in DIMS} if preset == "custom" else dict(PRESETS[preset])
    dimensions = architecture.get("dimensions", {})
    _require(isinstance(dimensions, dict), "architecture.dimensions must be an object")
    if preset == "custom":
        _require(bool(dimensions), "custom preset requires dimensions")
    for key, value in dimensions.items():
        _require(key in DIMS, f"unknown dimension: {key}")
        vector[key] = _bounded(value, f"dimensions.{key}")
    return vector


def _distance(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    return round(sum(abs(left[key] - right[key]) for key in DIMS) / len(DIMS), 6)


def cross(request: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(request, Mapping), "request must be an object")
    _require(request.get("scope") == SCOPE, f"scope must be {SCOPE}")
    architectures = request.get("architectures")
    _require(isinstance(architectures, list) and 1 <= len(architectures) <= 8, "architectures length must be 1..8")
    controls = dict(PROFILES.get(request.get("controls", {}).get("possibility_profile", "expansive"), PROFILES["expansive"]))
    controls.update(request.get("controls", {}))
    variation_count = int(controls.get("variation_count", 5))
    selection_count = min(int(controls.get("output_selection_count", 2)), variation_count)
    _require(2 <= variation_count <= 12, "variation_count must be 2..12")
    _require(1 <= selection_count <= variation_count, "invalid output_selection_count")
    exploration = _bounded(controls.get("exploration_level", .6), "exploration_level")
    constraint = _bounded(controls.get("constraint_strength", .55), "constraint_strength")
    depth = int(controls.get("crossing_depth", 3))
    _require(1 <= depth <= 5, "crossing_depth must be 1..5")

    input_vectors = []
    seen_ids = set()
    for index, architecture in enumerate(architectures):
        _require(isinstance(architecture, Mapping), f"architectures[{index}] must be an object")
        identifier = str(architecture.get("id", "")).strip()
        _require(bool(identifier) and identifier not in seen_ids, "architecture ids must be non-empty and unique")
        seen_ids.add(identifier)
        input_vectors.append({
            "id": identifier,
            "label": str(architecture.get("label", identifier)),
            "weight": _bounded(architecture.get("weight", 1.0), f"architectures[{index}].weight"),
            "vector": _architecture_vector(architecture),
        })

    total_weight = sum(item["weight"] for item in input_vectors)
    centroid = {
        key: sum(item["weight"] * item["vector"][key] for item in input_vectors) / total_weight
        for key in DIMS
    }
    matrix = [[_distance(left["vector"], right["vector"]) for right in input_vectors] for left in input_vectors]
    seed = int(controls.get("seed", int(_canonical_hash(request)[:12], 16) % 2_147_483_648))
    rng = random.Random(seed)
    amplitude = .24 * exploration * (1.0 - .55 * constraint)
    variants = []

    for index in range(variation_count):
        width = 1 if len(input_vectors) == 1 else min(len(input_vectors), max(2, depth))
        chosen = [input_vectors[(index + offset) % len(input_vectors)] for offset in range(width)]
        raw_weights = [item["weight"] * (.75 + .5 * rng.random()) for item in chosen]
        normalizer = sum(raw_weights)
        normalized = [value / normalizer for value in raw_weights]
        mixed = {
            key: sum(weight * item["vector"][key] for weight, item in zip(normalized, chosen))
            for key in DIMS
        }
        focus = DIMS[index % len(DIMS)]
        counter = DIMS[(index * 3 + 4) % len(DIMS)]
        vector = {}
        for key in DIMS:
            value = mixed[key] + (rng.random() * 2.0 - 1.0) * amplitude * .35
            if key == focus:
                value += amplitude * (.55 + .45 * rng.random())
            if key == counter:
                value -= amplitude * (.35 + .35 * rng.random())
            vector[key] = round(max(0.0, min(1.0, constraint * centroid[key] + (1.0 - constraint) * value)), 6)
        novelty = _distance(vector, centroid)
        variants.append({
            "id": f"cross-{index + 1:02d}",
            "parents": [{"id": item["id"], "weight": round(weight, 6)} for item, weight in zip(chosen, normalized)],
            "focus_dimension": focus,
            "counter_dimension": counter,
            "vector": vector,
            "novelty_from_centroid": novelty,
        })

    for variant in variants:
        distances = [_distance(variant["vector"], other["vector"]) for other in variants if other is not variant]
        distinctiveness = sum(distances) / len(distances) if distances else 0.0
        variant["distinctiveness"] = round(distinctiveness, 6)
        variant["selection_score"] = round(.65 * min(1.0, variant["novelty_from_centroid"] / .18) + .35 * min(1.0, distinctiveness / .22), 6)
    variants.sort(key=lambda item: (-item["selection_score"], item["id"]))
    selected = [item["id"] for item in variants[:selection_count]]
    result = {
        "status": "READY",
        "engine_version": VERSION,
        "scope": SCOPE,
        "request_id": request.get("request_id"),
        "mode": request.get("mode", "cross"),
        "seed": seed,
        "controls": controls,
        "input_vectors": input_vectors,
        "cross_matrix": {"ids": [item["id"] for item in input_vectors], "matrix": matrix},
        "cross_variants": variants,
        "selected_variants": selected,
        "cognitive_actions": [
            {"step": 1, "action": "blind_rank", "rule": "rank outputs before revealing parameters"},
            {"step": 2, "action": "select", "variant_ids": selected},
            {"step": 3, "action": "justify", "measure": "link decision to measured dimensions"},
            {"step": 4, "action": "transfer", "task": controls.get("transfer_task", "apply the selected pattern to a non-musical task")},
        ],
        "scope_note": "internal cognitive training; labels are analytical references, not exact predictions of people",
    }
    result["trace_hash"] = _canonical_hash(result)
    return result


def embed_mert(path: str | Path, model_id: str = "m-a-p/MERT-v1-95M", device: str = "auto") -> dict[str, Any]:
    try:
        import librosa
        import numpy as np
        import torch
        from transformers import AutoModel, Wav2Vec2FeatureExtractor
    except ImportError as exc:
        raise ToolUnavailableError('install semantic backend with: pip install -e ".[semantic]"') from exc
    source = Path(path).expanduser().resolve()
    _require(source.is_file(), f"audio file not found: {source}")
    target = "cuda" if device == "auto" and torch.cuda.is_available() else "cpu" if device == "auto" else device
    processor = Wav2Vec2FeatureExtractor.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_id, trust_remote_code=True).to(target).eval()
    sampling_rate = int(getattr(processor, "sampling_rate", 24000))
    audio, _ = librosa.load(str(source), sr=sampling_rate, mono=True)
    values = processor(audio, sampling_rate=sampling_rate, return_tensors="pt")["input_values"].to(target)
    with torch.inference_mode():
        output = model(values, output_hidden_states=True).hidden_states[-1][0].mean(dim=0)
    vector = output.detach().float().cpu().numpy()
    serial = [round(float(value), 8) for value in vector.tolist()]
    return {
        "backend": "mert",
        "model_id": model_id,
        "source": str(source),
        "dimension": len(serial),
        "norm": round(float(np.linalg.norm(vector)), 8),
        "sha3_256": hashlib.sha3_256(json.dumps(serial, separators=(",", ":")).encode()).hexdigest(),
        "preview": serial[:16],
    }


def embed_clap(path: str | Path, texts: Sequence[str] | None = None, model_id: str = "laion/clap-htsat-unfused", device: str = "auto") -> dict[str, Any]:
    try:
        import librosa
        import numpy as np
        import torch
        from transformers import AutoProcessor, ClapModel
    except ImportError as exc:
        raise ToolUnavailableError('install semantic backend with: pip install -e ".[semantic]"') from exc
    source = Path(path).expanduser().resolve()
    _require(source.is_file(), f"audio file not found: {source}")
    target = "cuda" if device == "auto" and torch.cuda.is_available() else "cpu" if device == "auto" else device
    processor = AutoProcessor.from_pretrained(model_id)
    model = ClapModel.from_pretrained(model_id).to(target).eval()
    audio, _ = librosa.load(str(source), sr=48000, mono=True)
    inputs = processor(audios=audio, sampling_rate=48000, return_tensors="pt")
    inputs = {key: value.to(target) for key, value in inputs.items()}
    with torch.inference_mode():
        feature = model.get_audio_features(**inputs)[0]
    vector = feature.detach().float().cpu().numpy()
    vector = vector / max(float(np.linalg.norm(vector)), 1e-12)
    similarities = {}
    clean_texts = [text.strip() for text in (texts or []) if text.strip()]
    if clean_texts:
        text_inputs = processor(text=clean_texts, return_tensors="pt", padding=True)
        text_inputs = {key: value.to(target) for key, value in text_inputs.items()}
        with torch.inference_mode():
            text_features = model.get_text_features(**text_inputs).detach().float().cpu().numpy()
        text_features = text_features / np.maximum(np.linalg.norm(text_features, axis=1, keepdims=True), 1e-12)
        similarities = {text: round(float(score), 8) for text, score in zip(clean_texts, (text_features @ vector).tolist())}
    serial = [round(float(value), 8) for value in vector.tolist()]
    return {
        "backend": "clap",
        "model_id": model_id,
        "source": str(source),
        "dimension": len(serial),
        "norm": round(float(np.linalg.norm(vector)), 8),
        "sha3_256": hashlib.sha3_256(json.dumps(serial, separators=(",", ":")).encode()).hexdigest(),
        "preview": serial[:16],
        "similarities": similarities,
    }


def separate_demucs(path: str | Path, output_directory: str | Path, model: str = "htdemucs", two_stems: str | None = None) -> dict[str, Any]:
    if importlib.util.find_spec("demucs") is None:
        raise ToolUnavailableError('install separation backend with: pip install -e ".[separation]"')
    source = Path(path).expanduser().resolve()
    _require(source.is_file(), f"audio file not found: {source}")
    output = Path(output_directory).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "demucs", "-n", model, "-o", str(output)]
    if two_stems:
        _require(two_stems in {"vocals", "drums", "bass", "other"}, "invalid two_stems")
        command.extend(["--two-stems", two_stems])
    command.append(str(source))
    process = subprocess.run(command, text=True, capture_output=True, check=False)
    if process.returncode != 0:
        raise ExecutionError(f"Demucs failed: {process.stderr.strip()}")
    stem_root = output / model / source.stem
    stems = sorted(str(item) for item in stem_root.glob("*.wav"))
    _require(bool(stems), f"no stems found in {stem_root}")
    return {"backend": "demucs", "source": str(source), "output_directory": str(stem_root), "stems": stems, "command": command}


def generate_musicgen(output_path: str | Path, prompt: str, duration_seconds: float = 8.0, seed: int = 0, model_id: str = "facebook/musicgen-small", device: str = "auto") -> dict[str, Any]:
    try:
        import numpy as np
        import torch
        from scipy.io import wavfile
        from transformers import pipeline, set_seed
    except ImportError as exc:
        raise ToolUnavailableError('install generation backend with: pip install -e ".[generation]"') from exc
    _require(bool(prompt.strip()), "prompt cannot be empty")
    _require(1.0 <= duration_seconds <= 30.0, "MusicGen duration must be in [1,30]")
    target = 0 if device == "auto" and torch.cuda.is_available() else -1 if device == "auto" else device
    set_seed(seed)
    synthesizer = pipeline("text-to-audio", model=model_id, device=target)
    max_new_tokens = max(32, int(duration_seconds * 50))
    result = synthesizer(prompt, forward_params={"max_new_tokens": max_new_tokens})
    audio = np.asarray(result["audio"]).squeeze()
    sample_rate = int(result["sampling_rate"])
    peak = max(float(np.max(np.abs(audio))), 1e-12)
    pcm = np.int16(np.clip(audio / peak, -1.0, 1.0) * 32767.0)
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(str(output), sample_rate, pcm)
    return {"backend": "musicgen", "path": str(output), "duration_seconds": round(len(pcm) / sample_rate, 6), "sample_rate": sample_rate, "seed": seed, "prompt": prompt, "model_id": model_id}


def run_session(request_path: str | Path) -> dict[str, Any]:
    source = Path(request_path).expanduser().resolve()
    _require(source.is_file(), f"session file not found: {source}")
    request = json.loads(source.read_text(encoding="utf-8"))
    _require(isinstance(request, dict), "session root must be an object")
    _require("session_id" in request and "cognitive_request" in request, "session_id and cognitive_request are required")
    workspace = Path(request.get("workspace", "./runs")).expanduser().resolve()
    session_dir = workspace / str(request["session_id"])
    session_dir.mkdir(parents=True, exist_ok=True)
    cognitive = cross(request["cognitive_request"])
    selected_ids = set(cognitive["selected_variants"])
    selected = [item for item in cognitive["cross_variants"] if item["id"] in selected_ids]
    backend = request.get("stimulus_backend", "procedural")
    duration = float(request.get("stimulus_duration_seconds", 8.0))
    stimuli = []
    for index, variant in enumerate(selected, start=1):
        output = session_dir / f"stimulus_{index:02d}_{variant['id']}.wav"
        prompt = f"SONORA {variant['id']} focus={variant['focus_dimension']} counter={variant['counter_dimension']}"
        if backend == "procedural":
            artifact = generate_procedural(output, prompt, duration, seed=cognitive["seed"] + index, vector=variant["vector"])
        elif backend == "musicgen":
            artifact = generate_musicgen(output, prompt, duration, seed=cognitive["seed"] + index)
        else:
            raise ValidationError(f"unsupported stimulus_backend: {backend}")
        stimuli.append({"variant_id": variant["id"], "artifact": artifact, "analysis": analyze(artifact["path"], request.get("analysis_backend", "auto"))})
    result = {
        "session_id": request["session_id"],
        "session_directory": str(session_dir),
        "cognitive": cognitive,
        "stimuli": stimuli,
        "interpretation": "design outputs are structural projections; record baseline and post-task results to measure transfer",
    }
    report = session_dir / "session_report.json"
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result["report_json"] = str(report)
    return result
