# Caminos por los que cada afirmación podría estar mal

Verificador con contexto limpio, tarea S162 MxD03. Escrito ANTES de abrir ningún archivo citado
(sólo leí el encargo, medí disco, hora del servidor y el commit del worktree
`D:\vrp-trabajo\s162-mxd03` = `87e91adf00d20e3535f12831877cf5ba1fa16682`, rama `s162-mxd03-codigo`).
Lo que aprenda después va al informe, no aquí.

## A1. `poblacion_mxd03.py` reproduce la población del §5

1. Los números que reproduce salen de releer una salida ya persistida (cache, JSON intermedio) y no
   de recontar los records: un instrumento muerto daría el mismo número.
2. La referencia que usa no es la congelada: `--ref` apunta a la carpeta pero el script lee otra copia
   (ruta por defecto dentro del repo, `data/mirova_reference/...`), o lee el consolidado congelado y el
   OCR vivo. Comprobar sha256 de lo que efectivamente abre, no de lo que dice el flag.
3. La ventana temporal de los records no es la del §5 (ejemplo: cuenta records escritos después de la
   fecha de corte, o el main congelado no es 80b819828 sino el HEAD del worktree).
4. «K publica» se calcula con un predicado reconstruido en Python y no con el predicado del tablero
   ejecutado por node (`banco_paridad.correr_node`): la vara es otra.
5. «Cenit ≤ 35°» se lee de un campo que no es el cenit del píxel del record (ejemplo: cenit del
   centro del gránulo, o del cráter, o un campo que vale NaN en una fracción y se cuenta como ≤ 35).
6. «Mitades partidas» y «protegidas expuestas» dependen de un pareo a ±120 s: si el pareo usa otra
   tolerancia, otra hora (hora del archivo vs hora de adquisición) u otra lectura (B en vez de A), el
   conteo cambia y aun así puede «coincidir» por compensación.
7. Las etiquetas (`neg_limpio`, protegida, bajo1) se asignan con una función propia y no con
   `banco_paridad.etiquetar`; o la regla SN de D-9 se aplica a MODIS cuando no debe.
8. El total 5.465 coincide pero la composición por volcán o por etiqueta no (compensación entre
   estratos, A90): comprobar los sub-conteos, no sólo el total.
9. El script requiere red (`--sin-bajar` lo evita) y sin red cae a un fallback silencioso que lee
   otra cosa.
10. Reproduce sobre el worktree actual, cuya `data/mirova_equivalent/` podría no ser idéntica a
    `origin/main` 80b819828 (eso lo cubre A7; si A7 falla, A1 falla también).

## A2. `probe_mxd03_ab.py` implementa los brazos del §3

1. Llama a `calculate_vrp` (u otra función de producción) con argumentos distintos de los que pasa
   `scripts/run_pipeline.py` de main: faltan kwargs, cambia un default, se pasa un flag del perfil
   distinto, o se importa `pipeline.profile` con `VRP_PROFILE` distinto de `mirova_equivalent`.
2. El brazo K del arnés no es idéntico a producción porque el arnés usa `_interp_geo` reimplementado
   en vez del de `process_modis.py`, o porque monkeypatchea algo que queda encendido en los demás brazos.
3. El brazo X usa MxD03 pero sólo para la posición del píxel, y la geometría de área/cenit sigue siendo
   la de K (o al revés): «X» mide a medias.
4. Los brazos de nulo R00 a R19 no están restringidos al cenit ≤ 35° del record de K sino al cenit de
   otra fuente (MxD03, gránulo), o la sal no es exactamente «s159-mxd03-r» (mayúsculas, sufijo, el
   índice no entra en la semilla) y entonces las 20 repeticiones son la misma o no son reproducibles.
5. El nulo R desplaza el píxel con una magnitud que no es comparable con la de X (otra distribución,
   otra dirección, sin la restricción de distancia).
6. X_fondo y X_det: los «dos controles de identidad» pueden ser comparaciones contra sí mismos que no
   pueden fallar (control que no puede fallar, A110), o compararse contra K cuando debían contra X.
7. El control 1 (identidad K = producción) compara contra los records persistidos con una tolerancia
   que absorbe la diferencia (ejemplo: redondeo a 2 decimales, comparación sólo de `vrp_mw` y no de
   posición), o compara sólo un subconjunto.
8. La retención de gránulos para el control 4 no guarda lo que `k_en_sha.py` necesita (ejemplo: no
   guarda `codigo_sha`, o guarda el gránulo pero no el MxD03 pareado, o lo guarda en un path que el
   workflow no sube como artifact).
