import json, sys
def diff(a,b,p=""):
    out=[]
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b: out.append((p+"/"+k, "falta en "+("a" if k not in a else "b")))
            else: out+=diff(a[k],b[k],p+"/"+k)
    elif a!=b: out.append((p, str(a)[:80]+" | "+str(b)[:80]))
    return out
a=json.load(open(sys.argv[1],encoding="utf-8")); b=json.load(open(sys.argv[2],encoding="utf-8"))
d=diff(a,b); print(len(d))
for x in d[:40]: print(x)
