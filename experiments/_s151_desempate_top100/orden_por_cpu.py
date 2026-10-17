"""Mismo arreglo con empates exactos, mismo numpy: el orden de argsort por defecto depende de la
ruta SIMD que numpy elige al arrancar. Se corre dos veces, con y sin X86_V3 (AVX2) habilitado."""
import hashlib
import numpy as np

rng = np.random.default_rng(0)
# 418 pixeles con VRP cuantizados (como MODIS: BT discreta, area uniforme, fondo escalar)
v = rng.choice([0.3931, 0.5242, 0.5949, 0.9173, 2.0313], size=418).astype(np.float64)
feat = np.show_runtime  # noqa
d = np.argsort(-v)
s = np.argsort(-v, kind="stable")
lx = np.lexsort((np.arange(v.size), -v))
print("default top5", d[:5].tolist(), "top100 md5", hashlib.md5(d[:100].tobytes()).hexdigest()[:10])
print("stable  top5", s[:5].tolist(), "top100 md5", hashlib.md5(s[:100].tobytes()).hexdigest()[:10])
print("lexsort == stable", bool((lx == s).all()))
