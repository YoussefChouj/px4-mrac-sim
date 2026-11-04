# Agent guide (also for cloud and phone sessions)

PX4 v1.17.0 simulation side of a master's thesis: multi-time-scale MRAC layers (rate, attitude, vz, XY accel) on top
of any baseline controller (PX4 PID, LQR, ADRC, MPC), flown in PX4 SIH. The owner (YoussefChouj) decides plans; agents
run experiments, analyse and write up. Everything an agent needs is in this repo and on its `results` branch.

## Read first
1. This file, then `research/HANDOFF.md` (state, caveats, open questions, next items in order).
2. `research/OPEN-ITEMS.md` (all items) and the last ~150 lines of `research/PROGRESS.md` (dated findings, append-only).
3. If the previous session's branch is not merged into main yet (`git ls-remote origin 'refs/heads/claude/*'`, compare
   its `research/HANDOFF.md`), merge it into your branch first: `git fetch origin <branch> && git merge FETCH_HEAD`.

## Fly: push a wave file
- Scenario = `scenarios/<name>.json` (params + flight script; copy a close one). Metric fields: `agent/arms.py`.
- Wave = `waves/<name>.txt` with `runs N`, `first N` and scenario names (`waves/README.md`). Past waves: `waves/archive/`.
- Commit it and push your branch: the `arms` workflow flies it on GitHub Actions (free for this public repo).
  One push = one run = one email to the owner, so batch decks into one wave. At most 256 jobs (scenarios x runs)
  per push; 20 fly at once.
- Measured 2026-11-04: 7 runs (870 flights) from one cached build took 22.6 min; a fly job takes a median 36 s.
- A change to `px4-mrac/**` or `ci/build.sh` makes the run compile PX4 first; a compile error ends the run with
  `build-tail.log` in its results folder. That is the only build path: do not compile PX4 in the session.

## Wait: one background loop, right after the push
```bash
S=$(git rev-parse HEAD | cut -c1-7); for i in $(seq 90); do git fetch -q origin results 2>/dev/null && git show FETCH_HEAD:results/INDEX.md | grep -q "$S" && break; sleep 30; done
```
If git fetch is blocked: `curl -s https://raw.githubusercontent.com/YoussefChouj/px4-mrac-sim/results/results/INDEX.md`.
Run status: `curl -s "https://api.github.com/repos/YoussefChouj/px4-mrac-sim/actions/runs?branch=<branch>&per_page=3"`
(no token: 60 requests per hour).

## Read results (`results` branch; only CI writes it, never push to it)
- `results/INDEX.md`: one row per run, newest first (finished UTC, wave, branch, sha, pass / jobs, lost, job states, folder).
- `results/<wave>-<run id>/`: `summary.md` (per-deck medians), `meta.json` (counts, lost jobs, plan error), `all.json`
  (`{deck: [one record per flight]}`, `run` = seed index), `logs/<job>.log` (fly-log tail of each failing job),
  `build-tail.log` (compile errors).
- Copy a folder out: `mkdir -p ~/res && git archive FETCH_HEAD results/<folder> | tar -x -C ~/res`.

## Rules
- Simulation only. The repo is public: no secrets, tokens, emails or private documents in it.
- Never edit `.github/workflows/` (the session's GitHub app may lack that permission): write the wanted change under
  "Desktop-only" in `research/HANDOFF.md`. Change `ci/*.py` only when an item needs it, after testing it locally.
- Stage by path (`git add <file>`), never `git add -A`. Push only your session branch.
- Numbers: measured only, each with its source (results folder or run id); estimates are marked [S].
- A failed gate is a result: record it, and never loosen a gate to make an arm pass.
- Compare arms only inside one wave (same build, same runners), paired by `run`. More seeds: the same wave file
  with `first 11`, control arms included.
- One finding = one dated entry at the end of `research/PROGRESS.md`. Before you end: update `research/HANDOFF.md`
  (state + next) and the status in `research/OPEN-ITEMS.md`, push, and open a PR to main (or give the owner the
  branch name) so the next session starts from your state.

## Talking to the owner (often on a phone)
Bottom line first, then at most ~150 words: plain words, one small table at most, no log dumps. Propose the next step
with your recommendation and ask one decision at a time. The owner approves plan changes; inside the plan, keep going.
