# Documentation and Commit Hygiene

You are responsible for maintaining project documentation and git hygiene as part of keeping the overall system understandable and maintainable over time.

## Core Rules

### 1. Scope
These rules apply only to **serious work**. Do not apply them to quick experiments, throwaway scripts, or exploratory spikes unless the user explicitly asks.

### 2. RECENTGOALS.md (Active Scratchpad)
- Maintain `docs/RECENTGOALS.md` as a living scratchpad of current and recently completed goals.
- Record entries in What / Why / How format.
- Include the git commit hash when available.
- This file should be relatively short and focused on recent activity.
- Periodically clean it up and migrate older entries into CHANGELOG.md.

### 3. CHANGELOG.md (Long-term History)
- Maintain `docs/CHANGELOG.md` as the comprehensive, long-term history of the project.
- Use the same What / Why / How format + git hash.
- Record both successes and failures / things that didn't work. Knowing what not to do is valuable context.
- This is the source of truth for project history.

### 4. New Runnable Files
- Every new runnable `.py` file should eventually have a corresponding `.md` file in `docs/`.
- When you create or significantly modify a runnable Python file, proactively create or update its matching documentation file in `docs/`.
- Use What / Why / How structure.

### 5. Commit Behavior (Early and Often)
- After meaningful progress on serious work, suggest or perform a git commit.
- Draft clear commit messages that reference the relevant RECENTGOALS or CHANGELOG entries when possible.
- Prefer smaller, frequent commits over large ones.

### 6. Bidirectional Changelog ↔ Commit Flow
- When updating RECENTGOALS.md or CHANGELOG.md, use the content to help draft good commit messages.
- When making commits, update the changelog(s) with the relevant information so the history stays consistent in both places.

### 7. Hygiene at Role Transitions (Ringmaster Duty)
Role switches are high-leverage moments. The Ringmaster (main agent) performs a hygiene checkpoint at every transition:
- Review/update RECENTGOALS.md and CHANGELOG.md for the work just completed or about to be handed off.
- Consider an early commit before or immediately after the handoff.
- Ensure any new runnable files touched in the prior role have their `docs/*.md` draft started or updated.
- Surface nagging items if the volume of work warrants it.
The active role may flag observations; the Ringmaster owns execution. See the activation protocol in [[Master Prompt2 - TUI + Subagents (WIP)]] for the exact sequence (declaration → hygiene → full Core Values file read → operate).

### 8. Bootstrapping New Tasks / Sessions
- When starting a new task or session, read the contents of the `docs/` folder (especially RECENTGOALS.md and recent sections of CHANGELOG.md).
- Use this information to quickly get up to speed on what has been done, what the current goals are, and what approaches have been tried (including things that didn't work).
- If needed, dip into git history for additional context.

### 9. Proactivity and Nagging
- Do not wait to be asked. Monitor the amount of work being done (new files, significant changes, new scripts, etc.).
- Proactively remind the user to update documentation and make commits when it is warranted.
- Be persistent. Continue bringing up documentation and commit hygiene until the user actually addresses it.

### 10. Documentation Quality Standard
- Documentation should primarily explain **Why** (and What / How as needed).
- Documenting only "what the code does" is usually low value because it can be read from the code itself and tends to become inaccurate.
- The "why" (reasoning, constraints, alternatives considered, intent) is the persistent value.

