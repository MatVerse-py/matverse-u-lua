from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import (
    ExecutionError,
    SonoraError,
    ToolUnavailableError,
    ValidationError,
    analyze,
    cross,
    doctor,
    embed_clap,
    embed_mert,
    generate_musicgen,
    generate_procedural,
    run_session,
    separate_demucs,
)


def _emit(payload: Any, pretty: bool = False) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2 if pretty else None))


def _load_json(path: str) -> dict[str, Any]:
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValidationError("JSON root must be an object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sonora", description="SONORA Open Tools")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor_cmd = sub.add_parser("doctor")
    doctor_cmd.add_argument("--pretty", action="store_true")

    analyze_cmd = sub.add_parser("analyze")
    analyze_cmd.add_argument("input")
    analyze_cmd.add_argument("--backend", choices=["auto", "stdlib", "librosa"], default="auto")
    analyze_cmd.add_argument("--max-seconds", type=int, default=120)
    analyze_cmd.add_argument("--pretty", action="store_true")

    generate_cmd = sub.add_parser("generate")
    generate_cmd.add_argument("--backend", choices=["procedural", "musicgen"], default="procedural")
    generate_cmd.add_argument("--prompt", required=True)
    generate_cmd.add_argument("--output", required=True)
    generate_cmd.add_argument("--duration", type=float, default=8.0)
    generate_cmd.add_argument("--sample-rate", type=int, default=32000)
    generate_cmd.add_argument("--seed", type=int, default=0)
    generate_cmd.add_argument("--vector-json")
    generate_cmd.add_argument("--pretty", action="store_true")

    cross_cmd = sub.add_parser("cross")
    cross_cmd.add_argument("request")
    cross_cmd.add_argument("--pretty", action="store_true")

    session_cmd = sub.add_parser("session")
    session_cmd.add_argument("request")
    session_cmd.add_argument("--pretty", action="store_true")

    embed_cmd = sub.add_parser("embed")
    embed_cmd.add_argument("input")
    embed_cmd.add_argument("--backend", choices=["mert", "clap"], required=True)
    embed_cmd.add_argument("--text", action="append", default=[])
    embed_cmd.add_argument("--device", default="auto")
    embed_cmd.add_argument("--pretty", action="store_true")

    separate_cmd = sub.add_parser("separate")
    separate_cmd.add_argument("input")
    separate_cmd.add_argument("--output-dir", required=True)
    separate_cmd.add_argument("--model", default="htdemucs")
    separate_cmd.add_argument("--two-stems", choices=["vocals", "drums", "bass", "other"])
    separate_cmd.add_argument("--pretty", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            _emit(doctor(), args.pretty)
            return 0

        if args.command == "analyze":
            _emit(analyze(args.input, args.backend, args.max_seconds), args.pretty)
            return 0

        if args.command == "generate":
            vector = _load_json(args.vector_json) if args.vector_json else None
            if args.backend == "procedural":
                result = generate_procedural(
                    args.output,
                    args.prompt,
                    args.duration,
                    args.sample_rate,
                    args.seed,
                    vector,
                )
            else:
                result = generate_musicgen(
                    args.output,
                    args.prompt,
                    args.duration,
                    args.seed,
                )
            _emit(result, args.pretty)
            return 0

        if args.command == "cross":
            _emit(cross(_load_json(args.request)), args.pretty)
            return 0

        if args.command == "session":
            _emit(run_session(args.request), args.pretty)
            return 0

        if args.command == "embed":
            result = (
                embed_mert(args.input, device=args.device)
                if args.backend == "mert"
                else embed_clap(args.input, args.text, device=args.device)
            )
            _emit(result, args.pretty)
            return 0

        if args.command == "separate":
            _emit(
                separate_demucs(
                    args.input,
                    args.output_dir,
                    args.model,
                    args.two_stems,
                ),
                args.pretty,
            )
            return 0

        raise ValidationError(f"unsupported command: {args.command}")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, SonoraError) as exc:
        _emit({"status": "ERROR", "error": str(exc)}, True)
        return 2
    except Exception as exc:
        _emit({"status": "INTERNAL_ERROR", "error": f"{type(exc).__name__}: {exc}"}, True)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
