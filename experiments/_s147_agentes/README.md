# Instrumentos de los agentes de S147, rescatados del scratchpad

> Estos scripts los escribieron los agentes con contexto limpio de S147 en el scratchpad de la
> sesión, que muere con ella. Se copian acá **tal como quedaron**, sin limpiar ni probar de nuevo,
> porque el proyecto ya perdió instrumentos por esa vía (lección de S146: se pierden los
> instrumentos, no las conclusiones). Sus conclusiones ya viven en `docs/audit_s147/`.
>
> **Estado: NO revisados ni re-corridos desde el repo.** Traen rutas absolutas al scratchpad y a la
> copia local de `mirova-tif-archive`, así que para volver a correrlos hay que ajustar esas rutas.
> Sirven para ver **cómo se midió** cada número de los informes, no como herramienta lista.

| archivo | de qué agente | qué mide | informe |
|---|---|---|---|
| `an1.py` a `an5.py` | verificador del pre-registro | los hallazgos H1 a H14 sobre los umbrales y la cobertura del A/B | `docs/audit_s147/VERIFICADOR_PREREGISTRO_AB.md` |
| `an6.py`, `poder_rerun_A.json` | verificador del pre-registro | el nulo de poder barajando por **bloque de noche** en vez de por record (H9): con la estructura preservada el azar alcanza la vara de pasada de VIIRS 750 | ídem |
| `medir_f05.py`, `dump_recs.py`, `ref.py` | verificador de F-05 | cuánto se mueve la razón de magnitud contra MIROVA si se publicara la suma de píxeles en vez del núcleo (1.512 pares) | `docs/audit_s147/VERIFICADOR_F_05.md` |
| `render.py`, `extraer.py` | papers y F-05 | renderizar páginas de PDF a PNG a 200 dpi (A95) y extraer texto para ubicar pasajes | `docs/audit_s147/INFORME_PAPERS_POR_QUE_MIROVA_CALLA.md` |
| `common.py`, `pair.py`, `master.py` | agente de TIF | parear los TIF de MIROVA con nuestros records por hora de adquisición | `docs/audit_s147/INFORME_TIF_QUE_VE_MIROVA.md` |
| `medir.py`, `medir2.py` | agente de TIF | la medición central: BT de MIROVA contra la nuestra en la misma celda, exceso sobre el fondo, percentil en el disco de 5 km con su nulo | ídem |
| `cruzado.py`, `cruzado.json` | agente de TIF | el control contra la maldición del ganador (A109): el mismo punto en otro gránulo de la misma noche | ídem |
| `picos.py`, `picos.json`, `smooth.py`, `smooth.json` | agente de TIF | si el remuestreo de MIROVA es por vecino más cercano o interpolado, y si conserva picos de una celda | ídem |

La versión **del repo** de la medición de TIF, ya con rutas relativas, sus límites declarados y
corrida sobre el régimen de hoy, es `experiments/_s147_tif/residual_contra_tif.py`.
