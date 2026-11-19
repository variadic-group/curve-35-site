"""The steps, as the printed guide, the build manual, the films and the site have always read them, now read from the canon
(canon/steps.yaml and canon/parts.yaml; tools/canon.py).  Edit the YAML, not this file: change a step there and every document changes.
  BUILD 1 to 4 make the dark box, 5 to 10 the front plate.  A step is named by its section and number (BUILD 7, FILM IN 2) or its id (b7, f2).
  The kit booklet prints 'do' and 'check'; the build manual prints everything."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canon

_C = canon.load()
def _asset(pid): return _C["part"][pid].get("asset", pid)            # the older file stem its pictures use (the film is 'cassette')
def _step(s):
    st = dict(sec=s["section"], n=s["n"], img=os.path.splitext(os.path.basename(s["picture"]))[0], do=s["instruction"], check=s["check"], ifnot=s.get("mistake", ""),
              why=s.get("why", ""), parts=[(_asset(k), q) for k, q in (s.get("parts") or {}).items()], bursts=[tuple(b) for b in s.get("clicks") or []])
    if s.get("guide_short"): st["short"] = s["guide_short"]      # the printed guide's page has room for less
    return st
# STEPS: build, film in, photos, film out.  WEB: THE HOLE, the pinhole experiment (lesson 1), on the guide's page 15 and the website.
STEPS = [_step(s) for s in _C["steps"] if s["section"] != "THE HOLE"]
WEB = [_step(s) for s in _C["steps"] if s["section"] == "THE HOLE"]
CODE = {x["key"]: x["letter"] for x in _C["sections"]}
def code(st): return CODE[st["sec"]] + str(st["n"])        # b7, f2, h3: the clip's file name and the page's address
PARTS = [(k, _C["part"][k]["name"], _C["part"][k]["does"]) for k in _C["guide_order"]]
TROUBLE = [(t["problem"], t["cause"], t["fix"]) for t in _C["trouble"]]
