#!/usr/bin/env python3
"""Watch a CAD-loop workflow journal. After each completed 'review #N' (min <= N <= max), launch an
Orca Claude session in alex-3d-skills: "Revision run for <tag> attempt N". Waits while another agent is
working in that workspace so revision runs never overlap (they commit to the same repo).
Usage: revision_watcher.py <journal.jsonl> <tag> <min> <max> [extra prompt text]"""
import json, subprocess, sys, time, pathlib, datetime

JOURNAL, TAG, LO, HI = pathlib.Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
EXTRA = sys.argv[5] if len(sys.argv) > 5 else ""
REPO = pathlib.Path.home() / "code-stuff/alex-3d-skills"
HERE = pathlib.Path(__file__).resolve().parent
STATE = HERE / f".watcher-{TAG}.json"; LOG = HERE / "watcher.log"
WT = "id:a3e13da0-f00d-4f5c-99cc-af1e90d84738::" + str(REPO)
ORCA = "/Applications/Orca.app/Contents/Resources/bin/orca"
DEADLINE = time.time() + 24 * 3600
state = json.loads(STATE.read_text()) if STATE.exists() else {"launched": []}

def log(m):
    with LOG.open("a") as f: f.write(f"{datetime.datetime.now():%F %T} [{TAG}] {m}\n")

def reviews_done():
    labels, done = {}, []
    if not JOURNAL.exists(): return done
    for line in JOURNAL.read_text().splitlines():
        try: e = json.loads(line)
        except Exception: continue
        if e.get("type") == "started": labels[e["key"]] = e.get("label", "")
        elif e.get("type") == "result" and isinstance(e.get("result"), dict):
            lab = labels.get(e["key"], "")
            if lab.startswith("review #"): done.append(int(lab.split("#")[1]))
    return sorted(set(done))

def busy():
    try:
        d = json.loads(subprocess.run([ORCA, "worktree", "ps", "--json"], capture_output=True, text=True, timeout=60).stdout)
        for w in d["result"]["worktrees"]:
            if w.get("path") == str(REPO):
                return any(a.get("state") == "working" for a in w.get("agents", []))
        return False
    except Exception as ex:
        log(f"ps failed: {ex}"); return True

log(f"started journal={JOURNAL} range={LO}-{HI}")
while time.time() < DEADLINE:
    pending = [n for n in reviews_done() if LO <= n <= HI and n not in state["launched"]]
    if pending and not busy():
        n = pending[0]
        prompt = (f"Revision run for {TAG} attempt {n}. Follow the 'Revision runs' section of docs/HARVEST_BRIEF.md "
                  f"(including its 'Process change' section): read docs/STATUS.md and docs/FINDINGS.md, ingest only this attempt's new data "
                  f"(workflow journal {JOURNAL}, the review #{n} entry and its attempt's agent transcripts in that directory, and the attempt's renders dir), "
                  f"add findings, improve and re-verify the skills/tools (verify_all.sh must pass before every commit), update STATUS, commit. {EXTRA}")
        r = subprocess.run([ORCA, "agent", "launch", "--agent", "claude", "--worktree", WT, "--prompt", prompt, "--json"],
                           capture_output=True, text=True, timeout=120)
        log(f"launched attempt {n}: rc={r.returncode} {r.stdout[:200]!r} {r.stderr[:200]!r}")
        state["launched"].append(n); STATE.write_text(json.dumps(state))
    if HI in state["launched"]: log("range complete; exiting"); break
    time.sleep(60)
log("exiting")
