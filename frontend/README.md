# M.A.R.S. Studio

Desktop-first web interface for M.A.R.S. (Multifunctional Autonomous Reasoning System).

## Current status
This is the first visual shell. Navigation, prompt entry, starter prompts, and local draft display work in the browser. The chat is **not connected to an AI model or backend**. System status labels are explicit about what is and is not connected.

## Requirements
- Node.js 20.9+
- npm

## Run locally
From this directory:

    npm install
    npm run dev

Open http://localhost:3000.

## Next steps
1. Agree on the backend's real API contract.
2. Add a typed API adapter without changing backend behavior.
3. Replace the local draft flow with actual session/message requests.
4. Read system and tool status only from real backend responses.
5. Add UI tests for navigation, composer, errors, and permission states.
