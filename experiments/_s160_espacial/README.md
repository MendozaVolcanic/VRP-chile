# Auditoría espacial S160: Tupungatito, Puyehue-Cordón Caulle e Isluga (2026-10-22)

Pedida por Nicolás: ¿la anomalía que alerta MIROVA está en el centro de su imagen, y la vemos y publicamos igual?

- Auditor (Fable 5.1): `INFORME.md`, `hallazgos.csv`, scripts `01_` a `05_` con sus salidas y mapas `mapa_*.png`.
- Verificador con contexto limpio (Opus 5.5): `verificador/INFORME.md` (re-corrió todo byte a byte). **Leer primero
  el verificador**: confirma lo central y corrige varios números del auditor (pareo de 02b, anillo real 21 × 19
  asimétrico, MODIS 26 y no 28, contrafactual 2 y no 3, la fuente del E de Cordón Caulle no es persistente).
- Mapa para Nicolás: `../_s160_espacial_mapa/` (dónde publicamos en noches limpias y focos recurrentes).
- **No commiteado** (copias de otras fuentes, reproducibles): `data/` (44 MB, JSON de producción sacados de
  `origin/main` `db0dfe847` con `git show`) y `_censo_s159/` (14 MB, artefactos del censo del oráculo, rama
  `s159-oraculo-censo`).

En una pantalla, ya con el verificador:
1. En Tupungatito y Cordón Caulle el cráter está a 4,79 km al NW y 7,61 km al N del centro del TIF de MIROVA; el calor
   que MIROVA alerta cae casi siempre en el cráter, y nuestro cúmulo en el mismo lugar (0,21 a 0,49 km en la misma
   pasada; 0,47 a 0,59 km con otra pasada de la misma noche, control A109). Isluga: 0,8 a 1,0 km al SW de la
   coordenada del yaml, según tres instrumentos.
2. Por geometría no perdemos alertas en el efecto (lo que no publicamos es sobre todo el cráter en 0,0 MW, D25), salvo
   la SOSPECHA VE-01: protegida de Tupungatito del 2026-09-29 04:54 (Suomi NPP, 1,86 MW) con nuestro único píxel a
   9,42 km ENE del cráter, fuera del inner de 7 km.
3. La caja de cumbre del código de MIROVA centrada en el TIF no reproduce sus alertas en esos dos volcanes (0 de 10 y
   0 de 48); es un hecho del port, no prueba qué usa MIROVA en producción.
4. Cordón Caulle con inner 20 km publica cúmulos en noches limpias hasta 20 km del cráter, muchos fuera del anillo de
   MIROVA (VIIRS 375 30 de 38 a más de 2 km; VIIRS 750 13 de 30; MODIS 26 de 38).