9. Las 4 mutaciones «atrapadas» lo son por caída (excepción) y no por aserción (regla S152: mutación
   que cae no es atrapada); o las mutaciones no tocan el camino que importa (brazos R, X_fondo).
10. El caso base «OK» usa escenas sintéticas en las que K y X coinciden trivialmente (grilla de 5 km
    plana), así que el arnés nunca ha visto un desplazamiento real.
11. El `probar_*.py` importa una copia del probe distinta de la que corre el workflow (ruta relativa,
    `sys.path`), o el workflow llama al probe con flags distintos de los probados.

## A3. `recorrer_en_sha.py` y `k_en_sha.py` (control 4)

1. No hay prueba local: el hueco pesa según si el control 4 decide algo del veredicto (si decide,
   un bug ahí convierte el A/B en INDECIDIBLE o en CUMPLE falso).
2. `codigo_sha` que leen no es el del record retenido sino el HEAD del runner; o el record no trae
   `codigo_sha` (campo con otro nombre, A89) y el script cae a un default silencioso.
3. Re-correr «con el código del sha» hace `git checkout` del sha pero importa el módulo ya cargado
   en memoria (import cache) o del `sys.path` del worktree actual: corre el código de hoy con el
   nombre del sha.
4. El sha es de un squash merge o de un commit que no existe en el clon parcial del runner (fetch
   depth), así que el checkout falla y se clasifica mal.
5. «deriva_de_version» vs «no_reproduce» se decide con tolerancias no escritas en el pre-registro;
   o la clasificación se invierte (si el código viejo reproduce y el nuevo no, es deriva; si ninguno
   reproduce, es no_reproduce).
6. Los scripts no se invocan desde el workflow (no están cableados) y el control 4 queda sin dato.
7. Dependencias del código viejo (pyhdf, perfil YAML con claves que ya no existen) hacen que el
   código viejo ni siquiera importe.

## A4. `evaluar_mxd03.py` implementa §6 y §8 y la tabla del §10

1. Las 12 pruebas «12 de 12» prueban que el evaluador acepta su propio formato, no que implemente
   las reglas: hay que leer qué afirma cada prueba. «0 de 12 contra el vacío» puede ser trivial si
   `evaluar_vacio.py` ni siquiera devuelve el tipo esperado (fallan por excepción, no por aserción).
2. P1 (no perder protegida): se mide sobre «publica» reconstruido en Python, no con node; o sobre
   `vrp_mw` del record y no `primary_cluster.vrp_mw`.
3. P1b, P2: el nulo R se usa para un umbral pero se compara una métrica de X con una distribución de
   R calculada en otra población (cenit ≤ 35° vs toda), o el percentil se toma al revés (unilateral
   del lado que no es).
4. «P2 sobre 35° y sin Cordón Caulle»: el filtro del volcán puede usar un nombre con variante
   (`PuyehueCordonCaulle` vs `Puyehue-Cordon Caulle`, A14) y entonces no excluye nada.
5. P4, P5, P6: pueden ser métricas que informan pero que el veredicto no consulta (o al revés, M que
   debía sólo informar decide).
6. La tabla del §10 tiene celdas (combinaciones de P que pasan/fallan) que el código no cubre y cae
   a un `else` que devuelve CUMPLE.
7. Los controles 1 a 8 del §8: alguno puede no estar implementado y el evaluador reporta OK por
   ausencia (ausencia silenciosa, S157); o un control que falla no bloquea el veredicto.
8. Las 5 mutaciones atrapadas pueden ser todas del mismo tipo (ejemplo: 5 veces cambiar un umbral)
   y no cubrir los caminos que importan (nulo, exclusión de volcán, protegidas).
9. Punta a punta: la salida del probe que entra al evaluador puede tener un esquema distinto del
   que el probe real escribe (la prueba fabrica el JSON a mano), así que lo que se probó es el
   evaluador contra un formato inventado.
10. Faltan datos de alguna parte (de las 24) y el evaluador no lo detecta: evalúa sobre una población
    incompleta y da CUMPLE (A108: cobertura antes del veredicto).
11. La unión arnés-población: si el arnés y la población congelada discrepan en etiquetas, cuál manda
    (dice un commit que «la etiqueta de la población congelada manda»: comprobar que ese control
    puede fallar).

## A5. `vara_mxd03.py` (vara VIIRS)

1. «Sin cambiar el instrumento de la 1.23»: puede importar `construir_vara_viirs.py` pero pasarle
   parámetros distintos (tolerancia, ventana, lectura), o copiar su código con cambios.
