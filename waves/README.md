# Waves: start cloud flights by pushing a text file

Push a new or edited `waves/<name>.txt` on any branch and the `arms` workflow flies it on PX4 SIH
(GitHub Actions, free for this public repo: 20 jobs in parallel, at most 256 jobs per wave).
Results land on the `results` branch in `results/<name>-<run id>/`, listed in `results/INDEX.md`,
and the owner gets one email (a comment on the "Cloud results" issue).

```text
# comments start with #
runs 10        # runs per scenario, 1-50 (default 5)
first 1        # first run index = seed (default 1); "first 11" with "runs 10" adds seeds 11-20
p11-lqr-alone p11-lqr-plus-mrac
p11-pid-alone  # scenario names = files scenarios/<name>.json, separated by spaces or new lines
```

- One push = one workflow run. Several wave files in one push fly as one run (label `a+b`);
  to go past 256 jobs, push the files one at a time.
- Editing a wave file and pushing again flies it again: the same `first` replicates, a new `first` adds seeds.
- A bad file (unknown scenario, invalid scenario JSON, more than 256 jobs) fails the plan job; the reason is
  the `error` field of `results/<name>-<run id>/meta.json`.
- A changed `px4-mrac/**` or `ci/build.sh` makes the run build PX4 from scratch first; compile errors land in
  `results/<name>-<run id>/build-tail.log`.
- Compare arms only inside one wave (same build, same runner pool) and pair them by `run`.
- `waves/archive/` holds the deck lists of waves flown before this trigger existed (A-G, 2026-11-04); copy one to
  `waves/` and set `first` to re-fly it. Files in subfolders never start a run.
