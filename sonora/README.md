# SONORA Open Tools v3

Módulo open source do MatVerse LUA para transformar música e som em carga cognitiva controlada.

## Objetivo

```text
áudio ou material-base
→ descritores
→ arquiteturas interpretativas
→ cruzamentos
→ outputs sonoros
→ ranking e seleção
→ tarefa de transferência
→ observação
→ ajuste da sessão seguinte
```

O caminho `core` funciona offline, sem GPU, sem modelos e sem dependências Python externas. Librosa, MERT, CLAP, Demucs e MusicGen são adaptadores opcionais carregados sob demanda.

## Ferramentas

| Backend | Função | Instalação |
|---|---|---|
| `stdlib` | análise PCM WAV | core |
| `procedural` | geração determinística de estímulos | core |
| `librosa` | tempo, onset, espectro, chroma e MFCC | `.[analysis]` |
| `mert` | embeddings de entendimento musical | `.[semantic]` |
| `clap` | alinhamento áudio–texto | `.[semantic]` |
| `demucs` | separação de fontes | `.[separation]` |
| `musicgen` | geração neural | `.[generation]` |

## Instalação

```bash
cd sonora
python -m pip install -e .
sonora doctor --pretty
```

Análise avançada:

```bash
python -m pip install -e ".[analysis]"
```

Modelos semânticos:

```bash
python -m pip install -e ".[semantic]"
```

Separação e geração:

```bash
python -m pip install -e ".[separation]"
python -m pip install -e ".[generation]"
```

## Uso rápido

```bash
sonora generate \
  --backend procedural \
  --prompt "contraste rítmico com silêncio crescente" \
  --output runs/stimulus.wav \
  --duration 8 \
  --seed 42

sonora analyze runs/stimulus.wav --backend auto --pretty
sonora cross examples/cognitive_request.json --pretty
sonora session examples/session_core.json --pretty
```

## Perfis cognitivos

- `focused`: discriminação fina, menor amplitude;
- `expansive`: equilíbrio entre coerência e descoberta;
- `frontier`: busca distante e maior cobertura.

## Hardware limitado

Comece por `core`. Ative somente `analysis` em seguida. Execute MERT, CLAP, Demucs e MusicGen individualmente, com trechos curtos e cache local.

## Licenças

Este módulo é MIT. Projetos e pesos externos preservam suas próprias licenças. O código do AudioCraft é MIT; os pesos oficiais documentados pelo projeto são CC-BY-NC 4.0, adequados ao escopo interno não comercial definido para SONORA.
