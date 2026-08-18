# Ringmaster: make Grok code like a senior, and stop paying full context to ask "still running?"

**Ringmaster** is a Grok Build plugin for serious coding. Four roles with real cognitive values. Hygiene so a long session is still a project when you come back. A hook that waits like a human instead of lighting the meter on fire.

The credit bill is how most people notice it. The pack is why they keep it.

By [@GrumpyTechBro](https://x.com/GrumpyTechBro) · [twinforces/grokdevprompts](https://github.com/twinforces/grokdevprompts) · plugin **v0.2.1**

---

## The bill you did not notice (the hook)

You background a test suite. Or a Docker build. Or a training run. Grok is supposed to wait.

What it actually does, once the session is fat:

1. Call `get_command_or_subagent_output`.
2. Hear "still running."
3. Become a **new parent turn**.
4. Re-send the **entire conversation** to find that out.
5. Do it again in 30 seconds. That is the tool default.

Turn 2, that poll is cheap. Turn 40, with a novel of tool output in context, each "just checking" costs real money. A twenty-minute job at 30s polls is forty full-context wakes. A job that runs overnight at a 10-minute cap is still dozens of novel-length asks for "not yet."

This is not a model-quality problem. It is a harness habit. Agents hate sitting still. They snapshot-poll. Advice in the system prompt does not survive time pressure.

**wait-credit-guard** is the piece that says no. Wait like a person:

| Rung | Meaning | Wait |
|---|---|---|
| **Instant** | You think it is about to finish | Command estimate (1–5 min typical) |
| **Coffee** | You would go get coffee | 15 min |
| **Lunch / overnight** | Hours. Morning is soon enough. | 1 hour |

If you already know it is overnight, start at lunch. The hook follows **elapsed wall time**, not a 2× ladder that caps at 10 minutes. A snapshot poll of a known-running task is **denied**. Finished work returns immediately even on a 1h wait.

Prompt-only was tried. Agents ignored it. The hook is why the meter stops spinning.

That is a good reason to install the plugin. It is a bad reason to stop reading.

---

## The actual problem

Grok's coding is mediocre out of the box. "Expert coder" tends toward overengineered sludge: extra abstractions, no *why*, a session that cannot be resumed by tired-you tomorrow.

A long TUI session makes it worse. Context gets huge. Roles blur. Commits get skipped. Docs never happen. Subagents get spawned because parallelism feels like progress. Background jobs get polled because sitting still feels like slacking.

You do not need a smarter autocomplete. You need a **circus boss**: one main agent that stays in the driver's seat, puts on the right hat, writes the history, and does not set money on fire while cargo thinks.

That is Ringmaster.

---

## What Ringmaster is

A self-contained Grok Build plugin. Playbooks live in the pack.

| Piece | Job |
|---|---|
| **Master prompt** | Session OS. You are the Ringmaster of the coding circus. |
| **Four Core Values notes** | Architect, Implementer, Reviewer, Tester. Loaded in full on every role entry. No condensed cheat sheet to rot. |
| **Hygiene playbook** | `docs/RECENTGOALS.md`, `CHANGELOG.md`, runnable code paired with Why-first docs, early commits. |
| **Skills** | `/bootstrap-prompt`, `/hygiene`, `/activate-role`. |
| **wait-credit-guard hook** | Human-scale waits. Trusted plugin. Deny, not a sermon. |

Philosophy, in one pass:

- The **main agent** does most of the work. Role switching inside one head is the default.
- **Subagents** are a power tool (true parallelism, isolation, background docs), not the architecture.
- **Code is a river.** Everything is optimized for future-you coming back under imperfect conditions: tired, stressed, 3am, one too many margaritas.
- Serious work follows the flow. Throwaways can skip it. The Ringmaster decides.

---

## Four hats, actually different brains

Default flow for serious work:

**Architect → Implementer ↔ Reviewer → Tester**

| Role | You put this hat on when | The brain |
|---|---|---|
| **Architect** | You do not understand the system yet, or the shape is wrong | Mental model of the *system* (people, tooling, evolvability), not the next function |
| **Implementer** | It is time to write or change code | 3am Saturday CEO on the phone. Clarity over clever. DRY because copying copies bugs. Explain *why*. Do not fear refactor. |
| **Reviewer** | A slice is reviewable | The best way to teach a junior is during review. Code that smells always breaks. Send work back. |
| **Tester** | It looks done | Implementing is not testing. Deliberate pessimist. Edge cases, failure modes, how it will actually be validated. |

Activation is a protocol, not a vibe:

1. Say the role and why.
2. Hygiene checkpoint (the Ringmaster never drops this).
3. **Read the full Core Values file.** Every entry and re-entry. No memory of last time.
4. Operate as that role until the next explicit switch.

Roles have agency. They can hand off ("this is reviewable," "we need the Architect"). The Ringmaster still owns coordination and hygiene. That hybrid is the point: hats are real, the circus does not run itself.

Quick experiment? Skip hats. Serious work? Do not let the model stay in "helpful intern who types a lot."

---

## Hygiene is not optional on serious work

Long sessions die when the only history is the scrollback.

Ringmaster owns:

- **`docs/RECENTGOALS.md`** — short scratchpad. What / Why / How + hash.
- **`docs/CHANGELOG.md`** — durable history, including what did *not* work.
- **Docs pairing** — a new runnable file gets a Why-first `docs/*.md`. What the code does is in the code. Why it exists is the part that survives.
- **Early commits** — after a meaningful slice, not after the novel.
- **Nagging** — on serious work only. Throwaway spikes are left alone.

Hygiene runs at every role transition, which is exactly when it is easiest to skip. Bootstrapping a new session starts by reading `docs/`, not by guessing.

This is how "code is a river" stays true when you close the laptop.

---

## Subagents, used like a grown-up

Default: stay in one agent and switch hats.

Spawn a child when it adds clear value:

- Background docs while you keep implementing.
- Two independent reviews on different modules.
- Isolation for a risky refactor.
- Persistent watch during a long operation (tight filters; terminal events only).

Do not spawn because the prompt said "use subagents." Depth is one. The Ringmaster integrates results and still owns hygiene.

---

## The credit guard, in that world

Once you are actually doing serious work, sessions get long. That is when the poll loop becomes a tax on the whole pack: every "still running?" re-sends the Architect plan, the review comments, the test dump.

So the same plugin that makes Grok wear the right hat also:

- Estimates the first wait from the command (or takes 1h if *you* know it is overnight).
- Steps **instant → coffee (15m) → lunch/overnight (1h)** by elapsed time.
- Denies snapshot and short polls while the task is running.
- Drops state on complete / fail / kill. First glance is free. Hook crash fails open.

Monitors emit `DONE` / `FAILED` / `CANCELLED`, not progress. Overnight `/loop` is 1h, not 60s.

The guard protects the budget so the rest of Ringmaster can afford to exist.

---

## How you actually use it

| Invoke | What happens |
|---|---|
| `/bootstrap-prompt` or `/bootstrap` | Load the master prompt as session OS |
| `/hygiene` | RECENTGOALS / CHANGELOG / docs pairing / commit checkpoint |
| `/activate-role architect` (etc.) | Hygiene, then full Core Values read, then operate as that role |

Then work. The Ringmaster should declare hat changes out loud. You can force a switch. You can say "hygiene" when the river is getting muddy.

Confirm the pack loaded: `grok plugin details ringmaster` should show **v0.2.1** and **hooks**.

---

## Install

```bash
grok plugin marketplace add twinforces/grokdevprompts
grok plugin install ringmaster --trust
grok plugin enable ringmaster
```

Already have it?

```bash
grok plugin update ringmaster
```

Then `/plugins` → `r`, or a new session. **Trust matters:** skills load when the plugin is enabled; hooks stay inert until trusted (`--trust`, or a copy under `~/.grok/plugins/`).

In-session: `/bootstrap-prompt`. That is the OS. The hook runs whether or not you remember the wait rules.


github.com/twinforces/grokdevprompts
```
