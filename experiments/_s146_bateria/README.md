# Batería del Apéndice A completa: todos los brazos, todos los cúmulos, nulo por píxel (S146)

## Por qué existe

La batería de los nueve casos del Apéndice A de Coppola 2016a es la única vara que dice qué variante
del algoritmo es fiel al paper, y de ella cuelgan varios cierres del proyecto. Quedó incompleta por
tres lados: tres brazos INDECIDIBLES en A2 porque sus salidas no guardaron la posición del cúmulo;
un brazo que nadie corrió (banda 22 con fondo local y CON la compuerta de temperatura); y dos nulos
espaciales vacíos por construcción, porque la batería guardaba un solo cúmulo por pasada, el que el
pipeline elige anclado al cráter. Lo que un brazo alertó a 10 km de la cumbre nunca quedó escrito,
así que "la caja rotada salió vacía" no probaba nada.

Esta carpeta re-corre la batería guardando lo que antes se descartaba, y trae el evaluador con el
nulo que sí tiene poder: por píxel alertado.

## Qué corre

Workflow: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.github\workflows\probe-s146-bateria-apendice.yml`
(sólo `workflow_dispatch`; hay que mergearlo a `main` antes de poder despacharlo).

| job | qué hace |
|---|---|
| `preparar` | falla si faltan credenciales; arma la lista de brazos; comprueba el sha256 de los dos criterios; corre `prueba_local.py` en Linux (el instrumento probado antes de gastar descargas) |
| `brazos` | matriz, un job por brazo, tres en paralelo. `correr_bateria.py` procesa los 9 casos con ese brazo |
| `evaluar` | junta las salidas, cuenta cobertura (`verificar_cobertura.py`), corre `evaluar_bateria.py`, guarda todo en una rama propia y pone el run en rojo si algo no se midió |

Brazos (tabla única en `brazos.py`): los 8 de S136 y S137, más `out_apendice_b22_fondolocal`
(B22 + fondo local, con compuerta, conectiva `min`), que es el que
`docs/audit_s145/D21_D22_ESTADO_DEL_BLOQUEO.md` sección 5 señala como nunca corrido. Hay un décimo
definido y apagado por defecto, `out_apendice_b22_fondolocal_prosa` (lo mismo con `max`): el brazo
que da 9 de 9 usa `max`, así que atribuir ESE resultado a la compuerta o al fondo pide el par con
`max`. Correrlo o no es decisión de quien despacha.

El pipeline de producción no se toca: los brazos se arman reasignando flags y funciones en el
namespace de `pipeline.process_modis` (patrón A75, el mismo mecanismo de S136 y S137, cuyo predicado
y cuyo parche de compuerta se IMPORTAN de `experiments/_s136/conformidad_apendice.py`, no se
copian). La captura (`captura.py`) envuelve `combine_hot_paths`, `first_pass_tests_2_and_3`,
`second_pass_adjacent` y `cluster_hotspots` y devuelve exactamente lo que devuelve la original.

## Comando de despacho

Los 9 brazos, los 9 casos:

```
gh workflow run probe-s146-bateria-apendice.yml --ref main
```

Variantes:

```
gh workflow run probe-s146-bateria-apendice.yml --ref main -f brazos=todos
gh workflow run probe-s146-bateria-apendice.yml --ref main -f brazos=out_apendice_b22_fondolocal,out_apendice_b22_prosa
gh workflow run probe-s146-bateria-apendice.yml --ref main -f caso=A2
```

El brazo de control (`out_apendice`, producción) corre SIEMPRE aunque no se lo nombre, porque la
cobertura de cada brazo se compara contra él. Con `-f caso=A2` los totales de 9 no aplican y el
control de identidad cubre sólo ese caso.

Seguir el run: `gh run watch` o `gh run list --workflow probe-s146-bateria-apendice.yml --limit 3`.

## Duración estimada, y en qué se basa

Unos **30 a 35 minutos** de reloj para los 9 brazos.

- Base medida: los 8 runs de `probe-s136-conformidad-apendice.yml` (un brazo, 9 casos, 24 pasadas)
  tardaron entre 3 min 50 s y 6 min cada uno (`gh run list` en esta sesión: por ejemplo creado
  08:32:45, terminado 08:37:13 del 2026-09-13). La captura agrega copias de máscaras, despreciable.
- 9 brazos de a 3 en paralelo son 3 tandas de 6 a 9 min (con instalación de HDF4), más `preparar`
  (unos 3 min; `prueba_local.py` tardó 31 s en local) y `evaluar` (unos 2 min).
- `timeout-minutes`: 45 por brazo (1,3 × 9 min = 12; el margen extra es por la lentitud de NASA,
  A64), 15 en `preparar` y 15 en `evaluar`.
- SOSPECHA, no medido: que tres sesiones Earthdata simultáneas no tengan costo. El cron NRT corre
  hasta 8 en paralelo con las mismas credenciales, por eso elegí 3.

## Qué salidas produce y dónde quedan

Por brazo, en `experiments/_s146_bateria/out/<brazo>/`:

- `resultado_apendice.json`: mismo esquema de S136 (así el predicado sellado lo lee sin cambios) más,
  por pasada, `cumulos` (TODOS: origen de la llamada, orden, si es el primario publicado, n de
  píxeles, lat, lon, distancia a la cumbre, MW crudos y MW publicados), `pixeles_alertados` (lat,
  lon, fila, columna, MW del píxel, distancia a la cumbre y `caminos`), `llamada_publicada`,
  `final_hotspot_source`, `pc_d9_capped`; y por caso `intentos`, una fila por gránulo nocturno con
  su desenlace.
- `meta.json`: flags EFECTIVOS leídos del procesador, commit, run, pasadas por caso, gránulos sin
  medir, discrepancias de captura.
- `report.txt`: la salida cruda del probe.

En `experiments/_s146_bateria/evaluacion/`: `cobertura.txt`, `evaluacion.txt`,
`resultado_bateria_s146.json` y `ESTADO_DEL_RUN.txt`.

Dónde quedan, dos copias:

1. Artefactos del run (`bateria-s146-brazo-<brazo>`, `bateria-s146-completa`,
   `bateria-s146-prueba-local`), 90 días.
2. **Un commit en una rama nueva por corrida, `s146-bateria-salidas-<run_id>`**, que no caduca.
   Bajarla: `git fetch origin s146-bateria-salidas-<run_id>` y
   `git checkout origin/s146-bateria-salidas-<run_id> -- experiments/_s146_bateria/out experiments/_s146_bateria/evaluacion`.

Por qué una rama y no `main`: `main` lo escribe el cron NRT cada dos horas bajo el candado
`push-main`, y GitHub guarda un solo run pendiente por grupo (el segundo que llega desplaza al que
esperaba, así se perdió el job `merge` en S125 y S126). Un empuje más a `main` o compite por ese
candado o reabre la carrera de rebase que cerró el PR #502. Una rama nueva por corrida no compite
con nadie, nunca choca (es nueva), no dispara `pages-deploy` ni `tests`, y pasa a `main` por un PR
normal cuando alguien haya leído `ESTADO_DEL_RUN.txt`. El bucle de reintento del empuje es por
cortes de red; no usa el grupo `push-main` (o grupo o reintento, nunca los dos).

## Cuándo el run sale rojo, a propósito

- faltan `EARTHDATA_USERNAME` o `EARTHDATA_PASSWORD` (un secreto ausente llega como string vacío);
- el sha256 de alguno de los dos criterios no coincide con el sellado;
- `prueba_local.py` falla en Linux;
- un brazo termina con algún caso en cero gránulos (salida 3), con algún gránulo sin medir
  (salida 4) o con la captura sin cuadrar contra el record (salida 5);
- algún brazo tiene menos pasadas que el control, o menos que la línea base commiteada de S136
  (24 pasadas: A1 4, A2 4, A3 2, A4 2, A5 2, A6 2, A7 3, A8 2, A9 3). La segunda vara atrapa el
  corte de NASA que les pega a todos por igual, control incluido (A108);
- el evaluador detecta captura muerta (R4, Cpx-a, Cpx-b).

Aun en rojo, las salidas que existan se guardan en la rama y en el artefacto.

## Cómo se lee el veredicto

Abrir `evaluacion/evaluacion.txt` de arriba hacia abajo:

1. **Las dos líneas de hash**: deben decir COINCIDE. Si no, el pre-registro quedó invalidado.
2. **Cpx-d IDENTIDAD**: con la vara vieja, las salidas nuevas deben reproducir los 72 veredictos
   commiteados. Si dice DERIVA, el pipeline o los gránulos cambiaron desde el 13-09-2026 y la
   comparación con los informes de S136, S137 y S146 deja de ser directa: leer qué celdas cambiaron
   antes de seguir.
3. **Cpx-a**: 0 pasadas con problemas, o los nulos no valen.
4. **TABLA BRAZO x CASO**: el veredicto sellado, por cúmulo primario. Acá se resuelven los tres
   INDECIDIBLES de A2, porque ahora todos los brazos guardan posición.
5. **DETALLE A2**: todos los cúmulos de cada pasada, con su separación a la fisura. El asterisco
   marca el primario publicado.
6. **NULO POR PÍXEL**: por brazo y caso, `n_con_magnitud(n_alertados)` en cada caja. `fis[FISURA]`
   es la caja del acierto de A2 y sirve de contraste; `[excl]` es A1 al norte (Klyuchevskoy), que
   no entra a la tasa.
7. **VEREDICTO POR BRAZO**, dos líneas por brazo:
   - `A2 sellado` es el del criterio de A2; `A2 final` le suma R1 (si alguna caja rotada tiene
     píxeles con magnitud, el acierto pasa a INDECIDIBLE).
   - `nulas ocupadas k/34`: 0 es "no regala", 1 a 3 "regalo marginal", 4 o más "REGALA ACIERTOS"
     y entonces un 9 de 9 se informa SIN VALOR DISCRIMINANTE.
   - `con N reserva(s)`: en ese negativo el cúmulo primario dio CONFORME pero hay píxeles alertados
     con magnitud a 5 km o menos de la cumbre.

El criterio completo, con sus cortes y la razón de cada uno, está en
`CRITERIO_NULO_POR_PIXEL.md` (sellado en `HASH_CRITERIO_NULO.txt` antes de escribir el evaluador).

Re-evaluar en local unas salidas ya bajadas:
`python experiments/_s146_bateria/evaluar_bateria.py --out <carpeta con un directorio por brazo>`.

## Límites declarados

- La magnitud de los cúmulos no primarios es la suma CRUDA de sus píxeles. El núcleo focal, el tope
  de 5 MW del camino D y el modo de un píxel el pipeline los aplica sólo al primario; para ese sí
  se guarda además la magnitud publicada.
- Cuando publica el bloque del Test 1, la lista incluye también los píxeles de ese bloque (rotulados
  `test1_integrado`). Están a menos de 3 km de la cumbre, así que no pueden llenar una caja a
  9,5 km, pero sí la caja de cumbre de un negativo (y en ese caso el veredicto por cúmulo ya era
  falso positivo).
- Los caminos `legado:*` se calculan siempre pero, con el primer pase encendido, no forman la
  máscara final: dicen qué más vio ese píxel, no por qué quedó alertado.
- El nulo por píxel usa todas las pasadas nocturnas, sin el filtro de validez por NTI de A5, A6 y
  A8 (más oportunidades de llenar una caja nula).
- No arregla los otros defectos del instrumento que S138 documentó (mezcla de pasadas de dos
  noches, cúmulos con tope de 5 MW contados como aciertos). No adopta nada ni mide paridad con
  MIROVA.
- Hallazgo de paso: `sha256sum docs/audit_s146/A2_CRITERIO_PRE_REGISTRADO.md` en este checkout de
  Windows NO da el hash sellado, porque `core.autocrlf=true` dejó el archivo con CRLF (245 retornos
  de carro medidos). Con los finales normalizados a LF sí coincide (`758b3ea1...`). Por eso el
  evaluador y el workflow hashean con LF.

## Prueba local, sin MODIS ni credenciales

`python experiments/_s146_bateria/prueba_local.py` (31 s). Corre `calculate_vrp` REAL sobre una
escena sintética con un foco en la cumbre y otro plantado 10 km al este, arma los 10 brazos con el
mismo código del probe, y prueba el evaluador y el verificador de cobertura contra salidas con
píxeles conocidos, cada control con su contraparte. Lo que NO prueba: la lectura de HDF4, la
búsqueda y descarga en NASA, y el comportamiento de `actions/download-artifact` al juntar brazos.
