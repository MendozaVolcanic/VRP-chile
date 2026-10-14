"""Cuenta records con primary_cluster.single_pixel_mode True en data/mirova_equivalent (solo lectura)."""
import glob, json, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
tot = conpc = sp = 0; keys = Counter()
for f in glob.glob("data/mirova_equivalent/*.json"):
    for r in json.load(open(f, encoding="utf-8")).get("records", []):
        tot += 1; pc = r.get("primary_cluster")
        if not pc: continue
        conpc += 1
        for k in pc:
            if "single" in k: keys[k] += 1
        if pc.get("single_pixel_mode") is True: sp += 1
print("records", tot, "con primary_cluster", conpc, "single_pixel_mode True", sp, "claves:", dict(keys))
