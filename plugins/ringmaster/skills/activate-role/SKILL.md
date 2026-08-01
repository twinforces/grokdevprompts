---
name: activate-role
description: Activate a Ringmaster coding role (Architect, Implementer, Reviewer, Tester) by reading the full vendored Core Values note, after a hygiene checkpoint. Use when the user says "activate role", "switch to Architect/Implementer/Reviewer/Tester", "/activate-role", or asks for a role switch with Core Values load.
argument-hint: "[architect|implementer|reviewer|tester] [reason]"
---

# Activate Role (Ringmaster pack)

Switch the main agent into a coding role using the **full file-read** protocol. Core Values are vendored in this plugin (no Obsidian).

## Role → reference file

| Role | Reference under `references/` |
|---|---|
| Architect | `architect-core-values.md` |
| Implementer | `implementer-core-values.md` |
| Reviewer | `reviewer-core-values.md` |
| Tester | `tester-core-values.md` |

Also useful: `role-definitions-for-routing.md`, `master-prompt.md`.

Resolve plugin root via `${GROK_PLUGIN_ROOT}` or `../../references/` from this skill directory.

## Activation steps (exact)

1. **Explicit role declaration**  
   State the role and reason (from user args, routing, or prior handoff).

2. **Hygiene checkpoint**  
   Run the same checks as `/hygiene` (brief is fine): RECENTGOALS/CHANGELOG touch, commit consideration, runnable→docs gaps, nags if warranted.  
   Prefer invoking the hygiene skill workflow rather than inventing a lighter process.

3. **Load full Core Values**  
   Read the complete role reference file above. Confirm internalization in one short sentence (mental model keywords, not a dump).

4. **Operate**  
   All subsequent work in this turn/phase stays under those values until the next explicit switch.

## Args

- First arg: role name (case-insensitive). If missing, ask once.
- Remainder: optional reason string.

## Do not

- Use condensed/inlined role summaries instead of reading the file.
- Skip hygiene at serious-work transitions.
- Load Obsidian vault paths unless the user asks for vault override.
