# wait-credit-guard.py

Pairing for `plugins/ringmaster/hooks/bin/wait-credit-guard.py`.

- **What:** Pre/Post tool hook that estimates the first wait, then steps through human-scale rungs: instant (estimate), coffee (15m), lunch/overnight (1h).
- **Why:** The parent agent pays for every "still running" poll in full-context tokens. A 10-minute cap still wakes a fat session all night. Overnight, hourly is enough. Advice in the prompt is easy to ignore; a deny with the next `timeout_ms` is not.
- **How:** `hooks/hooks.json` runs the script on wait/start/kill tools. Phase is elapsed wall time since start, not 2x-until-10m. Playbook: `Wait Credit Guard.md` / `plugins/ringmaster/references/wait-credit-guard.md`.
- **Run:** `python3 plugins/ringmaster/hooks/bin/wait-credit-guard.py --selftest`
