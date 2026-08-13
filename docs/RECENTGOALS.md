# RECENTGOALS

Living scratchpad. Older items migrate to `CHANGELOG.md`.

## Current

### Wait-credit-guard for long-running Grok tasks
- **What:** Human-scale waits: instant (estimate) → coffee (15m) → lunch/overnight (1h). Hook denies short/missing `timeout_ms` while the task is still running. If you know it is hours, start at 1h.
- **Why:** Each still-running poll is a full parent turn. A 10-minute cap still wakes a fat session all night. Overnight, hourly is enough.
- **How:** Elapsed wall time since start picks the rung (not 2x forever). Playbook + master prompt / coding-bootstrap. Plugin 0.2.1. Brochure covers the whole pack. Playbooks point at this repo only.
- **Hash:** `c496008` (0.2.0 was `282fa98`); brochure refresh pending
