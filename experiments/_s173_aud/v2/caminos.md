# Caminos por los que cada afirmación del auditor F2 podría estar mal

Escrito ANTES de abrir ningún archivo citado (regla del verificador, paso 1). Lo que aprenda después va al INFORME.md, no acá.

Varas que uso: producción = pipeline.profile leído con VRP_PROFILE=mirova_equivalent en el worktree de B; PR A = 0a0dae344; PR B = c9525f994; #932 = 28183712a; base = a3c5a9b49 (el main de hoy ya avanzó por commits NRT: 47cdc446f a las 12:25 UTC; eso mismo es un camino: «la base de la afirmación ya no es el main del día»).

## 205 (audit semanal cae con ValueError al primer MODIS publicado por la vía)
- La excepción puede estar atrapada más arriba (try/except en el runner o en el workflow con `continue-on-error`), y entonces sí hay informe o issue.
- El diccionario REGIMENES puede llenarse en otro lugar (función de carga, `setdefault`, `.get` con default) y la l. citada no ser la única ruta.
- El detector VIA_MODIS puede clasificar sólo por `via_codigo_mirova` y no por `final_hotspot_source`, o al revés; el camino que dispara el ValueError puede exigir una condición que la vía no produce (por ejemplo MODIS diurno).
- La prueba citada (tests/test_auto_audit_via_modis_s172.py:111-121) puede justamente cubrir ese caso y pasar porque el código ya lo maneja; o pasar porque el test no pisa la rama.
- «la primera vez que la vía publique MODIS en una noche con alerta de MIROVA»: la ventana del audit semanal puede no incluir la vía hasta semanas después (los records se reescriben); el fenómeno existe pero no «la primera vez».
- «el revert de B no lo arregla» es trivialmente cierto si el defecto está en A; pero si con B apagado el regimen VIA_MODIS no aparece nunca, el ValueError no se dispara: entonces el revert SÍ lo mitiga en la práctica.
- El workflow puede no correr auto_audit_weekly.py con los mismos argumentos que el test.

## 206 (recall de MODIS sin juzgar 7-8 semanas; MIN_N_RECALL=15)
- MIN_N_RECALL puede aplicarse por sensor y régimen, o sólo global; y n puede contar pasadas, noches o alertas (A90: unidad).
- El «n=5 con 8 días de vía» depende de cuántas alertas de MIROVA de MODIS hay por semana; la tasa real de Láscar puede ser mayor y acortar la espera.
- Puede existir un aviso «sensor sin juzgar» por otro camino (flag INSUFICIENTE, o texto en el informe) que el auditor no vio.
- Los flags de recall y magnitud pueden seguir calculándose para el régimen anterior (K) sobre la ventana vieja: «desaparecen» puede ser «aparecen bajo otra etiqueta».
- La ventana del audit puede ser 90 días y no 7: el n crece distinto.

