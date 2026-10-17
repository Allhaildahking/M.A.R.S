# MARS architecture

## Core
Own orchestration and stable interfaces. The core must not depend on one model vendor.

## Agent loop
MARS now supports a bounded model-driven tool loop:

1. Build system, history, memory, and tool catalog.
2. Ask the provider for a structured model turn.
3. If there are no tool calls, return the model's answer.
4. If tool calls are requested, execute each through the ToolRegistry.
5. Feed normalized tool results back into the conversation.
6. Ask the model to reason again.
7. Stop after a configurable maximum number of tool rounds.

The registry remains the enforcement point. Model output can request an action, but it cannot grant itself permission.

## Memory
Implemented:
- long-term user and project memory
- searchable memories
- explicit save and forget operations
- duplicate-safe storage
- short-term in-memory conversation sessions
- session-aware responses and session isolation

Planned:
- timestamps and provenance
- richer retrieval and memory lifecycle controls
- durable conversation history across restarts

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

Implemented read-only research tools:
- `web_search`: searches public web indexes and returns titles, snippets, and source URLs
- `web_fetch`: retrieves public HTTP(S) pages and extracts readable text
- page size and extracted text are capped; local/private network targets and unsafe redirects are rejected
- web content is untrusted input and must not override system instructions

The web search provider is the `ddgs` metasearch package. Search quality and availability depend on its upstream engines. A search result is evidence to inspect, not proof that a claim is true.

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
