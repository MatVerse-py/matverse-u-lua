# MatVerse LUA

**Learning Unit Architecture (COG → PoSE → PoLE)**

## Visão Geral

O **MatVerse LUA** (Learning Unit Architecture) é o sistema de aprendizado verificável do MatVerse Pessoal. Ele transforma cada sessão de interação em **conhecimento estruturado** com lastro criptográfico e governança matemática, pronto para ser integrado ao motor de decisão Ω-GATE.

## Filosofia

> "O conhecimento não é apenas armazenado, é **provado**. Cada sessão de aprendizado gera uma prova criptográfica de sua qualidade epistêmica."

O LUA não é um banco de dados de conversas. É um **pipeline de transformação epistêmica** que converte interações brutas em conhecimento auditável, mensurável e governado por métricas matemáticas.

## Arquitetura

### Pipeline de Transformação

```
┌────────────────────────────────────────────────────────────┐
│                    MatVerse LUA Pipeline                   │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────┐
    │  1. COG (Cognitive Capture)                  │
    │     Captura bruta de interações              │
    │     - Mensagens do usuário                   │
    │     - Respostas do sistema                   │
    │     - Contexto e metadados                   │
    └──────────────────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────┐
    │  2. PoSE (Proof of Semantic Extraction)      │
    │     Extração e estruturação semântica        │
    │     - Identificação de conceitos-chave       │
    │     - Extração de fatos e relações           │
    │     - Classificação por domínio              │
    │     - Geração de embeddings                  │
    └──────────────────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────┐
    │  3. PoLE (Proof of Learning Evidence)        │
    │     Validação e prova criptográfica          │
    │     - Cálculo de Ψ (qualidade epistêmica)    │
    │     - Cálculo de Ω (decisão de governança)   │
    │     - Cálculo de CVaR (risco)                │
    │     - Geração de Merkle Tree                 │
    │     - Assinatura PQC (pós-quântica)          │
    └──────────────────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────┐
    │  4. Storage & Indexing                       │
    │     Armazenamento e indexação                │
    │     - VectorDB (embeddings)                  │
    │     - Ledger (proofs)                        │
    │     - Graph DB (relações)                    │
    └──────────────────────────────────────────────┘
```

### Métricas de Governança

#### Ψ (Psi-Index) - Qualidade Epistêmica

```
Ψ = 0.4·Completude + 0.3·Consistência + 0.3·Rastreabilidade

Onde:
- Completude: % de campos preenchidos, referências válidas
- Consistência: Coerência interna, ausência de contradições
- Rastreabilidade: Presença de fontes, timestamps, hashes
```

#### Ω (Omega-Score) - Decisão de Governança

```
Ω = 0.4·Ψ + 0.2·Θ_norm + 0.2·(1-CVaR/0.05) + 0.2·PoLE

Onde:
- Θ_norm: Performance normalizada (tempo de processamento)
- CVaR: Risco de inconsistência (95% confidence)
- PoLE: Presença de prova criptográfica válida
```

#### CVaR (Conditional Value at Risk)

```
CVaR_95 = E[Risco | Risco > VaR_95]

Risco medido por:
- Fatos não verificados
- Referências quebradas
- Inconsistências detectadas
```

## Estrutura do Repositório

```
matverse-u-lua/
├── cog/                     # Cognitive Capture
│   ├── capture.py          # Motor de captura
│   ├── parsers/            # Parsers de diferentes fontes
│   └── schemas/            # Schemas de dados brutos
├── pose/                    # Proof of Semantic Extraction
│   ├── extractor.py        # Motor de extração semântica
│   ├── embeddings/         # Geração de embeddings
│   ├── classifier.py       # Classificação por domínio
│   └── graph.py            # Construção de grafo de conhecimento
├── pole/                    # Proof of Learning Evidence
│   ├── metrics.py          # Cálculo de Ψ, Ω, CVaR
│   ├── merkle.py           # Geração de Merkle Tree
│   ├── pqc.py              # Assinatura pós-quântica
│   └── proof.py            # Geração de proofs
├── storage/                 # Armazenamento
│   ├── vectordb/           # VectorDB (Qdrant/Weaviate)
│   ├── ledger/             # Ledger de proofs
│   └── graphdb/            # Graph DB (Neo4j)
├── governance/              # Governança
│   ├── registry.json       # Registry de proofs
│   ├── policies/           # Políticas OPA
│   └── audit.py            # Auditoria de proofs
├── scripts/                 # Scripts de automação
│   ├── collect-metrics.py  # Coletor de métricas
│   ├── generate-proof.py   # Gerador de proofs
│   └── audit-registry.py   # Auditor de registry
├── docs/                    # Documentação
│   ├── architecture.md     # Arquitetura detalhada
│   ├── metrics.md          # Especificação de métricas
│   └── api.md              # Referência de API
├── tests/                   # Testes
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── README.md               # Este arquivo
```

