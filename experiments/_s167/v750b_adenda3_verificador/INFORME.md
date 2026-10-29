# Verificador corto: adenda 3 de V750-B (regla N-3)

Fecha 2026-10-29. Sólo lectura sobre el repo; todo lo ejecutado vive en D:\vrp-trabajo\temporales\s167_ver_v750b_ad3\
(árbol extraído con `git -c core.autocrlf=false archive 5b924379d`; TMP, TEMP y TMPDIR en `tmp\`; C: 27 GB y D: 6,2 GB
libres, sobre el piso de 3 GB; 1 proceso a la vez).

## Veredicto: SELLABLE CON CAMBIOS MENORES (VA3-01 es condición del sello)

La regla N-3 está bien hecha y hace sólo lo que dice. Lo que falta es que el procedimiento de lectura que fija el §3 de
la adenda se salta la compuerta de cobertura con las cajas de la adenda 1 (VA3-01, gravedad 3). El arreglo es chico.

## Caminos previos (escritos antes de correr nada)

1. Toca algo sellado: el diff entre el tag y la punta incluye más que `adenda3/`.
2. Un reemplazo cambia más que la regla (el texto "viejo" calza en otro sitio, o el "nuevo" altera una línea ajena).
3. La regla difiere de V375-E §8.13 (sensor, hito, `<` contra `<=`, alerta de la tabla, protegida).
4. La batería pasa por la razón equivocada (rojo que falla sólo por texto, no por comportamiento).
5. Los dos equivalentes declarados no lo son.
6. N5 (la N-3 cambia la ROI de B2 a B4) revela un efecto no buscado.
7. El lector reemplaza un paso sellado de la lectura (la adenda 1 pone un lector con compañero de cobertura).
8. La N-3 abre la compuerta de cobertura o de control K (una protegida SIN DATO debería seguir frenando).
9. Las banderas de línea de comandos (`--salida`) se comportan distinto del analizador sellado.
10. La salida cambia en escenas sin N-3 (identidad).

## Hallazgos

**VA3-01, gravedad 3.** El §3 de la adenda 3 manda que el veredicto sea el de `leer_n3_v750b.py` "con los mismos
argumentos con que se correría `analizar_v750b.py`". Pero la lectura sellada es `adenda1/leer_v750b.py` (adenda 2 §8,
l. 139), que corre antes `cobertura_cajas_v750b.py` y no deja pasar al analizador si cierra (VAD-01; su docstring explica
que el analizador solo da veredicto sin marca cuando a una protegida le falta una caja). `leer_n3_v750b.py` llama al
analizador directo (l. 117 a 124) y no corre el compañero. Prueba: en la escena N1 (carpeta `vexp\`) le quité la caja B5
a la protegida de Láscar. `leer_n3_v750b.py`: "== cobertura: SUFICIENTE", compuerta ABIERTA, "ROI elegida: B4 ...".
`adenda1/leer_v750b.py` con los mismos argumentos: "cobertura con las cajas: INSUFICIENTE", salida 3, no se lee. Hay que
hacer que el lector de la adenda 3 corra el compañero con la misma lógica de `leer_v750b.py` (salidas 2 y 3, e
`--leer-con-faltantes`, que en `leer_v750b.py` marca y sale 5), o decir en el §3 que se corre el compañero primero y que
no se acepta un veredicto si sale 3, y agregar un escenario N9 que lo ejerza. La adenda dice "cobertura sin cambio": hoy
no se cumple en esta ruta.

**VA3-02, gravedad 1.** `leer_n3_v750b.py` l. 113 decide con `"--salida" not in argv`. Con `--salida=ruta` (o una
abreviación de argparse) agrega su `--salida` por defecto al final y gana el último: la salida cae en `adenda3\` y no
en `ruta`, sin aviso (probado: `vx_salida.txt` no se creó). El veredicto sigue saliendo por stdout.

**VA3-03, gravedad 1.** El "rojo 9 de 9" sobrestima: N0 y N6 fallan contra el sellado sólo porque falta el texto
"[con la adenda 3...]" y "P1 ... (que veta; ...)", no por comportamiento. Los rojos de comportamiento son N1 (B2 no
elegible), N5 (B4 no elegible) y las cifras de N7. Además hay una mutación no atrapada y no declarada:
`metricas(b,"O","tabla")["P1_todas"]` por `["P1"]` en `elig_todas` (l. 75) pasa 9 de 9 (corrida mía,
`run_mx\`). Es equivalente: en el canal "tabla" una etiqueta "prot" exige alerta de la tabla y entonces la pasada no es
N-3. Conviene declararla junto a las otras dos.

**VA3-04, gravedad 1.** `probar_adenda3.py` (N8) escribe `_ajeno_analizar_v750b.py` dentro de la carpeta sellada
`experiments/_s162_v750b/` y la borra en `finally`. Inocuo, pero toca la carpeta sellada durante la prueba.

**VA3-05, gravedad 1 (informativo).** N5 no es un efecto no buscado: es la regla actuando (B0 pierde una N-3 en Láscar,
B4 allí es la caja B0, y con la adenda queda B4 donde el sellado daría B2). Lo que implica: una ROI elegida por la N-3
puede perder una protegida que sí era real. El texto ya lo dice ("se ve, pero no decide"); al despachar, mirar la lista
aparte y la ROI del analizador sellado corrido al lado antes de que Nicolás confirme el §6.5.

## Comprobado

- Diff `s162-v750b-adenda2-sellada` a `5b924379d` y a la punta `d4a735ad2`: en `experiments/_s162_v750b/` sólo se agregan
  los 7 archivos de `adenda3/`; `d4a735ad2` sólo toca `tasks/LOOP_VIIRS750.md`. `pipeline/`, `data/`, `frontend/`,
  `scripts/`, `tests/`, `.github/`, `docs/` y `volcanoes.yaml`: diff vacío. (La rama trae además cambios de
  `experiments/_s162_v750a/`, ajenos a esta adenda.)
- sha256 LF de `analizar_v750b.py` idéntico (`83b7159bd066...`) en `s162-v750b-sellado`, `s162-v750b-adenda2-sellada` y
  `5b924379d`.
- Batería: 9 de 9 (`run1\`, 23 s). Rojo contra el sellado: 9 de 9 con falla por aserción (`run_rojo\`). Nulo: 12 de 12
  atrapadas, identidad PASA, control CAÍDA (`mut.log`), igual a lo que dice la adenda.
- Identidad por diferencia de salidas (sellado contra lector, normalizando sólo las marcas añadidas): 0 líneas distintas
  en N0, N2, N3, N4, N6; en N1, N5 y N7 sólo cambian las líneas de P1 de los brazos afectados y los elegibles/ROI, como
  predice la adenda. Las demás secciones son idénticas.
- Predicado: mismo que V375-E §8.13 (`leer_posicion_v375e.py` l. 308 a 312): protegida, sin alerta de la tabla, Suomi
  NPP, `hora[:10] < "2026-10-09"`. Los nombres de sensor del lector (`VIIRS_SNPP_750`) existen en los datos reales
  (`data/mirova_equivalent/*.json`) y `hora_utc` es "AAAA-MM-DD HH:MM".
- Cobertura: una N-3 con resultado en error (SIN DATO) sigue frenando (cobertura INSUFICIENTE, compuerta CERRADA, salida
  3; `vs1\`). Controles, E, P2, §6.2 y §6.3 sin cambio (sólo cambia `m["P1"]`, que se lee en `ver` y en `elegibles`).
- Los dos equivalentes declarados son equivalentes: "protegida" siempre es verdadera donde se consulta, y listar con
  "decide" o con "todo" coincide porque `noche` es la fecha de la pasada y sin alerta de la tabla sólo hay etiqueta con
  `noche >= 2026-06-13`.
- Sin guiones largos ni medios en los cuatro archivos nuevos (grep).

## No comprobado

- Ninguna lectura sobre datos reales (no hay lista del 2026-11-03); sólo escenas sintéticas.
- La ruta de relanzamiento (`--leer-con-faltantes`, salida 5) del lector de la adenda 3.
- Que `alerta_tabla` de la lista real esté bien calculado (límite declarado en el §5 de la adenda).
- La ejecución con una copia del repo con CRLF (el sha se normaliza a LF; el árbol de prueba es LF).
