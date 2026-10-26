# Verificador limpio del censo MOD-D (2026-10-26)

Modelo Fable, esfuerzo alto, contexto limpio. Escribió `CAMINOS.md` antes de medir (16:00:28 GMT del servidor) y después
`INFORME.md`. Copia fiel de `D:\vrp-trabajo\temporales\s162_modd\verificador_censo\`; no tocó el repositorio.

**Veredicto del verificador: «El veredicto DECIDE NICOLÁS se sostiene.»** Recalculó P1, P1b, P2 y M con código propio
(`verificar.py`) y re-corrió el evaluador completo (`rerun/r.json`, igual al entregado). Los 12 controles quedaron en verde.

## Lo que viaja con el veredicto (sin cambiar el resultado)

1. La única protegida que baja de 1 MW (Láscar 2026-04-25 07:35) lo hace por 0,027 MW, y eso depende del desempate del
   relleno del fondo. Con la regla de `fillmissing2` de MATLAB da 1,1124 MW (`p1b_regla.py`), y bajo esa regla ninguna de
   las 48 protegidas queda bajo 1 MW con K sobre 1: la fila sería la 6, CANDIDATO. La regla sellada manda el VRP del port,
   y sigue SIN DATO que MIROVA use ese `.m` para MODIS.
2. En la dirección contraria, 20 protegidas pasan de K < 1 MW a PM ≥ 1 MW.
3. El SIN RESOLVER de Chillán (6 de 7, p = 8/128) es un límite de la regla con 7 pares, no evidencia de que el déficit sea
   del sensor: sobre 30° el PM da 1,12.

## Correcciones aplicadas por sus hallazgos

- **PREREGISTRO.md de la rama** (sin las adendas 3 y 4, 112 líneas menos que el del tag): reemplazado por el del tag
  `s162-modd-tag`, que es el que gobernó el censo. `git diff s162-modd-tag -- PREREGISTRO.md` queda vacío.
- **«149 pasadas del lote en la población»** (adenda 3.11, texto sellado, no se edita): son **150**. Una tiene «volcán
  fuera del gránulo» en los dos lados. Los 148 evaluables y los 91 con píxeles sí coinciden. Sin efecto en el control.
- **Run de S159 (39712862945) con conclusión «failure»** (job MODIS 3 de 6): su archivo trae 25 records como los otros, y
  el censo los reproduce a 1e-6 con píxeles idénticos. El dato es consistente; la causa del fallo no se miró (SOSPECHA).
- **5 pasadas crepusculares** (dayflag 1, cenit solar 89 a 90°) dentro del censo «nocturno»: sin efecto en ninguna regla.
- **«Con y sin D33» del §3 no se informó**: medido por el verificador, efecto nulo (las 10 son negativos con K 0 y PM 0).