2. 83 de 92 y 65 bajo 35°: el cenit de la vara es el de VIIRS (otro sensor), no el de MODIS; si la
   regla pide el cenit del record MODIS de K, 65 está mal calculado por construcción. Y «92 alertas»
   puede incluir o excluir las que la regla SN de D-9 descarta en VIIRS375.
3. «Congelada antes del despacho»: congelada quiere decir sha256 en el manifiesto y leída del archivo
   por `--evaluar`; si `--evaluar` la reconstruye al vuelo con la referencia viva, no está congelada.
4. `evaluar_sola.vara` (lectura 3): la función puede recibir la vara con otro esquema de claves y
   leer defaults silenciosos.
5. La vara se construye con la referencia congelada o con la viva (`--ref`): comprobar la ruta real.

## A6. Workflow `probe-s162-mxd03.yml`

1. `on:` sin comillas (Norway, A43) → inválido; validar con `yaml.safe_load` y ver las claves.
2. Las ramas del `push` admiten patrones (`s162-mxd03-*`) que incluyen la rama de código
   `s162-mxd03-codigo`: cada push de código despacharía 47 h de runner.
3. Autentica con `EARTHDATA_USERNAME/PASSWORD` además del token (par vencido, A71, bloquea la
   cuenta); o el «falla al instante si viene vacío» comprueba la variable en un step distinto del que
   la usa, o con `-z` sobre una variable no exportada.
4. `runs-on: ubuntu-latest` en vez de `ubuntu-24.04`.
5. 24 partes en 3 tandas: `max-parallel`, `needs` o matrix pueden no estar como dice; el timeout del
   job (`timeout-minutes`) puede ser menor que costo × 1,3 (A15) o faltar (default 360 min = 6 h).
6. El workflow hace `git push` a main (debería ser sólo lectura; si pushea, le falta `group:
   push-main` o retry).
7. Los artifacts (records retenidos, salidas por parte) no se suben o tienen `retention-days` corto.
8. El workflow corre en la rama pero sólo es despachable desde main (`workflow_dispatch` 422);
   con `push` eso no aplica, pero hay que ver que el yml esté en la rama que se pushea.
9. Instala dependencias que no fijan versión (numpy 2 vs 1) y K deja de ser producción.
10. Checkout parcial (sparse) que no trae `data/mirova_equivalent/` o la referencia congelada.

## A7. Rama idéntica a `origin/main` 80b819828 en las rutas de producción

1. `git diff --stat 80b819828 HEAD -- pipeline scripts volcanoes.yaml frontend data/mirova_equivalent`
   debe dar vacío; si el worktree es un checkout parcial (sparse), el diff de rutas no materializadas
   puede dar vacío sin que estén ahí (comprobar `git sparse-checkout list` y que los archivos existen
   en disco, porque el arnés los importa del disco).
2. `origin/main` local puede estar atrasado respecto del remoto (A25/A52): comprobar que 80b819828
   existe y qué es `origin/main` hoy; si main avanzó, el despacho compara contra una producción que ya
   no es la de hoy (eso no invalida el A/B pero hay que decirlo).
3. Archivos sin seguimiento (`??`) dentro de esas rutas que el import sí ve.
4. `pipeline/profiles/*.yaml` y `pipeline/profile.py` se leen por `VRP_PROFILE`: si el arnés fija otro
   perfil, el código es idéntico pero el comportamiento no.

## A8. La adenda del sello no cambia lo sellado; la implementación no se aparta

1. La adenda puede cambiar «cómo se mide» (tag sobre commit de disparo, censo re-medido) de un modo
   que mueve la población o el nulo aunque diga que no cambia la pregunta.
2. Apartamientos típicos: número de repeticiones del nulo, umbral del cenit, nombre de la sal,
   exclusión de volcanes, tolerancia del pareo, qué cuenta como «publica», sensores de la vara,
   percentil del nulo, y qué pasa con records sin MxD03.
3. El código puede tener una regla extra «razonable» que el sello no tiene (una regla no sellada es
   un apartamiento aunque mejore).
4. Lo sellado puede ser ambiguo y el código eligió una lectura; eso se lista como apartamiento con
   peso bajo, no se oculta.

## Control positivo general
Para cada script, meter una mutación propia (distinta de las del auditor) y ver que la prueba la
atrape por aserción. Para cada conteo, cambiar el denominador y ver que el número se mueve.

---
sha256 (antes de esta línea): d2cbfe9221788f5b704903c96d61b13827a731f82d52ea5d33199b626e07a53f
Hora del servidor (header Date de api.github.com): Sat, 24 Oct 2026 15:49:57 GMT
