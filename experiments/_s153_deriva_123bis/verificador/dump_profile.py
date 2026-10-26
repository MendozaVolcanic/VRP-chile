import sys, os, json
sys.path.insert(0, '.')
import pipeline.profile as p
out = {}
for k in dir(p):
    if k.isupper():
        v = getattr(p, k)
        try:
            json.dumps(v); out[k] = v
        except Exception:
            out[k] = repr(v)
json.dump(out, open(sys.argv[1], 'w'), sort_keys=True, default=str)
