# Stop paying full context to ask "still running?"

**wait-credit-guard** is in Ringmaster 0.2.1. It keeps Grok from burning your credits on long jobs.

By [@GrumpyTechBro](https://x.com/GrumpyTechBro) · [twinforces/grokdevprompts](https://github.com/twinforces/grokdevprompts)

---

## The bill you did not notice

You background a test suite. Or a Docker build. Or a subagent. Grok is supposed to wait.

What it actually does, once the session is fat, is worse:

1. Call `get_command_or_subagent_output`.
2. Hear "still running."
3. Become a **new parent turn**.
4. Re-send the **entire conversation** to find that out.
5. Do it again in 30 seconds. That is the tool default.

Turn 2 of a session, that poll is cheap. Turn 40, with a novel of tool output in context, each "just checking" costs real money. A twenty-minute job at 30s polls is forty full-context wakes. The completion notification was almost free. The poll loop is what ate the budget.

This is not a model-quality problem. It is a harness habit. Agents hate sitting still. They snapshot-poll. Advice in the system prompt does not survive time pressure.

## What we shipped

**Wait like a human. Enforce it with a hook, not a suggestion.**

People do not check a long job every 10 minutes. They check at:

| Rung | Meaning | Wait |
|---|---|---|
| **Instant** | You think it is about to finish | Command estimate (1–5 min typical) |
| **Coffee** | You would go get coffee | 15 min |
| **Lunch / overnight** | Hours. Morning is soon enough. | 1 hour |

If you already know it is an overnight training run, start at lunch. Do not open with a 1-minute guess.

If you are unsure, start at the instant estimate (`pytest` 2m, cargo/npm 3m, docker 5m, other shell 1m, subagent 3m). The hook watches **elapsed wall time** and walks you up: after a couple of minutes you are on coffee, after about 20 minutes you are on hourly, and you stay there until morning.

A snapshot poll of a task we already know is running gets **denied**. Finished work returns immediately even when `timeout_ms` is an hour.

Prompt-only was tried. Agents ignored it. A 10-minute cap was tried too. That still wakes a fat session all night. The hook is the product.

## What you do not lose

- First glance is still free. You can see whether it already finished.
- Kill / fail / complete drops the backoff. You are not locked out of the result.
- Hook crash fails open. A broken script never bricks the tool.
- If you have real other work, do that. Do not invent "check again" turns.

Monitors still exist. They should emit `DONE` / `FAILED` / `CANCELLED`, not progress spam. `/loop` for overnight "is it done yet" is 1 hour, not 60 seconds.

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

Then `/plugins` → `r`, or a new session. Hooks stay inert until the plugin is trusted. Confirm with `grok plugin details ringmaster` (want **v0.2.1** and **hooks**).

In-session: `/bootstrap-prompt` loads the Ringmaster OS, including this rule.

---

## Paste this on X

Single post (edit the link if you want a screenshot under it):

```
Grok will light your credits on fire waiting for a long job.

Every "still running?" is a full parent turn. The whole chat goes back over the wire. Do that every 30s on a fat session and you are paying novel-length context to learn nothing.

Ringmaster 0.2.1 has wait-credit-guard:

• wait like a human: instant, coffee (15m), lunch/overnight (1h)
• if you know it is hours, start at 1h
• snapshot polls of a running task are denied

Prompt advice was not enough. The hook says no.

github.com/twinforces/grokdevprompts
```

Thread if you want more room:

**1/7**
Grok has a quiet way to drain a coding session: it polls background work like a toddler on a road trip.

"Still running?"
"Still running?"
"Still running?"

Each ask is not a cheap peek. It is another full turn.

**2/7**
`get_command_or_subagent_output` comes back "still running" and the harness wakes the parent model.

That wake re-sends the entire conversation.

Early in a session: whatever.
Hour two, after reviews and test dumps: you just paid for War and Peace to hear "not yet."

**3/7**
Default wait is 30 seconds. A 20 minute Docker build is ~40 of those wakes.

The completion ping was fine. The loop is the bug. Agents do it because sitting still feels like slacking, and a system-prompt footnote loses to that instinct.

**4/7**
Ringmaster 0.2.1 ships wait-credit-guard.

Wait like a human: instant, cup of coffee (15m), lunch/overnight (1h).
If you know it is hours, the first wait is already 1h.
Omit timeout on a known-running task and the hook denies the call.

**5/7**
A 10-minute cap still wakes you all night. Overnight, hourly is enough.

The hook follows elapsed wall time. A job that has already been running for three hours skips the toddler rungs and goes hourly.

Finished work returns immediately even with a 1h timeout. You are not punished for a job that ends early.

**6/7**
We tried telling the model. It still snapshot-polled.

So this is a trusted plugin hook, not a sermon. Crash fails open. First glance is allowed. Kill/complete clears state.

**7/7**
Ringmaster is the rest of the pack too: Architect / Implementer / Reviewer / Tester, hygiene, bootstrap. This is the piece that stops the meter from spinning while cargo thinks.

github.com/twinforces/grokdevprompts

```
grok plugin marketplace add twinforces/grokdevprompts
grok plugin install ringmaster --trust
grok plugin enable ringmaster
```

Then `/plugins` → r. Look for v0.2.1 + hooks.

---

Shorter alt if you only want one punch:

```
New in Ringmaster: wait-credit-guard.

Grok was paying full-context rates to ask "still running?" every 30s. That's how long jobs eat a SuperGrok allotment.

Now: instant / coffee / lunch / overnight (hourly). Tight polls get denied.

github.com/twinforces/grokdevprompts
```
