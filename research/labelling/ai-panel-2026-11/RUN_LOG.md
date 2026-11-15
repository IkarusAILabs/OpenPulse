# Run log: AI-panel round AP-1

All times 2026-11-01. Each reader ran as a background subagent of the orchestrating Claude Code session, in a new context, with a two-paragraph instruction to read its prompt file and nothing else. Session transcripts are kept by Claude Code under the session's `subagents/` directory; the tool calls below were extracted from them.

| Step | Model (from transcript) | Tool calls | Output |
|---|---|---|---|
| Packets and prompts built, hashes locked (`label_packets.py`) | — | — | `LOCK.json` `before_labelling` |
| Labeller A | `claude-opus-5-5` | 2 × Read of `prompt-labeller-A.md` (in parts); 1 × Write | `raw/labeller-A.jsonl`, 167 lines |
| Labeller B | `claude-sonnet-5-5` | 3 × Read of `prompt-labeller-B.md` (in parts); 1 × Write | `raw/labeller-B.jsonl`, 167 lines |
| Validation, hashes locked (`label_panel.py validate`) | — | — | both files valid, no retry needed; `LOCK.json` `labels` |
| Adjudication prompt built (`label_panel.py adjudication`) | — | — | 19 disagreements; `LOCK.json` `adjudication` |
| Adjudicator, planned | `claude-fable-5-1` | none: the run failed before any model call (HTTP 429, no usage credits for this model) | nothing written |
| **Deviation** recorded in `LOCK.json` `deviations` before re-running | — | — | adjudicator changed to Haiku 5.5 |
| Adjudicator, actual | `claude-haiku-5-5` | 5 × Read of `prompt-adjudicator.md` (in parts, two parts read twice); 1 × Write | `raw/adjudicator.jsonl`, 19 lines |
| Finalised, hashes locked (`label_panel.py finalise`) | — | — | unblinding permitted |
| Unblinded analysis (`label_sensitivity.py`) | — | — | `research/results/retro/label_sensitivity.json` |

Every reader's tool calls were limited to reading its own prompt file and one write of its answers. None listed, searched or read another file, ran a command or used the web.

The orchestrator did not open any label file before `finalise`. The two exceptions are mechanical: `validate`, which checks the format, and `adjudication`, which builds the adjudicator's prompt from the disagreed pairs.
