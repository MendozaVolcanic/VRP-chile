# CAMINOS por los que cada afirmacion podria estar mal

Escrito el 2026-10-27 21:58 UTC (hora del servidor de GitHub), ANTES de leer el diff del PR #922.
Solo con las afirmaciones A1 a A8 y el conocimiento general del proyecto (CLAUDE.md, reglas A).

## A1 (bit a bit con flags apagados contra el tag)

1. El golden se congelo con el arnes copiado sobre el tag, pero el arnes mismo puede haber cambiado entre
   399891638 y 3926f6a93 (la comparacion seria del arnes nuevo con el arnes nuevo, no del codigo nuevo con el viejo).
2. El golden puede serializar poco: si el JSON omite campos (stdout de cobertura, codigo de salida, records escritos
   por el store falso), «bit a bit» vale solo para lo que serializa.
3. El commit 399891638 puede no tener `pipeline/` y `scripts/` iguales al tag (la afirmacion lo dice; hay que
   medirlo con `git diff tag 399891638 -- pipeline scripts`).
4. Con #921 (V375-E) integrado en 0df7b5257, `scripts/run_pipeline.py` o `pipeline/` pueden haber cambiado de forma
   que el arnes no ejerce (VIIRS) o si ejerce (resumen de cobertura comun). El golden anterior a #921 puede seguir
   igual por casualidad (el arnes solo corre MODIS) y no probar que el merge es inocuo.
5. El arnes puede fijar la semilla o el reloj de modo que oculte un no determinismo real (S152 argsort inestable).
6. Las cuatro escenas sinteticas pueden no cubrir el caso «crater sin posicion»: con flags apagados da lo mismo,
   pero si ninguna escena lo cubre, A2 tampoco se ejerce.
7. El golden puede haberse regenerado despues (commit que lo toca despues de 399891638).
8. El modo de leer flags: si el arnes pasa `--flag` por monkeypatch de `pipeline.profile`, y el codigo nuevo lee
   el flag de otra parte (YAML, env), el golden mide otra cosa (A89).

## A2 (incidencia unica por descarte, con volcan, fecha, plataforma, granulo; cobertura no «completa»)

1. Doble anotacion: el aviso puede llamarse en `calculate_vrp` y ademas el caller anotar por su cuenta al recibir
   `None`, o anotarse por granulo y por pasada a la vez (dos granulos de la misma pasada = dos incidencias).
2. El motivo puede traer el nombre del granulo solo cuando el arnes lo inventa; con un granulo real el nombre
   puede ser una ruta completa, o None.
3. La fecha puede ser la fecha de la corrida (`--start`) y no la de la pasada; la plataforma puede salir del nombre
   del archivo y no del record.
4. «Cobertura deja de decir completa»: puede seguir diciendo «completa» si el resumen filtra incidencias por tipo
   (por ejemplo solo cuenta las contables) y la nueva no cuenta (A3) y por eso tampoco aparece.
5. El golden `geo_sin_dato_antes.json` puede tener la pasada escrita como noche sin anomalia: entonces «lo unico que
   cambia es esa incidencia» seria falso (tambien cambia el record escrito), salvo que #920 ya la descartara.
6. Con los dos flags encendidos pero sin MxD03 disponible en el arnes, el camino puede no ejercerse nunca
   (la posicion del crater sale del fallback y nunca es «sin dato»).
7. La incidencia puede anotarse tambien cuando la escena esta fuera del granulo por otra razon (`calculate_vrp`
   devuelve None por falta de pixeles de fondo), confundiendo tipos.
8. «Respecto del tag con los mismos flags»: el tag con `ENABLE_MODIS_CRATER_SIN_DATO=True` ya descartaba la
   pasada; el diff puede ademas cambiar que se escribe o no se escribe algo mas (p. ej. el record `no_anomaly`).

## A3 (no cuenta en modo estricto; reproc_brazos la trata como no contable)

1. El modo estricto puede contar «cualquier incidencia» con `len(incidencias) > 0`, no por tipo.
2. `reproc_brazos.py` puede tener su propia lista de tipos contables (copia en linea de la logica, A102) y no
   la del `run_pipeline`.
3. La no contabilidad puede estar implementada por el nombre del tipo en una lista blanca; un typo en el nombre
   (`crater_sin_dato` vs `crater-sin-dato`) la haria contable sin que ningun test lo note.
4. El codigo de salida puede ser 0 por otra razon (el arnes no llega al `sys.exit`), y la prueba no distinguir.
5. La razon declarada («se repite igual en todos los brazos») puede ser falsa si los brazos difieren en
   `ENABLE_MODIS_GEO_MXD03` (un brazo con MxD03 y otro sin): entonces el descarte NO se repite igual y el modo
   estricto si deberia avisar la asimetria de cobertura (A108: contar pasadas por brazo).
