"""S190: recalcula la línea de pipeline/grillas_mirova.yaml de los volcanes cuyo centro cambió (auditar_centros.py).

Usa la MISMA regla que generó la grilla de los 34 (experiments/_s172_sombra34/generar_grillas_34.py, función entrada:
(X0, Y0) = UTM del lat/lon de volcanoes.yaml en la zona estándar por longitud, redondeado a 0,1 m; centro_lat/lon =
el lat/lon del yaml a 5 decimales). Reemplaza sólo la línea de cada volcán y conserva su roi_v750; no toca nada más.

Uso: python experiments/_s190_coordenadas/regenerar_grillas.py Callaqui Mentolat ...
"""
import io
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "experiments" / "_s172_sombra34"))
from generar_grillas_34 import entrada, linea  # noqa: E402


def main(nombres):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    volc = {v["name"]: v for v in yaml.safe_load((REPO / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    ruta = REPO / "pipeline" / "grillas_mirova.yaml"
    texto = ruta.read_text(encoding="utf-8")
    grillas = yaml.safe_load(texto)["volcanes"]
    lineas = texto.split("\n")
    for n in nombres:
        e = entrada(volc[n])
        e["roi_v750"] = grillas[n]["roi_v750"]
        idx = [i for i, l in enumerate(lineas) if l.startswith(f"  {n}:")]
        assert len(idx) == 1, n
        print(f"{n}: antes {lineas[idx[0]].strip()}\n{' ' * len(n)}  ahora {linea(n, e).strip()}")
        lineas[idx[0]] = linea(n, e)
    ruta.write_text("\n".join(lineas), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
