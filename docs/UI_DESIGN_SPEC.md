# M.A.R.S. UI Design Specification

**Product:** M.A.R.S. (Multifunctional Autonomous Reasoning System)  
**Stage:** Foundation / v0.1  
**Workstream:** Desktop web interface  
**Status:** Initial design direction

## 1. Product feel

M.A.R.S. should feel like a private builder's studio: a practical command surface for reasoning, research, software work, and eventually market analysis. It must not look like a generic AI chat clone or imply capabilities that are not implemented.

Design principles:
- Utility before decoration.
- Clear system state and visible permission boundaries.
- Calm, dense-enough information layout with generous spacing.
- Every panel has a real purpose.
- Capabilities are marked as available, in progress, or planned.

## 2. Visual system

### Color tokens

| Token | Value | Use |
|---|---|---|
| Obsidian | `#0A0A0D` | Main application background |
| Graphite | `#15151B` | Sidebar, cards, secondary surfaces |
| Raised surface | `#1D1D25` | Inputs, hover surfaces, nested panels |
| Border | `#30303A` | Dividers and panel outlines |
| Signal lime | `#D7FF64` | Primary action, selected state, meaningful live indicators |
| Mist | `#E7E7EC` | Primary text |
| Muted | `#9696A2` | Secondary labels and metadata |
| Danger | `#FF6B6B` | Errors and risky actions only |

Use lime sparingly. Do not use gradients, constant glow effects, or decorative charts.

### Typography

- Interface: Geist, Inter, or a similar neutral sans-serif.
- Technical metadata, code, IDs, timestamps: JetBrains Mono.
- Headings should be compact and editorial, not oversized marketing typography.

### Shape and spacing

- Panels: 10–14px radius.
- Inputs and buttons: 8–10px radius.
- Thin borders over heavy shadows.
- Consistent 4px spacing scale.
- Motion should be subtle and respect reduced-motion preferences.

## 3. Desktop application shell

Target initial viewport: 1440 × 900. Support smaller laptop screens gracefully.

### Left navigation rail

Width: approximately 224px.

- M.A.R.S. mark and wordmark.
- New session.
- Home.
- Workspace.
- Projects.
- Research.
- System Lab.
- Settings at the bottom.

Only show destinations that exist. Planned features must not appear as functioning tools.

### Main workspace

The default Home screen contains:

1. Compact top bar with current workspace, session status, and settings.
2. A concise greeting and one-line prompt.
3. Main composer with clear submit action.
4. Quick actions for available capabilities.
5. Recent sessions or projects, once persistence is available.
6. A small activity/status area that shows real events only.

Avoid a permanently visible right sidebar in the first iteration. Use a contextual inspector only when selected content needs it.

## 4. Core screens

### Home / Command Centre
- Main conversation composer.
- Quick access to implemented capabilities.
- Recent sessions when backed by real data.
- Empty states that explain what can be done now.

### Workspace / Conversation
- Message history.
- Composer with submit, loading, and error states.
- Clear indication when a tool is being used.
- Source links for research results.
- Permission prompt or approval state when a tool requires permission.
- Retry and copy actions where useful.

### System Lab
- Capability registry with status: available, experimental, planned, or unavailable.
- Backend/API health checks only when a real health endpoint exists.
- Request/response inspection for development mode, with secrets redacted.
- Recent errors and test results if the backend exposes them.
- No fabricated metrics or fake live telemetry.

### Projects
- Initially a useful empty state or a list backed by actual project data.
- Do not create nonfunctional project cards just to fill space.

## 5. Interaction rules

- Enter submits only when safe; Shift+Enter creates a new line.
- Show loading state while a request is running.
- Preserve the user's input if a request fails.
- Use inline error messages with a retry path.
- Keyboard focus must be visible.
- Buttons need labels or accessible names.
- Color is never the only way to communicate status.
- Tool permissions and any consequential actions must be explicit.
- Never expose API keys, environment variables, or sensitive tool payloads in the UI.

## 6. Backend integration contract

Keep UI and API integration separate. Do not change backend behavior merely to satisfy the visual layer.

Before wiring screens, inspect the current backend entry points and public interfaces. Prefer a thin API adapter and typed response models. If no stable HTTP API exists yet, build the visual shell with a clearly isolated mock adapter and label mock data as development-only.

Expected integration needs:
- Submit a user message and receive a response.
- Display conversation/session IDs if the backend supports them.
- Render tool activity and source citations if returned.
- Surface permission denials and errors clearly.
- Read capability/system status only from a real endpoint or registry.

## 7. Implementation sequence

1. Establish the design tokens and application shell.
2. Build the Home screen and responsive desktop layout with clearly labelled development data.
3. Add conversation states: empty, sending, response, tool activity, error.
4. Add System Lab with real backend status when an endpoint is available.
5. Replace the mock adapter with the actual API contract.
6. Add tests for navigation, composer behavior, loading, errors, and permission states.
7. Review keyboard accessibility, contrast, and small-laptop layouts.

## 8. Definition of done for the first UI milestone

- A coherent dark desktop shell with the M.A.R.S. identity.
- Home and conversation screens are navigable.
- Composer handles submit, loading, and error states.
- Mock data is clearly isolated and cannot be mistaken for live system status.
- No invented backend endpoints.
- No secrets in client code.
- README includes exact local run instructions once the frontend stack is selected.
