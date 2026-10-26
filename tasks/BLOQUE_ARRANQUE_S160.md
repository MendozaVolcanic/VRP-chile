# Bloque de arranque S160 (cierre de S159: «retomar» + loop + ola 2 y 2b + guía de auditorías, 2026-10-21 y 22)

Escrito el 2026-10-22 ~03:40 UTC sobre `loop/activo` (`bcdc328fa` antes de este commit, igual al remoto). **El estado se
fijó CON TRABAJO EN CURSO** (ver tabla a, filas «corriendo»): cuatro agentes de la sesión S159 siguen vivos y van a
commitear en sus propias ramas después de este cierre, y dos sesiones aparte (auditoría S160 y auditoría de Mirova-v1)
siguen solas. La sesión nocturna que toma el loop después de este cierre es la ÚNICA dueña del loop; la sesión S159
queda sólo como relevo de los informes de sus agentes. El detalle de cada vuelta está en la bitácora
`tasks/LOOP_OBJETIVOS.md` §6 (entradas del 2026-10-21 y 22) y la cola de decisiones en su §5 (D-28 a D-34).

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| D25: placebo como comparador (D-28) | **SELLADA e implementada** | `experiments/_s157_prereg_d25/ADENDA_PLACEBO.md` (`2629f5a16`), código `b4258040c`, verificador PARCIAL `63e310af5` (rama `s159-evaluador-d25`) |
| D25: respuestas a las 5 preguntas (D-30), 1.000 repeticiones (D-32), P2 por bootstrap de bloques (D-34, reemplaza a D-33) | **en implementación, corriendo** | agente de S159 en `C:\vrp-trabajo\s159-evaluador`; remoto de la rama en `7cbee245a` al cerrar |
| D25: días sin CMR (D-29) | **SELLADA**: sin el 17 al 20 ni el 13 parcial, declarados | §5 del loop |
| D25: veredicto | **SIN LEER** | falta: entrega de la segunda vuelta, verificador limpio de D-30, D-32 y D-34, tag de lectura, referencia congelada por hash |
| Frente M (MxD03) | **CONFIRMA**, verificado (3 confirmadas, 1 parcial) | `experiments/_s159/m/` y su verificador, en `s159-pruebas` |
| Frente N (fondo y suma del código) | F enciende de más; **censo** ΔE **+12** (no +104); grilla de GEO confirmada (razón 1,000) | `experiments/_s159/n/` con apéndice del censo, verificador |
| Chillán MODIS (#864) | caen en el **Test 2** (dNTI a 3,7σ) y la magnitud sale 0 por el fondo; con el flag real `min` sola detecta | `experiments/_s159/chillan_modis/` y su verificador |
| Pareo MODIS | **±120 s es correcto**, no tocar; MIROVA lista el gránulo sur | `experiments/_s159/pareo_modis/` y su verificador |
| Negativo limpio con cráter | **refutado** (no cambia la línea base de K) | `experiments/_s159/negativo_crater/` |
| Gemelo de D25 | K' es copia bit a bit de K (0 de 4.610): ruido de P2 = 0 por construcción | `experiments/_s159/gemelo_d25/` |
| Déficit oblicuo | el paquete de MIROVA lo cierra en V750 (0,996), pero **MIROVA también diluye** (0,503 en la misma noche) | `experiments/_s159/oblicuo_paquete/` y su verificador |
| Código OSF entero | 42 pasos (12 iguales, 22 distintos); no dice nada del gránulo; sin sun-glint de nuestro lado | `experiments/_s159/osf_codigo/` |
| Bibliografía 2025-2026 | Suomi NPP cesa; MODIS C6.1 con retiro anunciado; Coppola 2022 y Aveni 2024 sí describen el 375 | `experiments/_s159/biblio_2026/` (PNG y PDF fuera del repo) |
| Referencia de MIROVA | la tabla pierde filas por **carrera de workflows del scraper**; las 39 reescrituras OCR son **correcciones manuales de Nicolás** | `experiments/_s159/referencia_estable/` y su verificador |
| Rescate de gránulos | 12-oct reprocesado (CMR da 404, el archivo existe en LAADS); 17-19 en CMR NRT por pocos días; SNPP del 20 no existe | `experiments/_s159/laads_rescate/` |
| Cese de Suomi NPP (2026-11-02 13:00 UTC) | se apaga **en silencio**; ninguna vigilancia por plataforma | `experiments/_s159/cese_snpp/` |
| PR del cese (vigilancia por plataforma, aviso en los 3 HTML, ficha SDA v1.10) | **corriendo** (agente de S159, rama `s159-cese-snpp`, sin subir al cerrar) | worktree `C:\vrp-trabajo\s159-instrumentos`; falta verificación en navegador (launch `vrp-frontend-s159-cese`, puerto 8096) |
| Port del código V750 a V375 y MODIS | **MODIS reproduce a MIROVA** (razón 1,006, 50 de 50 protegidas); V375 magnitud 1,000 pero PIERDE PROTEGIDA 6 de 36 pre-registrado | `experiments/_s159/portes/` (run 39712862945); **verificador corriendo** |
| Censo del oráculo sobre 5.476 negativos V750 | **corriendo** (rama `s159-oraculo-censo` en `C:\vrp-trabajo\s159-m`, remoto `96ba0955b`) | incluye las 3 pasadas del 12-oct por URL directa |
| Pre-registro de MxD03 | **v2 lista**, falta verificar el delta y el sello de Nicolás (§11, 12 puntos) | `experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md` |
| Guía de auditorías | **mejorada y en git**: 214 a 442 líneas | repo privado `MendozaVolcanic/workspace-guias`, `31b70f1`; integración en `experiments/_s159/guia_auditorias/` |
| Auditoría S160 | **corriendo en su sesión** (ola 1: F1a, F2, F3, F4) | sesión `local_7491a729-1f11-4a2c-b5db-9dc29f9c436c`, rama `s160-auditoria` en `C:\vrp-trabajo\s159-pruebas` (ese worktree es SUYO), PR #891 del preámbulo |
| Auditoría de Mirova-v1 | **corriendo en su sesión** | sesión `local_767edc9b-ceb8-42fa-812c-3aad0cf338dc`, copia parcial `D:\vrp-trabajo\mirova-v1`, informe en `D:\vrp-trabajo\mirova-v1-auditoria\` |
| Ramas integradas en `s159-pruebas` | M, N (con censo), Chillán, pareo, MxD03 v2, oblicuo, OSF, bibliografía, referencia, rescate, cese (informe), gemelo, negativo, guía A/B/C, port | remoto `2934273f5` |

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | **Brazo de sensibilidad de D25 sobre el 17 al 19 de octubre por NRT** antes de que LANCE lo purgue (urgente, días) | correrlo, declarado aparte, sin tocar el veredicto sellado · no | **correrlo**: dice si incluir esos días cambia el veredicto |
| 2 | Mergear #889 (instrumentos) | tú desde GitHub · darme permiso | **mergearlo tú** (sigue en borrador; marcar «Ready for review») |
| 3 | Mergear #891 (preámbulo corregido, de la sesión S160) | revisar y mergear | **sí**, después de mirar el diff |
| 4 | PR del cese de Suomi NPP | mergear antes del 2-nov | **sí**, en cuanto tenga CI verde y la verificación en navegador |
| 5 | `pipeline/fetch.py`: dejar de pedir SNPP, fallback a listado de LAADS ante cero resultados o 404, registrar la falla | con tag y sí · esperar | **sí, con tag**, en un solo PR después del 2-nov |
| 6 | Sello del pre-registro de MxD03 (v2, 12 puntos del §11) | verificar el delta y sellar · esperar | **verificar el delta primero** |
| 7 | OCR: Nicolás considera `latest.php` lo más creíble | decidir con la tabla sola · informar las dos | **informar siempre las dos**, y que la tabla sola decida en lo nuevo; `clase_mirova.py:65-75` cuenta como protegida una alerta OCR aunque la tabla diga FALSO_POSITIVO |
| 8 | Arreglos del scraper Mirova-v1 (carrera de workflows, OCR) | según el informe de su auditoría | esperar el informe |
| 9 | Ampliar el port más allá de 300 pasadas | sí · no | **esperar a su verificador** |
| 10 | Heredadas: tope de cordura de `store.py` (con tag), páginas de papers en `main`, D-10 diurno (ahora con el sun-glint que falta), #813, λ de B22, PAT, aviso a OVDAS | | ver `tasks/BLOQUE_ARRANQUE_S159.md` §b |

## c. Lo aprendido

Reglas generales del workspace (ya integradas en `GUIA_MAESTRA_AUDITORIAS.md` cuando aplica; el resto, para el `CLAUDE.md` global o la memoria):
- **Un gemelo que corre en el mismo proceso que el control es una identidad, no un nulo.** Mide determinismo, no ruido. El ruido que importa para «¿mejora en general?» es de muestreo (bootstrap por bloques), no de máquina.
- **Antes de ponderar una muestra, preguntar si el conjunto elegible se puede contar entero.** El estimador dio +104; el censo, +12.
- **Un contrafactual se aplica a todos los consumidores del flag**, no a una etapa: «hace falta min y sin compuerta» salió de aplicar `min` sólo al primer pase.
- **Antes de un merge en un worktree compartido, mirar `git branch --show-current`.** Integrar desde el worktree de la rama de origen con `git push origin HEAD:<destino>`. Me pasó con la sesión S160.
- **Las sesiones nuevas sólo se arrancan desde un mensaje del usuario**; en un turno disparado por una notificación queda como tarjeta.
- **Verificar en la fuente primaria todo hallazgo crítico de un agente** antes de pasarlo (el cese de Suomi NPP se comprobó en Earthdata).
- **Repos de datos gigantes: clon parcial** `--filter=blob:none` con `sparse-checkout` (Mirova-v1 pesa 13,9 GB; la copia útil, 158 MB).
- **Las guías del workspace ahora tienen historia** en `MendozaVolcanic/workspace-guias` (lista blanca en `.gitignore`).

Del proyecto (candidatas a reglas A120 en adelante del `CLAUDE.md`, en un PR que toque ese archivo, A113):
- La tabla de `latest.php` es la parte creíble de la referencia; el OCR tiene correcciones manuales y alertas con datos de otra pasada.
- MIROVA lista el gránulo SUR cuando el volcán cae entre dos, y sólo alerta si el cráter está en él.
- MIROVA también tiene el déficit oblicuo: copiar su paquete da paridad, no física. Corregir la dilución es candidato del experimental.
- CMR puede seguir entregando entradas de gránulos que LAADS ya reprocesó (404): una búsqueda vacía o un 404 no son «no hay dato».
- El mismo código V750 de MIROVA, con banda 22 y MxD03, reproduce a MIROVA en MODIS (sin verificar al cerrar).

## d. Problemas abiertos e hipótesis

| problema | estado |
|---|---|
| Suomi NPP deja de entregar el 2026-11-02 13:00 UTC | **CONFIRMADO** (Earthdata) |
| El NRT de LANCE de Suomi NPP también se corta | **SOSPECHA** fuerte (NESDIS «all S-NPP data products, Permanent»); confirmar el 3-nov con `experiments/_s159/cese_snpp/cmr_colecciones_y_granulos.py` |
| La tabla de la referencia pierde filas por carrera de workflows en Mirova-v1 | **CONFIRMADO** por el verificador y por la auditoría de Mirova-v1 (8 commits del bot) |
| 40 a 75 alertas protegidas falsas en el OCR | **SOSPECHA** (auditoría de Mirova-v1, verificador corriendo) |
| El port reproduce a MIROVA en MODIS | **SOSPECHA** hasta su verificador |
| Las 6 protegidas que pierde el port en V375 son filas OCR de otra pasada | **SOSPECHA** (explicación post hoc) |
| D25 sin poder ante un efecto disperso (ruido 0,10 en log10: CUMPLE 1 de 12) | **CONFIRMADO** por el verificador del comparador; declarado en la adenda |
| La causa real de las dos protegidas MODIS de Chillán del #864 | Test 2 + fondo **CONFIRMADO**; «cumbre nevada más fría» como causa física **SOSPECHA** |
| Un `codigo_sha` distinto escribió 5.449 de 5.465 records MODIS de la ventana de MxD03 | **CONFIRMADO** (borrador de MxD03 v2) |

## e. Lo que ya está cerrado y no hay que rehacer

- **El pareo a ±120 s es correcto**; ensanchar empeora (0 de 2.212 alertas rescatadas, doble conteo).
- **Exigir el cráter en el gránulo de MIROVA no cambia la línea base de K** (sólo saca denominador).
- **F (fondo y suma solos) enciende de más**, contado: ΔE +12 sobre el censo de 122 pasadas.
- **La compuerta de 3 K no cambia ninguna publicación en V750** (0 de 391).
- **La grilla de GEO con remuestreo lineal reproduce a MIROVA en V750** (verificado, sin sobreajuste).
- **El veredicto de K de S153 no cambia** por la inestabilidad de la referencia (usó referencia congelada por hash).
- **Las 39 reescrituras OCR a FALSO_POSITIVO_OCR son correcciones manuales de Nicolás**, no un defecto.
- **OSF zm62w sin código nuevo desde julio** (`vigilar_osf_mirova.py`: sin novedades en 7 proyectos).
- **D-33 quedó reemplazada por D-34** antes de implementarse.

## f. Prompt para la próxima sesión

```
Retoma VRP Chile como ÚNICA dueña del loop (sesión nocturna después del cierre de S159). Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (debe ser loop/activo); hora del servidor con gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date (A86).
2. Lee CLAUDE.md del proyecto, después tasks/BLOQUE_ARRANQUE_S160.md entero, después tasks/LOOP_OBJETIVOS.md §5
   (D-28 a D-34) y las entradas del 2026-10-21 y 22 de su §6.
3. Comprueba contra GitHub, no contra este texto: estado de #889, #890, #891 y del PR del cese de Suomi NPP
   (rama s159-cese-snpp); qué commiteó cada agente de S159 después del cierre (ramas s159-evaluador-d25,
   s159-oraculo-censo, s159-cese-snpp; la carpeta experiments/_s159/portes/verificador/ de C:\vrp-trabajo\s159-pruebas).
   Pide al computador que no se suspenda (mcp__ccd_host__request_keep_awake, until session_idle).

Trabajo, en orden:
- D25: cuando la segunda vuelta de #890 esté commiteada (D-30, D-32, D-34), lanza un verificador con contexto limpio
  SÓLO del cambio; si confirma, tag de lectura y relectura de D25 sin los días de D-29, con la referencia congelada por
  hash (MANIFIESTO de S151), informando también la tabla de latest.php sola. Nunca leas el veredicto antes del tag.
- Lee el verificador del port y el censo del oráculo cuando estén; integra sus ramas a s159-pruebas DESDE SU PROPIO
  worktree (git push origin HEAD:s159-pruebas tras traer origin/s159-pruebas), nunca haciendo git en
  C:\vrp-trabajo\s159-pruebas, que es de la sesión S160.
- PR del cese de Suomi NPP: verificación en el navegador de las tres vistas (preview vrp-frontend-s159-cese, puerto
  8096), captura, y dejarlo listo para que Nicolás lo mergee antes del 2026-11-02.
- Si Nicolás contesta la decisión b.1 (sensibilidad de D25 sobre el 17-19 por NRT), despáchala desde el tag de D25
  antes de que LANCE purgue.
- Al llegar los informes de las sesiones S160 y Mirova-v1, súmalos al traspaso; no dupliques su trabajo.

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45; el PR del cese sí toca frontend y
lo mergea él); sólo EARTHDATA_TOKEN (A71); nada de gh run watch ni bucles de gh; disco justo (C: ~14 GB, D: ~11 GB,
parada bajo 3 GB; borrar worktrees de agentes que terminaron con git worktree remove si están limpios y subidos);
git add por archivo; no commitear páginas de papers; esperar el CI con conclusión antes de dar un PR por listo;
español de Chile sin voseo ni guiones largos; rutas absolutas al entregar.

Si la sesión no alcanza: commitea lo que haya, anota en la bitácora qué quedó corriendo (run id) y cierra con /cierre.
```
