import os, sys, pickle, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b7 import *  # noqa
t0=time.time()
H = herm()
print("== estrato hermano: %d pasadas ==" % len(H), flush=True)
D = corre(H, "cruzada", "cruzada")
pickle.dump(D, open("h_cruz.pkl","wb"))
print("estados:", D.estado.value_counts().to_dict(), " %.0fs"%(time.time()-t0))
