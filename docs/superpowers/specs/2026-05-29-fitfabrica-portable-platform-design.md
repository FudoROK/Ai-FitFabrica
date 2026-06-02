# AI FitFabrica Portable Platform Design

## Purpose

Replace the project's Google-first platform foundation with a single portable enterprise architecture that can run in any region, on any cloud, or on self-managed infrastructure, while keeping the agent/model layer pluggable.

This design changes the baseline of the whole project. It does not add another deployment option. It defines the only target platform architecture going forward.

## Approved Direction

AI FitFabrica will use:

- PostgreSQL as the primary source of truth
- Qdrant as the vector search engine
- S3-compatible object storage as the media/object storage layer
- Redis as the cache, ephemeral coordination, and short-lived state layer
- FastAPI as the backend orchestration layer
- Gemini plus Google ADK / Vertex agent tooling as the initial agent/model execution layer

This design removes Google Cloud from the role of foundational data platform. Google may remain in the AI provider layer only.

## Non-Goals

This design does not:

- keep two competing infrastructure stacks in parallel
- preserve Firestore as a primary system of record
- preserve GCS as the primary storage API
- require Vertex, ADK, or Gemini to own business state or persistence
- commit the project to Google-only deployment

## Architecture Principles

### One Platform Baseline

The project must have one platform baseline, not a Google-first baseline plus a portable alternative. Parallel platform variants create duplicate adapters, duplicate documentation, inconsistent operations, and long-term architecture drift.

### Backend Owns Truth

All business truth lives in backend-controlled storage:

- identities
- jobs
- workflow state
- billing and credits
- audit and compliance events
- media references
- embeddings metadata

Agents may read context and return structured outputs, but they do not own system truth.

### AI Provider Layer Is Replaceable

The model and agent layer is provider-swappable. The system must be able to keep the same domain model, workflow engine, storage, and APIs while changing:

- Gemini
- OpenAI
- Anthropic
- Qwen
- DeepSeek
- future internal or regional providers

This implies clear ports for:

- text and reasoning invocation
- image generation and editing
- embeddings generation
- agent runtime execution

### Workload Isolation

Transactional data, vector search, and object storage must not be collapsed into a single infrastructure component when that would create contention under production load.

The system should separate:

- OLTP and transactional consistency in PostgreSQL
- vector retrieval and ANN indexing in Qdrant
- binary object storage in S3-compatible storage

## Target Platform

### PostgreSQL

PostgreSQL is the system of record for all canonical entities and workflow state.

It stores:

- users
- B2C profiles
- B2B business profiles
- identities and bindings
- jobs and job state
- workflow events
- pricing and credits ledger
- product and catalog core records
- marketplace references
- quality verification records
- audit records
- permissions and policy state

PostgreSQL must be designed for enterprise operation:

- schema migrations
- strict constraints
- transactional integrity
- explicit indexes
- partitioning where justified
- read replicas where justified

### Qdrant

Qdrant is the vector database for similarity and retrieval workloads.

It stores and serves:

- garment embeddings
- product embeddings
- persona style embeddings
- visual similarity records
- search payload metadata required for filtered retrieval

Qdrant is chosen over pgvector as the final enterprise vector baseline because vector workloads should be isolated from primary OLTP pressure as the platform grows.

### S3-Compatible Object Storage

All large binary artifacts live in S3-compatible object storage.

This includes:

- uploaded human photos
- uploaded garment photos
- product photos
- masks
- intermediate media artifacts
- generated result images
- quality snapshots
- export packages

The storage contract must target the S3 API rather than a vendor-specific storage SDK so the project can run on:

- Yandex Object Storage
- AWS S3
- MinIO-compatible deployments
- other S3-compatible providers

### Redis

Redis is used only for short-lived operational concerns, not for canonical truth.

Typical uses:

- rate limiting
- idempotency keys with TTL
- distributed locks
- job dispatch coordination
- short-lived cache
- temporary polling acceleration

## Identity And Recognition Design

The identity and recognition contour must move out of Firestore and into the portable core platform.

### PostgreSQL Identity Records

Canonical tables should include:

- persons
- channel_identities
- identity_bindings
- person_profiles
- recognition_events
- identity_resolution_audit

These records require strong constraints, lifecycle transitions, revocation, supersession, and auditability. They should not remain in document storage as the primary implementation.

### Qdrant Recognition Vectors

Recognition and similarity vectors should live in Qdrant, not in PostgreSQL.

Typical vector domains:

- face embeddings
- body and silhouette embeddings
- garment embeddings
- style embeddings

### Object Storage Recognition Media

Recognition source media and derived artifacts should live in object storage.

Typical artifacts:

- source image
- normalized crop
- mask
- landmark artifact
- verification snapshot

## Agent Layer Design

The project may keep Gemini and Google ADK / Vertex AI Agent Builder as the first agent execution layer.

That layer must remain replaceable.

### Allowed Responsibilities

Agents may:

- reason
- classify
- rank
- propose actions
- generate structured JSON
- call backend-approved tools through explicit interfaces

### Forbidden Responsibilities

Agents must not directly own:

- canonical persistence
- billing state
- credit charging
- retry policy final authority
- identity truth
- workflow state truth

### Agent Provider Ports

The architecture should converge on explicit ports such as:

- AgentRuntimePort
- StructuredReasoningPort
- ImageGenerationPort
- ImageEditingPort
- EmbeddingProviderPort

## FitFabrica Workflow Mapping

### Try-On

- PostgreSQL stores job, status, cost, audit, references, and quality decisions
- Qdrant remains the platform vector layer for any Try-On-adjacent retrieval, similarity, and embedding-backed features
- S3-compatible storage stores uploads and results
- agent/model layer analyzes constraints and returns structured outputs

### Similar Product Search

- PostgreSQL stores product catalog and legal marketplace metadata
- Qdrant performs visual and semantic nearest-neighbor search
- backend combines similarity with pricing and marketplace filters

### Product Card And Content Package

- PostgreSQL stores versions, metadata, workflow records, and export references
- S3-compatible storage stores generated media and export bundles
- agent/model layer creates structured content drafts and generation instructions

### Persona And Style Profile

- PostgreSQL stores canonical profile data
- Qdrant stores style and look embeddings where needed
- object storage stores user-approved profile images

## Reliability Baseline

The target implementation must be production-ready under load.

### Core Reliability Requirements

- no silent failures
- typed error envelopes
- idempotent job submission and processing boundaries
- durable audit trail
- explicit timeout and retry policies
- queue and worker isolation for heavy workloads
- bounded synchronous request work
- background processing for generation and indexing

### Scaling Direction

Scale out should happen by role:

- API nodes
- worker nodes
- PostgreSQL primary plus replicas
- Qdrant cluster
- object storage
- Redis

The design should avoid a single giant process that performs API, orchestration, vector search, file IO, and heavy model work in one place.

## Migration Decision

The current Google-first persistence and storage assumptions are treated as transitional implementation history, not as the future target architecture.

Existing Firestore and GCS-backed code may remain temporarily during migration, but the final project baseline is:

- PostgreSQL
- Qdrant
- S3-compatible object storage
- Redis
- pluggable agent/model layer

## Planning Implication

This design changes the whole project plan.

The project must now be executed in this order:

1. Portable platform foundation
2. Identity and core data migration
3. Workflow persistence migration
4. Search and vector foundation
5. Media storage foundation
6. Agent/provider abstraction hardening
7. Product workflow expansion
8. Production reliability and operations

Detailed execution planning should reference this design as the new master architecture baseline.
