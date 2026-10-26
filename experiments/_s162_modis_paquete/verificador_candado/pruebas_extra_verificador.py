# -*- coding: utf-8 -*-
"""Verificador del candado MOD-D: pruebas que la batería probar_evaluar_paquete.py NO trae, para reglas selladas o de
la adenda 3 que quedaron sin ejercitar. Reutiliza los armadores de pasadas sintéticas de la batería (fila, base,
correr) y su protocolo: cada prueba tiene que pasar contra evaluar_paquete.py y fallar POR ASERCIÓN contra la mutación
que rompe esa regla (ver mutaciones_propias.py --bateria <este archivo>).

  x01_bloque_noche          §4 P2: dos pasadas discordantes de la misma noche-volcán son UN bloque (B no sube)
  x02_chillan_6_de_7        §5.3: 6 de 7 pares a favor da p = 0,0625 y NO alcanza (SIN RESOLVER)
  x03_p1_k_calla            §4 P1: una protegida que K tampoco publica no veta
  x04_bajo1_sin_publicar    §4 P2: una alerta bajo 1 MW que K publica y PM no es +1 para PM
  x05_grilla_incompleta     adenda 3.6: «grilla_incompleta» sale del denominador y se cuenta por motivo
  x06_chillan_regla4_bajo   §5.4: con los pares de cenit <= 30 fuera de [0,8; 1,25] NO es ES DEL SENSOR
  x07_chillan_empate        §5.5: un par con las dos distancias iguales sale de la prueba y se lista
  x08_chillan_grupo_vacio   §5.5 (VCD-16): con el grupo de cenit > 30 vacío la regla 4 no se cumple
  x09_soporte_mismo_modis   adenda 1 / A109: el mismo satélite MODIS no es soporte independiente
Uso: python -I pruebas_extra_verificador.py [--modulo evaluar_paquete.py] [--json salida]
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CANDADO = AQUI.parent
sys.path.insert(0, str(CANDADO))
import probar_evaluar_paquete as T  # noqa: E402  (fila, base, correr, exige, g, dia, Falla)

fila, base, correr, exige, g, dia = T.fila, T.base, T.correr, T.exige, T.g, T.dia


def x01_bloque_noche(E):
    # 6 noches Llaima donde sólo K publica (base) + en UNA de esas noches una segunda pasada igual: B sigue en 6
    fs = base() + [fila("Llaima", dia(100).replace("01:05", "03:05"), "neg_limpio", k=0.2)]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p2", "B") == 6 and g(r, "brazos", "PM", "p2", "neto") == -7,
          "bloque: B %s neto %s (esperado B 6, neto -7)" % (g(r, "brazos", "PM", "p2", "B"), g(r, "brazos", "PM", "p2", "neto")))


def x02_chillan_6_de_7(E):
    al = [fila("NevadosDeChillan", dia(500 + i), "protegida", k=0.6, pm=1.0, mirova=1.0, z=20.0) for i in range(6)]
    al.append(fila("NevadosDeChillan", dia(506), "protegida", k=1.0, pm=0.6, mirova=1.0, z=20.0))   # K más cerca
    r = correr(E, base() + al)
    c = g(r, "chillan", defecto={})
    exige(c.get("n_pares") == 7 and c.get("b_mas_cerca") == 6, "Chillan: pares %s a favor %s" % (c.get("n_pares"), c.get("b_mas_cerca")))
    exige(c.get("estado") == "SIN RESOLVER", "Chillan 6 de 7 (p = 8/128 = 0,0625): %s, esperado SIN RESOLVER" % c.get("estado"))


def x03_p1_k_calla(E):
    fs = base() + [fila("Lascar", dia(300), "protegida", k=None, pm=None, mirova=3.0)]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p1", "estado") == "SIN PERDIDA" and r["veredicto"] == "CANDIDATO",
          "P1 con K callado: %s %s" % (g(r, "brazos", "PM", "p1", "estado"), r["veredicto"]))


def x04_bajo1_sin_publicar(E):
    fs = base() + [fila("Lascar", dia(220 + i), "bajo1", k=0.5, pm=None, mirova=0.5) for i in range(2)]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p2", "neto") == -4 and g(r, "brazos", "PM", "p2", "s_b") == 2
          and g(r, "brazos", "PM", "p2", "B") == 8,
          "bajo1 sin publicar: neto %s s_b %s B %s (esperado -4, 2, 8)" % (
              g(r, "brazos", "PM", "p2", "neto"), g(r, "brazos", "PM", "p2", "s_b"), g(r, "brazos", "PM", "p2", "B")))


def x05_grilla_incompleta(E):
    fs = base() + [fila("Lascar", dia(320), "protegida", k=3.0, pm=None, mirova=3.0, port_grilla="grilla_incompleta")]
    r = correr(E, fs)
    exige(r["veredicto"] == "CANDIDATO" and g(r, "controles", "cobertura", "fuera_del_denominador", "escena_invalida") == 1
          and len(g(r, "controles", "cobertura", "protegidas_fuera_del_denominador", defecto=[])) == 1,
          "grilla incompleta: %s %s" % (r["veredicto"], g(r, "controles", "cobertura", "fuera_del_denominador")))


def x06_chillan_regla4_bajo(E):
    al = ([fila("NevadosDeChillan", dia(600 + i), "protegida", k=0.6, pm=1.6, mirova=1.0, z=20.0) for i in range(4)]
          + [fila("NevadosDeChillan", dia(610 + i), "protegida", k=0.5, pm=0.3, mirova=1.0, z=45.0) for i in range(3)])
    r = correr(E, base() + al)
    exige(g(r, "chillan", "estado") == "SIN RESOLVER",
          "regla 4 con mediana bajo 30 en 1,6: %s, esperado SIN RESOLVER" % g(r, "chillan", "estado"))


def x07_chillan_empate(E):
    al = [fila("NevadosDeChillan", dia(500 + i), "protegida", k=0.6, pm=1.0, mirova=1.0, z=20.0) for i in range(5)]
    al.append(fila("NevadosDeChillan", dia(506), "protegida", k=0.5, pm=0.5, mirova=1.0, z=20.0))   # empate exacto
    r = correr(E, base() + al)
    c = g(r, "chillan", defecto={})
    exige(c.get("n_pares") == 5 and len(c.get("empates", [])) == 1 and c.get("estado") == "RESUELTO POR EL PAQUETE",
          "empate exacto: pares %s empates %s estado %s" % (c.get("n_pares"), len(c.get("empates", [])), c.get("estado")))


def x08_chillan_grupo_vacio(E):
    # 5 pares todos bajo 30 grados, PM en 1,0 pero sólo 3 de 5 a favor: ni regla 3 (p = 0,5) ni regla 4 (grupo > 30 vacío)
    al = ([fila("NevadosDeChillan", dia(600 + i), "protegida", k=0.6, pm=1.0, mirova=1.0, z=20.0) for i in range(3)]
          + [fila("NevadosDeChillan", dia(610 + i), "protegida", k=1.0, pm=0.6, mirova=1.0, z=20.0) for i in range(2)])
    r = correr(E, base() + al)
    exige(g(r, "chillan", "estado") == "SIN RESOLVER" and g(r, "chillan", "mediana_z_gt30") is None,
          "grupo > 30 vacio: %s" % g(r, "chillan", "estado"))


def x09_soporte_mismo_modis(E):
    fs = base() + [fila("Copahue", "2026-05-01 03:05", "neg_limpio", pm=0.2)]
    t = datetime(2026, 5, 1, 3, 5, tzinfo=timezone.utc)
    nuestros = [{"vol": "Copahue", "b": "MODIS", "sensor": "MODIS_AQUA", "dt": t, "noche": "2026-05-01",
                 "dc": "summit", "pub": 1, "disp": 0.3}]
    r = correr(E, fs, nuestros=nuestros)
    s = g(r, "brazos", "PM", "soporte_adenda1", defecto={})
    exige(s.get("n") == 1 and len(s.get("candidatas", [])) == 0, "el mismo MODIS conto como soporte: %s" % s)


PRUEBAS = [v for k, v in sorted(globals().items()) if k.startswith("x") and k[1:3].isdigit()]
T.PRUEBAS = PRUEBAS

if __name__ == "__main__":
    sys.exit(T.main())