## Início Rápido

### Pré-requisitos

- **Python**: 3.11+
- **VectorDB**: Qdrant ou Weaviate (opcional)
- **Graph DB**: Neo4j (opcional)
- **Dependências**: numpy, scipy, cryptography

### Instalação

```bash
# Clonar repositório
git clone https://github.com/MatVerse-py/matverse-u-lua.git
cd matverse-u-lua

# Instalar dependências
pip install -r requirements.txt

# Configurar
cp config.example.yaml config.yaml
nano config.yaml  # Editar configurações
```

### Uso Básico

#### 1. Capturar Interação (COG)

```python
from cog.capture import CognitiveCapture

capture = CognitiveCapture()

# Capturar uma sessão de chat
session = capture.capture_session(
    user_messages=["Explique a arquitetura MatVerse"],
    assistant_messages=["MatVerse é um sistema..."],
    metadata={"source": "chat", "timestamp": "2026-02-13T12:00:00Z"}
)

print(f"Session ID: {session.id}")
```

#### 2. Extrair Semântica (PoSE)

```python
from pose.extractor import SemanticExtractor

extractor = SemanticExtractor()

# Extrair conceitos e fatos
extraction = extractor.extract(session)

print(f"Conceitos: {extraction.concepts}")
print(f"Fatos: {extraction.facts}")
print(f"Embeddings: {extraction.embeddings.shape}")
```

#### 3. Gerar Prova (PoLE)

```python
from pole.proof import ProofGenerator

generator = ProofGenerator()

# Gerar prova criptográfica
proof = generator.generate(extraction)

print(f"Ψ: {proof.metrics.psi}")
print(f"Ω: {proof.metrics.omega}")
print(f"CVaR: {proof.metrics.cvar}")
print(f"Merkle Root: {proof.merkle_root}")
print(f"Decision: {proof.decision}")  # APPROVE ou BLOCK
```

#### 4. Armazenar e Indexar

```python
from storage.vectordb import VectorStore
from storage.ledger import LedgerStore

# Armazenar embeddings
vector_store = VectorStore()
vector_store.insert(extraction.embeddings, metadata=extraction.metadata)

# Armazenar proof no ledger
ledger = LedgerStore()
ledger.append(proof)

print("✅ Conhecimento armazenado e indexado")
```

## Exemplo Completo

```python
#!/usr/bin/env python3
"""
Exemplo completo: COG → PoSE → PoLE
"""

from cog.capture import CognitiveCapture
from pose.extractor import SemanticExtractor
from pole.proof import ProofGenerator
from storage.vectordb import VectorStore
from storage.ledger import LedgerStore

def process_learning_session(user_input: str, assistant_output: str):
    """Pipeline completo de processamento"""
    
    # 1. COG: Captura
    capture = CognitiveCapture()
    session = capture.capture_session(
        user_messages=[user_input],
        assistant_messages=[assistant_output]
    )
    
    # 2. PoSE: Extração semântica
    extractor = SemanticExtractor()
    extraction = extractor.extract(session)
    
    # 3. PoLE: Geração de prova
    generator = ProofGenerator()
    proof = generator.generate(extraction)
    
    # 4. Storage: Armazenamento
    if proof.decision == "APPROVE":
        vector_store = VectorStore()
        vector_store.insert(extraction.embeddings, metadata=extraction.metadata)
        
        ledger = LedgerStore()
        ledger.append(proof)
        
        print(f"✅ Sessão aprovada e armazenada")
        print(f"   Ψ: {proof.metrics.psi}")
        print(f"   Ω: {proof.metrics.omega}")
    else:
        print(f"❌ Sessão bloqueada (Ω < 0.85)")
    
    return proof

# Executar
proof = process_learning_session(
    user_input="Explique WireGuard",
    assistant_output="WireGuard é um protocolo VPN moderno..."
)
```

## Configuração Detalhada

### config.yaml