## 208 (revert de B deja de ser limpio si otro PR toca línea vecina del YAML)
- Es una afirmación sobre el futuro (hipotética); hay que medir si HOY existe tal PR (V750-B toca el YAML? #932 lo toca?) y si el revert sobre main+A+#932 (X1) choca o no.
- `git revert` de un merge necesita `-m 1`; un revert simulado por squash da otro resultado.
- Las líneas vecinas citadas (138-148) pueden ser de B y no de A; si A ya las introduce, el revert de B sólo toca una línea.

## 201 (guard de B rojo con #932: sombra_34 no está en VIVOS)
- La lista VIVOS puede derivarse de los yml y no estar hardcodeada; o el guard puede excluir perfiles con `data_subdir` de sombra.
- El guard puede estar en B y #932 cambiarlo; el estado combinado sólo se mide con un merge real de las tres ramas (X1) y pytest sobre ese árbol.
- Puede ser rojo pero por otra razón (import, fixture) que no sea VIVOS.

## 202 (#932 deja rojas 16 de 32 pruebas de la ROI V750-B)
- Las pruebas pueden leer el YAML de la grilla desde el repo (11 entradas) o desde fixture propio; si fixture, no se rompen.
- origin/s169-roi-v750 no está mergeado: combinarlo con #932 necesita merge real; conflictos pueden ser otros.
- «16 de 32» depende de la colección: parametrizadas por volcán; si #932 agrega 34, el número de parametrizaciones crece y el conteo cambia.
- Puede ser que #932 ya actualice esas pruebas (si la rama de la ROI no está en main, #932 no las ve: entonces es un conflicto futuro, no actual).

## 204 (nadie vigila que la guardia K ni su vigilancia corran)
- nrt-monitor puede cubrir «todos los workflows con cron» por lista derivada y no hardcodeada; o la vigilancia de la guardia puede tener su propio `schedule` con issue al fallar (`if: failure()`).
- Un workflow que falla manda correo a Nicolás por GitHub: «nadie vigila» puede ser «sólo GitHub vigila».
- La guardia K puede correr dentro de nrt.yml (y entonces nrt-monitor la cubre indirectamente).
- El árbol citado (a4ce2182a) no es ni A ni B: puede estar desfasado respecto a B.

## 207 (fechan el encendido por distintos criterios: primera observación de la vía vs primera escritura vs constante inexistente)
- Puede que las tres fechas coincidan en la práctica si el NRT sólo reescribe 1 día; el «hasta ~9 días» depende de la ventana de reescritura real (`--days`? `lookback`?).
- El tablero puede usar `processed_utc` y no la fecha de observación.
- La constante inexistente puede existir con otro nombre (A89: el nombre en el punto de uso no es el de la definición).
- El borrador de la regla no está en main: está en loop/activo; citarlo como defecto del PR es mezclar ramas.

## 209 (excepción de la vía distinta de pyproj deja MODIS mudo con NRT verde)
- El try/except puede re-lanzar o caer a K (fallback) para toda excepción, no sólo ImportError; hay que leer el bloque.
- run_pipeline puede propagar el error y el job quedar rojo; el workflow puede tener `continue-on-error`.
- «mudo» puede significar «record sin detección» o «sin record»; lo segundo lo ve la vigilancia de sombra (3 días), lo primero no.
- La vigilancia de la guardia puede detectar «0 records de la vía» más rápido que 3 días.

## 203 (squash de B sin rebase choca add/add)
- Depende del orden real: si A se mergea por merge commit, el squash de B sobre main puede no chocar; hay que simularlo con ambos métodos.
- El archivo citado puede ser idéntico en A y B (add/add con mismo contenido se resuelve solo).

## 210 (citas rotas en la regla: constante, tag, línea del lector; issue remite a regla fuera de main)
- CAMBIO_DETECTOR_MODIS_UTC puede existir en B con otro nombre (grep de la familia `CAMBIO_DETECTOR`), o en frontend/cambio_detector.js como clave JS.
- El tag s170-v375e-lector puede existir y ser legítimo además del re-sellado.
- La línea 47/49: medir con `git show tag:archivo | sed -n`.
- El issue de reversión puede enlazar un archivo que B sí trae (ruta distinta).

## 211 (con B y #932, un mirova_equivalent a mano sobre uno de los 34 corre la vía con grilla no sacada de TIF)
- grillas_mirova.yaml puede marcar el origen de cada grilla (campo `fuente`) y process_modis puede comprobarlo; o la grilla puede ser sólo para la sombra por `data_subdir`.
- La vía puede exigir el volcán en una lista blanca (VIVOS o Tier A) además de la grilla.
- «corrido a mano» no es producción: el NRT no corre los 34 en mirova_equivalent; gravedad depende de si el audit o backfill lo hace.

## X1 (órdenes de merge limpios y mismo árbol; revert de B = main+A+#932 con pruebas verdes)
- Mismo árbol: medir `git rev-parse <merge>^{tree}` en los tres órdenes; conflicto «limpio» puede esconder conflicto semántico (dos ramas tocan el mismo YAML en claves distintas y el merge textual une pero el perfil queda inválido).
- El revert de un merge commit en main con commits NRT posteriores (hoy 47cdc446f) puede chocar con los JSON de data: medir sobre el main de HOY y sobre a3c5a9b49.
- «pruebas verdes»: no puedo correr la suite completa (restricción); correré los archivos de prueba que tocan A, B, #932 y la guardia; declaro lo que no corrí.

## X2 (la vía cuesta ≤33 s por fecha en el NRT y cabe en 50 min)
- Un tiempo medido en local no es el del runner; buscar en runs de GitHub (gh run view con logs) un job MODIS con la vía encendida (sombra o A/B) y leer su duración.
- «por fecha» vs «por gránulo»: el NRT procesa varios gránulos por fecha.
- El 50 min es por paso: sumar al costo del MODIS actual, no compararlo solo.

## X3 (S8 del lector re-sellado de V375-E no marca régimen nuevo con A, B y #932)
- S8 puede leer flags por nombre (`enable_modis_*` no es VIIRS 375) y entonces no marca; pero puede mirar el hash del YAML entero o de process_modis y sí marcar.
- Hay que correr el S8 real sobre el árbol combinado, no deducirlo.
- El tag del lector (12b49057f) puede no estar contenido en A/B: el lector que corre en el árbol combinado puede ser otro.

## Generales
- La copia del worktree s172-modd-encendido está en c9525f994; cualquier «hoy» del auditor puede ser sobre otro árbol (a4ce2182a, loop/activo).
- Las líneas citadas pueden haberse corrido entre A y B (A101).
- Los números del auditor (16 de 32, n=5, 33 s, ~9 días) sin script son creencias hasta que los reproduzca.

---
sha256 (antes de esta línea): 7a43eb53e8775c6ebc7e68c410db2b1860c68dad6444febcf1dca7bf82acffa7
Hora del servidor: Date: Mon, 02 Nov 2026 13:01:32 GMT
