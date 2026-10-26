# S163: #889 puesto al día sobre `main` (qué se conservó, qué se retiró y por qué)

Lo que todavía aporta de #889, reescrito en la rama nueva `s163-instrumentos` (PR #909) sobre `origin/main` en
`691e4d588` (después de #897, #903, #904 y #905). No reescribí `s159-instrumentos`: el force-push a esa rama quedó
bloqueado por permisos, así que sigue intacta y además en el tag `pre-s163-rebase-889` (`d0968e389`). Lo de S159 sigue en
`experiments/_s159/instrumentos/NOTAS.md` como historia; las salidas de esta pasada están acá.

## Qué se conservó

**I1, cobertura en el NRT.** Sigue haciendo falta. El fenómeno: el satélite pasa o no pasa sobre el volcán, el
catálogo de NASA tiene el gránulo o todavía no, y la geolocalización (MOD03, VNP03) a veces llega tarde o no llega.
Hoy el NRT sólo distingue «falló la búsqueda» de «salió bien»; un día en curso, una búsqueda vacía para un volcán y un
L1B sin geolocalización terminan iguales a «no hubo nada». #897 (S161) agregó un conteo por plataforma que avisa
cuando una plataforma dio cero en **toda** la corrida, pero no dice el volcán ni el día, ni ve la geolocalización
ausente ni el día parcial. I1 deja eso escrito por volcán y día.

Cómo se fusionó con #897:
- `pipeline/fetch.py`: `_INCIDENCIAS` vive al lado de `_FALLAS` y `_PLATAFORMAS`; `limpiar_fallas()` limpia las tres.
  La incidencia `sin_granulos` se registra en la misma rama donde #897 cuenta la plataforma muda, con la misma
  condición (sólo si la búsqueda no falló). Cabecera FICHA actualizada.
- `scripts/run_pipeline.py`: `informar_cobertura(..., plataformas=..., incidencias=...)`. «Completa» exige ahora las
  dos cosas: ninguna plataforma faltante (S161) y ninguna incidencia (S159). Las incidencias se imprimen en una
  función aparte (`_informar_incidencias`) para no tocar el bloque de fallas de S157. Cabecera FICHA actualizada.
- `scripts/reproc_brazos.py`: igual que en #889.
- `tests/test_cese_plataforma_nrt_s161.py`: el fixture congela `fetch.dia_incompleto` en `False`. Por qué: esas pruebas
  simulan el día siguiente al cese de Suomi NPP (2026-11-03, hoy en el futuro), y con I1 un día sin terminar es
  «día parcial», que cuenta en modo estricto; una de ellas salía con 3 por el reloj y no por el cese. El día parcial
  lo prueba `tests/test_cobertura_incidencias_s159.py`.

**El código de salida del NRT no cambia**: `nrt.yml` no pasa `--estricto-cobertura`, y sin modo estricto
`informar_cobertura` devuelve 0 en todos los casos (lo fijan las pruebas parametrizadas con `estricto=False`). Lo que
sí cambia en el NRT: el log deja de decir «Cobertura: completa» (el día en curso siempre es parcial) y gana una
sección «Incidencias de cobertura». En los reprocesos con `--estricto-cobertura` (`reproc_brazos.py`,
`reproc-chunked.yml`) un L1B sin geolocalización o un día sin terminar ponen el job rojo (código 3): es el cambio
buscado (A108), pero es un cambio de comportamiento que Nicolás tiene que aprobar.

**I3, una sola ventana de pareo con MIROVA.** No estaba superado: #903, #904 y #905 hicieron que
`evaluador_comun.py`, `auto_audit_weekly.py` y `vigilancia_sombra.py` importen `clase_mirova.VENTANA_S`, pero
`banco_paridad.TOL_S = 120` seguía escrito como literal. Se conserva el cambio de #889 (importar la ventana) y la
prueba suma `evaluador_comun.py` a la lista vigilada. Ningún número cambia: la ventana sigue en 120 s.

**A, prueba `xfail(strict=True)` del tope de cordura de VIIRS 375** (R2-7). `pipeline/store.py` no cambió desde
#889 y el defecto sigue: la prueba sigue en xfail. No se arregla acá (A45).

## Qué se retiró

**I2, placebo obligatorio en el evaluador de D25.** Ya había salido de #889 en su segundo commit (`d0968e389`), a
#890, porque cambiaba un pre-registro sellado. Desde entonces: D25 se decidió NO ADOPTAR (D-48; tabla del
`tasks/BLOQUE_ARRANQUE_S163.md` de `loop/activo`), así que el «choque a decidir» de I2 ya no bloquea nada; y la idea
del placebo como instrumento general quedó en `scripts/evaluador_comun.py` (#905: placebo de ganancia K×1,2 y K×0,8
con el comparador d′, y los placebos de D-44). Este PR no trae nada de I2. Qué hacer con #890 lo decide Nicolás
(probablemente cerrarlo como superado por #905; no lo toqué).

Los archivos de evidencia de I2 de S159 ya no estaban en la rama; `experiments/_s159/instrumentos/mutar.py` conserva
su grupo i2 como historia, pero ese grupo ya no aplica. El control de esta pasada es
`experiments/_s163_rebase_889/mutar.py` (grupos i1 e i3).

## Lo que I1 no cubre

- **VA61-01** (verificador de A61, rama `s162-a61-mxd03`, `experiments/_s162_mxd03/a61/verificador/INFORME_VERIFICADOR.md`):
  unos 215 records MODIS con el píxel más cercano al cráter en la primera o última línea del gránulo se guardan como
  noches observadas sin anomalía. Eso pasa **dentro del procesador**, después de que fetch entregó el gránulo: I1 no
  lo ve. Arreglarlo es un estado «sin dato» por record en `pipeline/process_modis.py` o `pipeline/store.py` (A45), otra
  tarea.
- Un L1B que no llegó al disco con su geolocalización sí presente queda en silencio (habría que cruzar al revés), y un
  día que el catálogo tiene a medias después de las 3 h no se puede ver desde acá (igual que en S159).
- El estado «sin dato» no llega a `data/` ni al tablero: vive en el log y en el JSON de cobertura.

## Salidas de esta pasada

- `rojo.txt`: las pruebas conservadas sobre `main` sin el port: 11 fallan (las 10 de I1 y la de I3), 6 pasan (los
  controles) y 1 xfail (A).
- `verde.txt`: las pruebas conservadas más las de cobertura de S157 y S161, con el port. Dio 73 en verde y 1 roja,
  `test_tras_el_cese_el_modo_estricto_no_falla_por_el_retiro` (S161), que salía con 3 por el día parcial del
  2026-11-03 y no por el cese: de ahí el congelado de `dia_incompleto` en su fixture.
- `mutaciones.txt`: control de mutaciones (atrapada sólo si cae por aserción): **9 de 9 en I1 y 2 de 2 en I3**. Las
  dos de I1 que reescribí a mano para el código fusionado dieron «NO APLICA» en la primera pasada (el texto de la
  mutación no calzaba) y se corrigieron antes de la corrida que quedó en el archivo.
- `suite.txt`: suite completa sobre árbol quieto (A112), sobre el commit `6d31e417c`: **2.528 pasan, 29 saltadas,
  2 xfail, 0 fallas**. Una primera corrida, antes de ese commit, había dado 2 fallas del guard G8 de citas
  `archivo:línea` del CLAUDE.md (`run_pipeline.py:252` y `:262`): mi texto nuevo en la cabecera FICHA de
  `run_pipeline.py` agregaba una línea. Se reescribió con el mismo número de líneas.
- `mutacion_fallas_e_incidencias.txt`: prueba agregada después de la suite, a pedido del verificador (nadie probaba
  fallas e incidencias en la misma corrida). Su mutación (no informar las incidencias cuando hay fallas) cae por
  aserción en los dos modos. Esa prueba corrió sola (15 de 15 en su archivo), no dentro de `suite.txt`.

## Verificador limpio (otro modelo, sin mi conclusión)

Sin regresión en el código de salida del NRT sin modo estricto (todos los retornos dan 0; `nrt.yml` l. 195 y 236 no
pasan `--estricto-cobertura`), ninguna excepción nueva, interacción con #897 coherente (una plataforma retirada por
cese no genera incidencia, una búsqueda caída no se cuenta como «sin gránulos»), ninguna prueba que dependa de la
hora, y el xfail del tope sigue reflejando el defecto (`pipeline/store.py` l. 551 contra 555 a 557). Lo que señaló y
queda declarado, no arreglado:
1. En el NRT «Cobertura: completa» ya no puede salir nunca, porque la ventana incluye siempre el día en curso. Es lo
   que se buscaba (el día en curso no está completo), pero la señal «completa» deja de servir en el NRT.
2. Los reprocesos estrictos (`reproc-chunked.yml`, `reproc-s146-ab-sin-test1.yml`, `reproc_brazos.py --estricto`)
   salen con 3 si la ventana toca el día en curso o un L1B sin geolocalización; sus comentarios todavía hablan sólo
   de «búsqueda o descarga». Con qué frecuencia aparece `sin_geolocalizacion` en un reproceso histórico no está
   medido (la única cifra es la de VB-1, 72 contra 68 el 20-oct): SIN DATO.
3. Cosmético: una plataforma muda sale dos veces en el log, en la nota de S161 y entre las incidencias.