```yaml
version: "1.0.0"

cog:
  sources:
    - chat
    - documents
    - web
  max_session_size: 10000  # caracteres

pose:
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  embedding_dim: 384
  classifier:
    domains:
      - security
      - networking
      - cryptography
      - architecture

pole:
  metrics:
    psi_threshold: 0.70
    omega_threshold: 0.85
    cvar_max: 0.10
  merkle:
    hash_algorithm: sha3-256
  pqc:
    algorithm: dilithium3  # NIST PQC

storage:
  vectordb:
    type: qdrant
    host: 10.0.0.1
    port: 6333
    collection: matverse-knowledge
  ledger:
    path: /var/lib/matverse/ledger/lua-proofs.log
  graphdb:
    type: neo4j
    uri: bolt://10.0.0.1:7687
```

## Métricas e Governança

### Registry de Proofs

```json
{
  "version": "1.0.0",
  "timestamp": "2026-02-13T12:00:00Z",
  "source": "MatVerse LUA",
  "proofs": [
    {
      "proof_id": "sess_a1b2c3d4",
      "type": "Learning-Session",
      "timestamp": "2026-02-13T12:00:00Z",
      "session_data": {
        "concepts_extracted": 15,
        "facts_extracted": 8,
        "embeddings_dim": 384
      },
      "metrics": {
        "psi": 0.92,
        "omega": 0.89,
        "cvar": 0.03,
        "theta": 0.95
      },
      "merkle_root": "0x9f86d081884c7d659a2feaa0c55ad015...",
      "signature_pqc": "0x1234567890abcdef...",
      "decision": "APPROVE"
    }
  ],
  "statistics": {
    "total_proofs": 1,
    "average_psi": 0.92,
    "average_omega": 0.89,
    "average_cvar": 0.03
  }
}
```

### Auditoria

```bash
# Auditar registry de proofs
python scripts/audit-registry.py --registry=governance/registry.json

# Verificar assinaturas PQC
python scripts/verify-signatures.py --registry=governance/registry.json

# Gerar relatório de qualidade
python scripts/quality-report.py --output=reports/quality-$(date +%Y%m%d).md
```

## Operações

### Coletar Métricas de Repositórios GitHub

```bash
# Coletar métricas reais do GitHub
python scripts/collect-metrics.py \
  --org=MatVerse-py \
  --repos=matverse-u-core,matverse-u-network,matverse-u-gate \
  --output=governance/github-metrics.json
```

### Gerar Proof Manualmente

```bash
# Gerar proof de uma sessão específica
python scripts/generate-proof.py \
  --session-id=sess_a1b2c3d4 \
  --output=governance/proofs/sess_a1b2c3d4.json
```

### Consultar VectorDB

```python
from storage.vectordb import VectorStore

store = VectorStore()

# Buscar conhecimento similar
results = store.search(
    query="Como funciona WireGuard?",
    top_k=5,
    filter={"domain": "networking"}
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Texto: {result.text}")
    print(f"Metadata: {result.metadata}")
```

## Segurança

### Assinatura Pós-Quântica (PQC)

O LUA usa **Dilithium3** (NIST PQC) para assinar proofs, garantindo resistência a ataques quânticos.

```python
from pole.pqc import DilithiumSigner

signer = DilithiumSigner()

# Gerar par de chaves
keypair = signer.generate_keypair()

# Assinar proof
signature = signer.sign(proof_data, keypair.private_key)

# Verificar assinatura
is_valid = signer.verify(proof_data, signature, keypair.public_key)
```

### Merkle Tree

Cada proof é parte de uma Merkle Tree, permitindo verificação eficiente de integridade.

```python
from pole.merkle import MerkleTree

tree = MerkleTree(hash_algorithm='sha3-256')

# Adicionar proofs
tree.add_leaf(proof1.hash())
tree.add_leaf(proof2.hash())
tree.add_leaf(proof3.hash())

# Obter root
root = tree.get_root()

# Gerar proof de inclusão
inclusion_proof = tree.get_proof(proof2.hash())

# Verificar inclusão
is_included = tree.verify_proof(proof2.hash(), inclusion_proof, root)
```

## Performance

### Métricas Esperadas

| Métrica | Valor |
|---------|-------|
| Latência COG | < 100ms |
| Latência PoSE | < 2s |
| Latência PoLE | < 500ms |
| Throughput | ~50 sessões/min |
| Memória | < 500MB |

## Referências

- [MatVerse Core](../matverse-u-core) - Sistema Core + Twin
- [MatVerse Network](../matverse-u-network) - Infraestrutura WireGuard
- [MatVerse Gate](../matverse-u-gate) - Autenticação SIWE
- [MatVerse Docs](../matverse-u-docs) - Documentação consolidada
- [NIST PQC](https://csrc.nist.gov/projects/post-quantum-cryptography) - Criptografia pós-quântica

---

**MatVerse LUA** - O conhecimento é provado, não apenas armazenado.
