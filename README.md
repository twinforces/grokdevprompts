# grokdevprompts (Ringmaster)

Prompts and a **self-contained Grok Build plugin** for serious coding with Grok — four roles, hygiene, and a TUI + subagents master prompt.

By [@GrumpyTechBro](https://x.com/GrumpyTechBro).

## WHY

Grok's coding is mediocre out of the box. "Expert coder" tends toward overengineered sludge. This pack uses **senior** posture and four roles with distinct cognitive values, plus rules for when to switch:

| Role | Job |
|---|---|
| **Architect** | Plans; owns problem understanding |
| **Implementer** | Writes maintainable, pragmatic code |
| **Reviewer** | Makes sure the code doesn't suck |
| **Tester** | Makes sure the code works |

It also pushes **project hygiene** (RECENTGOALS, CHANGELOG, docs pairing, early commits) so long sessions stay continuous.

## Two ways to use this repo

### 1. Grok plugin (recommended — no Obsidian)

Installable pack under `plugins/ringmaster/`. Skills read vendored playbooks from `plugins/ringmaster/references/`.

```bash
# Clone (or use your existing checkout)
git clone https://github.com/twinforces/grokdevprompts.git ~/Development/grokdevprompts

# Marketplace install
grok plugin marketplace add ~/Development/grokdevprompts
# or: grok plugin marketplace add twinforces/grokdevprompts

grok plugin install ringmaster --trust
grok plugin enable ringmaster
```

Or symlink the plugin into the auto-trusted user plugins dir:

```bash
ln -sfn ~/Development/grokdevprompts/plugins/ringmaster ~/.grok/plugins/ringmaster
```

Optional `~/.grok/config.toml`:

```toml
[plugins]
enabled = ["ringmaster"]
```

Reload plugins in the TUI (`/plugins` → `r`) or start a new session.

| Invoke | What it does |
|---|---|
| `/bootstrap-prompt` or “bootstrap” | Load master prompt as session OS |
| `/hygiene` | Docs + commit hygiene checkpoint |
| `/activate-role architect` (etc.) | Hygiene → full Core Values read → operate as role |
| `/bootstrap` | Thin command alias for bootstrap |

Validate:

```bash
cd ~/Development/grokdevprompts
grok plugin validate plugins/ringmaster
```

### 2. Classic (copy into Obsidian / vault)

Root-level markdown notes for hand-copy or vault sync:

- `Master Prompt2 - TUI + Subagents (WIP).md`
- `coding-bootstrap.md`
- `Documentation and Commit Hygiene.md`
- `Architect Core Values.md` / `Implementer Core Values.md` / `Reviewer Core Values.md` / `Tester Core Values.md`
- `Role Definitions for Routing.md`

Tell Grok Build to read `coding-bootstrap.md` (or run `/bootstrap-prompt` if the plugin is installed).

## Layout

```
grokdevprompts/
  README.md
  *.md                              # human-facing / Obsidian-friendly titles
  .grok-plugin/marketplace.json     # marketplace index
  plugins/ringmaster/
    plugin.json
    skills/                         # bootstrap-prompt, hygiene, activate-role
    commands/bootstrap.md
    references/                     # kebab-case playbooks used by skills
```

**Source of truth for the plugin install** is `plugins/ringmaster/`. Root `*.md` files are the same content with readable titles for browsing and Obsidian; keep them aligned when you edit playbooks.

| Root note | Plugin reference |
|---|---|
| `Master Prompt2 - TUI + Subagents (WIP).md` | `references/master-prompt.md` |
| `coding-bootstrap.md` | `references/coding-bootstrap.md` |
| `Documentation and Commit Hygiene.md` | `references/documentation-and-commit-hygiene.md` |
| `Architect Core Values.md` | `references/architect-core-values.md` |
| `Implementer Core Values.md` | `references/implementer-core-values.md` |
| `Reviewer Core Values.md` | `references/reviewer-core-values.md` |
| `Tester Core Values.md` | `references/tester-core-values.md` |
| `Role Definitions for Routing.md` | `references/role-definitions-for-routing.md` |

## Share / remote

```bash
grok plugin marketplace add twinforces/grokdevprompts
grok plugin install ringmaster --trust
grok plugin enable ringmaster
```

## Feedback

I'm [@GrumpyTechBro](https://x.com/GrumpyTechBro) on X.
