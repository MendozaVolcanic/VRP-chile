# Geometria de la perdida: pixel de K, crater, centro de grilla de MIROVA. Solo lectura.
import math
def hav(a, b, c, d):
    R = 6371.0; p1, p2 = math.radians(a), math.radians(c); dp = p2 - p1; dl = math.radians(d - b)
    return 2*R*math.asin(math.sqrt(math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
def ne(a, b, c, d):
    return (c - a) * 111.32, (d - b) * 111.32 * math.cos(math.radians((a + c) / 2))
vent = (-23.36293, -67.731416); nom = (-23.369, -67.732); grid = (-23.37041, -67.73102); px = (-23.36081, -67.70013)
print("pixel-vent  %.3f km  (dN,dE)=(%.3f, %.3f)" % ((hav(*vent, *px),) + ne(*vent, *px)))
print("pixel-nom   %.3f km" % hav(*nom, *px))
print("pixel-grid  %.3f km  (dN,dE)=(%.3f, %.3f)" % ((hav(*grid, *px),) + ne(*grid, *px)))
print("grid-vent   %.3f km  (dN,dE)=(%.3f, %.3f)" % ((hav(*vent, *grid),) + ne(*vent, *grid)))
g = hav(*vent, *grid)
print("MIROVA a 1,41 km del centro de grilla: entre %.2f y %.2f km del crater" % (abs(1.41 - g), 1.41 + g))
print("cota inferior pixel K a la alerta de MIROVA: %.2f km" % (hav(*grid, *px) - 1.41))
# Puede la alerta de MIROVA (radio 1,41 desde grilla) caer fuera de la caja de 2,5 km centrada en el crater?
mx = 0
for k in range(3600):
    t = math.radians(k / 10); dn = g * 0 + 1.41 * math.cos(t); de = 1.41 * math.sin(t)
    gn, ge = ne(*vent, *grid); n, e = gn + dn, ge + de
    mx = max(mx, max(abs(n), abs(e)))
print("max |dN| o |dE| de la alerta de MIROVA respecto del crater: %.2f km (caja: 2,5)" % mx)
