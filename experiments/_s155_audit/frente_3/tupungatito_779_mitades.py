"""F3: el 0,647 de #779 (corpus del 2026-10-14, todo C0) partido en dos mitades de la ventana y por magnitud
de la alerta de MIROVA. Usa reproducir_779.ratio (control: reproduce 0,647/23). P1: si fuera sólo la salida de
una noche, las dos mitades darían medianas parecidas. P2: n por mitad impreso."""
import sys, statistics
sys.stdout.reconfigure(encoding="utf-8")
import reproducir_779 as r7  # imprime su propia reproducción primero
n, med, rs = r7.ratio("f3b414213", ("2026-08-15", "2026-10-14"), True)
print("control", n, med)
for nom, f in (("08-15..09-12", lambda d: d <= "2026-09-12"), ("09-13..10-14", lambda d: d >= "2026-09-13")):
    xs = [x for (b, d), x in rs if f(d)]
    print(nom, "n", len(xs), "mediana", round(statistics.median(xs), 3))
