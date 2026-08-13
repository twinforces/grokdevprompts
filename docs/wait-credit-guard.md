# wait-credit-guard.py

Pairing for `plugins/ringmaster/hooks/bin/wait-credit-guard.py`.

- **What:** Pre/Post tool hook that estimates how long a background command or subagent should take, then requires geometric backoff on later collects.
- **Why:** The parent agent pays for every "still running" poll in full-context tokens. Advice in the prompt is easy to ignore; a deny with the next `timeout_ms` is not. Finished tasks still return immediately when retried with a large timeout.
- **How:** `hooks/hooks.json` runs the script on wait/start/kill tools. State is `$GROK_PLUGIN_DATA/wait-credit-guard.json`. Constants and the duration table live in the script; the human playbook is `Wait Credit Guard.md` (root) and `plugins/ringmaster/references/wait-credit-guard.md`.
- **Run:** `python3 plugins/ringmaster/hooks/bin/wait-credit-guard.py --selftest`
