# MARS architecture

## Core
Own orchestration and stable interfaces. The core must not depend on one model vendor.

## Memory
Implemented:
- long-term user and project memory
- searchable memories
- explicit save and forget operations
- duplicate-safe storage

Planned:
- short-term conversation state
- timestamps and provenance
- richer retrieval and memory lifecycle controls

## Tools
MARS tools are isolated behind a registry.

Each tool exposes:
- a stable name
- description
- input schema
- required permission
- normalized execution result

The registry handles registration, lookup, duplicate protection, and permission checks before execution.

Initial permission levels:
- read
- write
- external_action

Actual web, filesystem, code-execution, GitHub, calculator, and external-API tools will be added behind this boundary rather than embedded in the reasoning core.

## Capabilities
Initial boundaries:
- writing
- programming
- research
- market analysis
- task planning
- automation

Capabilities should compose tools instead of owning vendor-specific integrations.

## Trading
Trading stays isolated.

Flow:
analysis -> strategy -> risk validation -> permission -> execution

The trading layer must enforce capital-protection rules independently of model output.

Trade-Oracle is the planned specialist trading capability for MARS. MARS should orchestrate it rather than duplicate its trading logic.

## Interfaces
The core should work through:
- CLI during development
- web application
- Telegram
- future voice interface

Interfaces must not contain core reasoning logic.

## Provider abstraction
The model provider is replaceable. No single vendor should become a hard dependency.