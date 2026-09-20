# Conteos de S0-bis CON el filtro de usabilidad (como el resto del documento). Solo conteo.
import os, sys, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.abspath(HERE + "/../v3"), os.path.abspath(HERE + "/../v4"), HERE):
    sys.path.insert(0, p)
from common3 import *  # noqa
from c6 import df, cruzada_v6, raster  # noqa

for nom, sub in (("patron sin pub (2.999)", df[df.patron]),
                 ("patron con pub (2.627)", df[df.patron & df.pub])):
    print("\n-- %s, con filtro de usabilidad y pasada cruzada nocturna --" % nom, flush=True)
    for etq, kw in (((">=15 min, sin tope"), dict(gmin=900, gmax=10 ** 9)),
                    ((">=45 min, sin tope"), dict(gmin=2700, gmax=10 ** 9)),
                    (("ventana v6 [45,120]"), dict(gmin=2700, gmax=7200))):
        n = 0
        for vol, g in sub.groupby("vol"):
            for _, r in g.iterrows():
                cr, why = cruzada_v6(vol, r["t"], **kw)
                n += cr is not None
            raster.cache_clear()
        print("   %-24s %4d" % (etq, n), flush=True)
print("\n  la v6 dice: 1.824 con >=15 min y 1.594 con >=45 min (denominador 2.541)")
