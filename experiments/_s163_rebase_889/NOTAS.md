# S163: #889 puesto al día sobre `main` (qué se conservó, qué se retiró y por qué)

Rama `s159-instrumentos` reescrita sobre `origin/main` en `691e4d588` (después de #903, #904, #905 y #897). La rama
anterior queda en el tag `pre-s163-rebase-889` (`d0968e389`). Lo de S159 sigue en
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
- `verde.txt`: las pruebas conservadas más las de cobertura de S157 y S161, con el port.
- `mutaciones.txt`: control de mutaciones (atrapada sólo si cae por aserción).
- `suite.txt`: suite completa sobre árbol quieto (A112).
