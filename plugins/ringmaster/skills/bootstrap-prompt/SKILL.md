---
name: bootstrap-prompt
description: Load the Ringmaster master prompt and treat it as session operating instructions. Use when the user says "bootstrap prompt", "bootstrap", "/bootstrap-prompt", or asks to load the Ringmaster / TUI + Subagents master prompt.
---

# Bootstrap Prompt (Ringmaster pack)

Load the vendored Ringmaster master prompt and follow it for the rest of the session. **No Obsidian required.**

## Note location (self-contained)

Prefer, in order:

1. Plugin references (when this skill is loaded from the ringmaster plugin):

   ```
   ${GROK_PLUGIN_ROOT}/references/master-prompt.md
   ```

   If `GROK_PLUGIN_ROOT` is unset, resolve relative to this skill file:

   ```
   <plugin-root>/references/master-prompt.md
   ```

   From this skill directory that is:

   ```
   ../../references/master-prompt.md
   ```

2. Repo checkout (when developing the marketplace itself):

   ```
   plugins/ringmaster/references/master-prompt.md
   ```

## Steps

1. **Read** `references/master-prompt.md` in full (file tools).
2. **Internalize** as session operating instructions (Ringmaster identity, role routing, sub-agent policy, hygiene ownership, global rules).
3. **Acknowledge briefly**
   - Confirm loaded (title + that it came from the plugin pack).
   - List 3–7 non-negotiables or active directives in short bullets.
   - Do **not** paste the entire prompt unless asked.
4. **Proceed** under those rules. If the user only said "bootstrap prompt", stop after the summary and wait.

## Related pack skills

- `/hygiene` — project documentation and commit hygiene checkpoint
- `/activate-role` — switch role with full Core Values read from pack references
- Long-running waits: follow `references/wait-credit-guard.md` (instant / coffee / lunch-overnight). A trusted hook denies tight polls.

## Do not

- Fall back to Obsidian paths unless the user explicitly wants vault sync.
- Silently use a different master prompt without saying so.
