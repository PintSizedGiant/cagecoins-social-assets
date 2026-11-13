#!/usr/bin/env python3
"""Record what a run did, so later runs skip duplicates and retries know whether to start.

  python3 tools/record.py posted build/manifest.json "KEY|PLATFORM" ["KEY|PLATFORM" ...]   append scheduled posts to log/posted.jsonl
  python3 tools/record.py run YYYY-MM-DD done|failed "reason or summary"                   write log/runs/YYYY-MM-DD.json
  python3 tools/record.py check YYYY-MM-DD                                                 prints DONE if today's run already finished"""
import json, os, sys, datetime as dt
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(REPO, "log")

def main():
    cmd = sys.argv[1]
    os.makedirs(os.path.join(LOG, "runs"), exist_ok=True)
    if cmd == "posted":
        m = {(p["key"], p["platform"]): p for p in json.load(open(sys.argv[2]))["posts"]}
        with open(os.path.join(LOG, "posted.jsonl"), "a", encoding="utf-8") as f:
            for kp in sys.argv[3:]:
                key, plat = kp.rsplit("|", 1); p = m[(key, plat)]
                parts = key.split("|")
                f.write(json.dumps(dict(key=key, platform=plat, template=p["template"], date=p["slot"][:10],
                                        ticker=parts[2] if p["template"] == "T7" and len(parts) > 2 else None), ensure_ascii=False) + "\n")
        print(f"recorded {len(sys.argv) - 3}")
    elif cmd == "run":
        day, status, text = sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else ""
        p = os.path.join(LOG, "runs", f"{day}.json")
        prev = json.load(open(p)) if os.path.exists(p) else {"attempts": []}
        prev["attempts"].append(dict(at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), status=status, note=text))
        prev["status"] = status
        json.dump(prev, open(p, "w"), indent=1, ensure_ascii=False); print(f"{day}: {status}")
    elif cmd == "check":
        p = os.path.join(LOG, "runs", f"{sys.argv[2]}.json")
        print("DONE" if os.path.exists(p) and json.load(open(p)).get("status") == "done" else "NOT DONE")

if __name__ == "__main__": main()