6. Puede haber otro consumidor de las incidencias (resumen semanal, `audit-weekly`, tablero) que las cuente.

## A4 (aviso solo en el descarte por crater sin posicion; None igual sin aviso)

1. El aviso puede dispararse con `GEO` solo si el codigo comprueba el flag `SIN_DATO` despues de llamar al aviso.
2. Puede haber mas de un `return None` por «crater sin posicion» (por banda primaria B21/B22, por `_interp_geo`
   y por MxD03) y el aviso estar solo en uno (A102).
3. El aviso puede ser un parametro con default `None` y el codigo hacer `al_sin_dato(...)` sin comprobar que
   exista: un llamador viejo recibiria `TypeError`, no `None`.
4. El aviso puede llamarse antes de decidir el descarte (p. ej. en el calculo de la posicion), y por eso tambien
   en escenas cubiertas con MxD03 parcial.
5. Un `return None` distinto (sin fondo, saturacion, sin pixeles validos) puede compartir rama con el nuevo.

## A5 (solo run_pipeline llama a calculate_vrp de MODIS en produccion y pasa el aviso)

1. Llamadores por nombre calificado o alias (`pm.calculate_vrp`, `from pipeline.process_modis import calculate_vrp
   as X`), A89: el grep del nombre no basta.
2. Workflows de reproceso (`reproc_brazos.py`, `_archive/*.yml`, `scripts/backfill_*.py`, probes S151) que
   llamen a `run_pipeline` por otra entrada o a `calculate_vrp` directo.
3. Un wrapper intermedio (p. ej. `process_granule`, `run_volcano`) que sea el llamador real y al que el aviso
   se pase o no.
4. El llamador de `run_pipeline` puede pasar el aviso solo en una de las ramas (Standard y NRT, o B21/B22).
5. VIIRS: «no le corresponde» se sostiene solo si VIIRS no tiene un descarte equivalente silencioso. Si lo
   tiene, no es falso A5 pero es un hallazgo.

## A6 (10 de 10 mutaciones atrapadas por asercion; controles viva y caida)

1. «Atrapada» puede incluir caidas (excepcion) y no solo aserciones (feedback S152, S156): hay que ver como
   clasifica la bateria.
2. Las mutaciones pueden ser todas de la misma pieza (p. ej. 10 variantes de borrar la llamada al aviso) y no
   cubrir: la lista blanca del modo estricto, `reproc_brazos`, el formato del motivo, la unicidad, el resumen
   de cobertura.
3. La bateria puede mutar una copia que no es la que importa el arnes (feedback S165: mutaciones en copia).
4. El control «caida» puede caer por una razon ajena a la mutacion (import roto) y clasificarse igual.
5. Los asserts del arnes pueden comparar con el golden entero: entonces cualquier mutacion que cambie un byte
   «se atrapa» sin que nadie compruebe la pieza.
6. La bateria puede haberse corrido sobre 0df7b5257 y no sobre 3926f6a93 (el mensaje del commit lo dice): si
   algo cambio despues, el 10 de 10 es de otro arbol.

## A7 (suite 0 fallas sobre arbol quieto; CI verde)

1. El CI del PR en borrador puede no haber corrido todos los jobs, o estar verde sobre un commit anterior al
   ultimo push.
2. Fallas dependientes del disco (`test_guard_libro_de_pruebas_s146` con basetemp en otro disco) o del entorno
   Windows (pyhdf).
3. Un test que lee documentos (CLAUDE.md, FICHA) puede fallar por las citas que A8 toca.
4. «0 fallas» puede incluir skips que esconden el camino nuevo.

## A8 (citas remapeadas por contenido; FICHA v1.17 y v1.16; sin afirmar de mas)

1. El guard G8 puede comprobar la linea por aritmetica (`l. 1595 + n`) y pasar por casualidad.
2. CLAUDE.md puede citar lineas de `process_modis.py` (p. ej. `:1185`, `:1172`, `:64`) que el cambio corrio y
   no se remaparon todas (A101).
3. La FICHA puede describir el flag como «anota la pasada» sin decir que es solo con dos flags encendidos y
   apagados en produccion, o afirmar que el modo estricto la cuenta.
4. El merge con #921 puede haber movido lineas del frontend (`index.html` l. 1595) que G8 vigila.
5. La version de la FICHA puede estar duplicada o fuera de orden (v1.16 de #921 no estar en la rama).
