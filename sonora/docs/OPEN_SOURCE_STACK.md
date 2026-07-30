# Open-source architecture

## Stack

| Layer | Project | SONORA use | Runtime policy |
|---|---|---|---|
| Core DSP | Python `wave`, `array`, `math` | PCM analysis and stimulus synthesis | mandatory |
| Music analysis | librosa | beat, onset, spectral, chroma, MFCC | optional |
| Music representation | MERT 95M | deep musical embeddings | optional, lazy |
| Audio–text representation | CLAP | concept alignment and semantic ranking | optional, lazy |
| Source separation | Demucs | vocals, drums, bass and accompaniment | optional, subprocess |
| Neural generation | MusicGen Small | text-conditioned stimuli | optional, lazy |
| API | FastAPI | local service | proposed next layer |
| UI | Gradio | internal laboratory | proposed next layer |

## Design decisions

1. The core has zero Python dependencies.
2. Every heavy library is imported only when selected.
3. Missing tools return an actionable installation command.
4. Model IDs are explicit and replaceable.
5. Generation always has a deterministic procedural fallback.
6. Output is written locally.
7. The same request and seed reproduce the same core output.
8. References to artists remain analytical labels, not claims of exact simulation.

## Resource profiles

### Core

- no GPU;
- no network;
- PCM WAV;
- procedural synthesis;
- cognitive crossing;
- end-to-end session report.

### Analysis

- `numpy`, `soundfile`, `librosa`;
- recommended first extension;
- CPU-friendly for short excerpts.

### Semantic

- MERT 95M or CLAP, one model at a time;
- short excerpts;
- persistent cache;
- CPU fallback when GPU memory is insufficient.

### Separation

- Demucs;
- prefer two-stem mode when the complete four-stem output is unnecessary;
- process one input at a time on limited machines.

### Generation

- MusicGen Small;
- short outputs;
- optional experimental backend;
- procedural generation remains the baseline.

## External licenses

This module is MIT. External code, models and weights keep their own licenses. Record model ID, revision and license before redistributing any downloaded artifact.
