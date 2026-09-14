# Bloque de arranque S140

> Cierre de S139 (2026-09-13 17:23 a 2026-09-14 14:15 UTC, hora del servidor). Rama `main` en
> `fcd6dbe03`, verificado igual al remoto con `git ls-remote`. Suite **1331 passed**, 4 skipped, 2
> xfailed (corrida al cerrar). Sin agentes vivos, sin ramas `s139-*`, sin PR abiertos, un solo
> worktree. Los commits del cron NRT y del sync seguirán aterrizando sobre `data/`; no invalidan nada.
> Los 4 stashes de S72 a S78 siguen intactos. Modelos usados: Opus 5 y Fable 5.1 (cambió a mitad).

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **S138-H**: `isValidDetection` exige cúmulo con energía (index y mosaico) | **mergeado y publicado** | PR #642 `b973ccc39`; guard `tests/test_isvaliddetection_coherencia_s139.py`; Pages verificado en el sitio |
| Auditoría de paridad: 6 ejes + verificador limpio + descomposición de magnitud | **mergeada** | PR #643; `docs/audit_s139/EJE_1..6_*.md`, `VERIFICADOR.md`, `MAGNITUD_DESCOMPOSICION_OSF.md` |
| Tanda 2: bases de Mirova-v1, OSF contra NRT, cadencia del NRT, lectura de PDFs, distancia contra TIF | **mergeada** | PR #643 (2º commit), #645, #646; `docs/audit_s139/MAPA_BASES_MIROVA_V1.md`, `OSF_VS_NRT.md`, `NRT_CADENCIA_Y_MEJORAS.md`, `LECTURA_PDF_TABLAS_FIGURAS.md`, `DISTANCIA_MIROVA_VS_TIF.md` (con adenda del orquestador) |
| **Plan definitivo de paridad** | **APROBADO por Nicolás 2026-09-14** | `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md` (§0 decisiones, §2 terminado, §7 revisión) |
| **Plan de ejecución de la Fase 0** (11 tareas) | **escrito, NO iniciado** | `docs/superpowers/plans/2026-09-14-fase0-instrumento-paridad.md` (PR #644, #646 a #649) |
| keep_peak 0,708 → 0,692 explicado | medido, evaluador S135 reproducido exacto | `experiments/_s139_audit/keep_peak_paridad/RESULTADO.md` |
| Artefactos A/B S129/S130/S133/S135 rescatados antes de vencer | 172 de 172, 433 MB, **fuera de git** | `experiments/_artefactos_ab/INVENTARIO.tsv` |
| Borrador de correo a Coppola (12 preguntas) | **escrito, sin enviar** (lo envía Nicolás) | `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md` |
| Aviso a Mirova-v1 (filas perdidas, coma de miles, mojibake) | **issue abierto** | `MendozaVolcanic/Mirova-v1#19` |
| Archivo de TIF local | copia en 2026-05-20; el `git pull` completo **falló** (remoto 16,5 GB, disco al 100 %); se borraron 12,5 GB de `tmp_pack_*` huérfanos | `../mirova-tif-archive`; 400 TIF bajados selectivamente a `experiments/_s139_audit/distancia_tif/_dl_/` (ignorado) |
| NRT | vivo, verde, pero ~5 corridas diarias: GitHub despacha con ~3,5 h de atraso desde 2026-08-27; cobertura intacta | `NRT_CADENCIA_Y_MEJORAS.md`; último run 2026-09-14 09:34 success |

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Enviar el correo a Coppola | enviar tal cual · recortar a las preguntas 1 a 5 · no enviar | **enviar**; las preguntas 1 a 5 bloquean los A/B, la 11 cierra la definición de distancia |
| 2 | Token Earthdata (vence ~2026-10-03; ya causó 13 días de apagón en julio) | renovar ya · esperar el aviso | **renovar esta semana**; es credencial suya |
| 3 | Tarea 8a: perfil `experimental` en el cron del NRT (se calcula y se pierde: escribe en `experimental_v2/`, se commitea `experimental/`) | quitarlo del cron · commitear su carpeta real | **quitarlo**; nadie lo consume y es ~la mitad del reloj del job |
| 4 | Tareas 7 y 8 de la Fase 0 tocan `pipeline/` y `nrt.yml` | confirmar caso a caso (A45) | confirmar cuando lleguen, con tag previo |
| 5 | Umbrales de terminado (spec §2): falsas publicaciones ≤ 10 % focales, ≤ 15 % nevados; magnitud en [0,8; 1,25] por volcán | aceptar como partida · otros | **aceptar** y congelar al cerrar la Fase 0, como dice la spec |
| 6 | Magnitud oficial por pasada o máximo de la noche | por pasada · máximo | **por pasada** (como publica MIROVA y el OSF) |
| 7 | S138-E (reintento del cortacircuitos) y S138-F (limpieza de git) | siguen abiertas | fuera del plan de paridad, sesión aparte |
| 8 | Espacio en disco local (97 %) | liberar · dejar | **liberar cuando convenga**: no bloquea reprocesos (corren en la nube) sino análisis locales y fetch grandes |

## c. Lo aprendido

**Reglas generales del workspace** (proponer para `GUIA_MAESTRA_AUDITORIAS.md` §7 e `INVESTIGACION`):

1. **Un conteo sobre un archivo curado no se transfiere al feed crudo.** El OSF de MIROVA está supervisado a mano (Coppola 2023 §2.5, p. 4, leída): se quitaron incendios y falsas alertas. De un archivo así sirven las definiciones por fila, nunca proporciones ni distribuciones. Error propio de esta sesión: di "87 %" y "4 a 8 %" sacados del OSF como si valieran para el NRT.
2. **Al elegir una fuente de datos, la copia que el proyecto trae puede no ser la del dueño.** El snapshot de VRP Chile lo actualiza sólo el auto-audit semanal y estaba 7 días atrás; el workflow horario actualiza otro archivo. La fuente para medir es el remoto, con sha registrado (refuerza la regla 5 del workspace).
3. **Una función de carga "de alertas" es un filtro.** `load_mirova_alertas` descarta RUTINA y FALSO_POSITIVO; un banco construido con ella se queda sin negativos sin fallar. Antes de reusar un loader, leer qué filas descarta (familia A89).
4. **Un intervalo de confianza que excluye las dos hipótesis no apoya a ninguna.** La prueba de la distancia dio +0,113 km [0,072; 0,153] entre 0 y 0,232, y el titular del subagente decía "demostrado". Leer el número contra las dos predicciones antes de repetir el titular.
5. **Normalizar tildes al cruzar nombres.** Mi re-medición sobre el OSF perdió Láscar y Chaitén por `re.sub('[^a-z]','')` sobre texto con tildes (4,0 % contra 6,9 % real).
6. **Un repo de datos puede no caber en el disco.** El `git pull` de `mirova-tif-archive` (16,5 GB) llenó el disco y dejó 12,5 GB de `tmp_pack_*`. Para repos de datos: `index.csv` remoto + descargas selectivas por `raw.githubusercontent.com`.

**Propias del proyecto** (van a `CLAUDE.md` en la próxima revisión, propuestas A97 a A100):

- **A97** (propuesta S138, sigue vigente): atribución de mecanismo simulando el paso siguiente; "publicamos" con el predicado literal del operador.
- **A98**: la brecha de paridad es **sobre-publicación**, no recall (874/877 noches de volcán con alerta; publicamos en ~90 % de noches sin alerta). Toda métrica nueva lleva negativos.
- **A99**: magnitud ~0,7 = **conteo de píxeles** (1 nuestro contra 3 de MIROVA) × **fondo de anillo 3,5 K más tibio**; a igual conteo la razón es 0,995, pero en parte por compensación con la selección del píxel más caliente.
- **A100**: `keep_peak` daba paridad **por accidente** con un píxel a ~3 km del cráter; nunca apagarlo solo.
- **A95 ampliada**: la capa de texto de SP426.5 convierte `>` en punto y `=` en `¼`; toda fórmula se lee renderizada (tarea 9 de la Fase 0).

## d. Problemas abiertos e hipótesis

### CONFIRMADO (verificado con herramienta en S139)

- En noches sin alerta MIROVA, V375 publica en 82 % (por noche-sensor), V750 55 %, MODIS 18 %; cualquier sensor 874/877 en noches con alerta (eje 2, reconciliado por el verificador).
- 1.356 de 2.062 publicaciones V375 en gránulos MIROVA con VRP 0 son el objeto D19 (re-corrí `v3_keep_peak_y_desfase.py`).
- keep_peak OFF: 71 de 574 pasadas comunes cambian de magnitud (53 bajan, mediana B/A 0,40); el píxel del cráter queda 1,21 K sobre el fondo contra 5,86 K en pasadas sin cambio.
- Descomposición contra OSF (re-corrí los 8 scripts): igual conteo R 0,995 (n 342, Fbg 0,873 × Fhot 1,14); conteo distinto R 0,615.
- OSF supervisado a mano (Coppola 2023 §2.5 p. 4 renderizada) y sin solape con el NRT guardado.
- Fernandina 2025 p. 9 (renderizada): coeficiente de Wooster en forma cerrada; grilla UTM 51 km centrada en la cumbre GVP; fondo = vecinos no alertados.
- SP426.5 p. 9 (renderizada): MIROVA declara ~10 % de omisión y ~5 % de falsas alertas.
- Coppola 2014 p. 9 (renderizada): test 2 con `and` explícito.
- El remoto de Mirova-v1 es superconjunto exacto del snapshot (0 diferencias); 852 FALSO_POSITIVO en el consolidado remoto.
- 18 ALERTAS del respaldo del 2026-04-08 faltan en el consolidado (remoto y snapshot).
- `load_mirova_alertas` descarta RUTINA y FALSO_POSITIVO (`pipeline/mirova_csv_loader.py:147-149`).
- 578 de 846 ALERTA_TERMICA_OCR sin distancia por mojibake (`â‰ˆ`).
- El cron corre el perfil `experimental` (`nrt.yml:192`) que escribe en una carpeta que no se commitea; `product_version_from_granule` (`fetch.py:367`) no tiene llamador.

### SOSPECHA (no verificado o evidencia mixta)

- Que la distancia publicada por MIROVA sea `Max_Dist` (píxel más lejano): la pendiente apoya, la constante queda entre hipótesis (n = 171).
- Que el foco dominante esté fuera del radio en ~95 % de los FALSO_POSITIVO sirva para algo más que controlar nuestras `far`: el mismo instrumento sólo ubica el cráter en 33 % de las ALERTA.
- Que Campus 2022, FY-3D MERSI-II y `rs11131528.pdf` traigan umbrales VIIRS (sólo se miró autor y afiliación).
- Que el atraso de ~3,5 h del despachador de GitHub sea algo del repo y no general.
- Que MODIS TIR sea banda 31 en el MIROVA de 2025 (D20; lo afirma el agente, no leí la página).
- La cita fabricada en `docs/MIROVA_DETAILED_CITATIONS.md:216` (la señaló el agente; confirmado por mí sólo que la ecuación 5 impresa es la de NTIbk).

## e. Cerrado en esta sesión, no rehacer

1. **S138-H** (PR #642) y su guard. No reabrir "¿qué es una detección válida?" en index/mosaico.
2. **La auditoría de paridad completa** (6 ejes, verificador, tanda 2). No relanzar los ejes: leer `docs/audit_s139/`.
3. **"El problema es el recall"**: refutado. Es sobre-publicación.
4. **"Banda 22 primero, sola"**: descartado (no mueve la etiqueta far y ya se probó en S133).
5. **Por qué keep_peak baja la paridad** y **por qué la magnitud es ~0,7**: explicados con datos.
6. **"El OSF sirve para recall o precisión del clon NRT"**: refutado. Sólo definiciones por fila.
7. **"RUTINA no sirve como negativo"** (eje 1): corregido por el verificador; sí sirve por gránulo nocturno.
8. **Qué CSV de Mirova-v1 usar**: consolidado y OCR del remoto; los derivados no traen FP ni RUTINA.
9. **Leer la tesis de Massimetti**: fuera (trata de Sentinel-2 y Landsat-8, verificado).
10. **Rescate de artefactos A/B**: hecho; no re-descargar.

## f. Prompt para la próxima sesión

```
Retomo VRP Chile en S140. Antes de creerle a nada, verifica el estado real:

  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
  git fetch origin --prune && git pull --ff-only
  python -m pytest tests/ -q --no-header --tb=line -p no:cacheprovider | tail -1   # esperado: 1331 passed
  gh api repos/MendozaVolcanic/VRP-chile -i 2>/dev/null | grep -i "^date:"          # A86: hora del servidor
  gh run list --workflow=nrt.yml --limit 3                                          # NRT vivo?
  gh api "repos/MendozaVolcanic/Mirova-v1/commits?per_page=1" -q '.[0].commit.committer.date'

Lee en este orden, comprobando contra el codigo de hoy lo que afirme:
  1. tasks/BLOQUE_ARRANQUE_S140.md                          <- este archivo (decisiones §b)
  2. docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md   <- plan APROBADO (§0, §2, §7)
  3. docs/superpowers/plans/2026-09-14-fase0-instrumento-paridad.md        <- las 11 tareas de la Fase 0
  4. docs/audit_s139/VERIFICADOR.md y MAGNITUD_DESCOMPOSICION_OSF.md       <- por que el plan es este

TRABAJO: ejecutar la Fase 0 con executing-plans o subagent-driven-development, una tarea por PR.
  - Orden: 1 (loader OCR) -> 2 (referencia desde el REMOTO de Mirova-v1 + respaldo 8-abr) -> 3 (banco)
    -> 5 (linea base); en paralelo 4 (magnitud), 9 (docs), 10 (papers del grupo MIROVA), 11 (correcciones).
  - 7 (radiancia de fondo persistida) y 8 (NRT) tocan pipeline/ y nrt.yml: tag defensivo ANTES del primer
    edit y confirmacion explicita de Nicolas (A45). 8a: preguntar si se quita el perfil experimental del cron.
  - Preguntar a Nicolas si ya envio el correo a Coppola y renovo el token Earthdata (vence ~2026-10-03).

REGLAS DURAS:
  - Manda la PARIDAD POR SENSOR; la fidelidad literal decide solo entre brazos que empatan (decision S139).
  - Toda metrica lleva NEGATIVOS; se mide por pasada y por noche de volcan, por volcan (S126), con ventana
    y denominador (A90). Predicado del dashboard ejecutado desde frontend/index.html con node, sha fijado.
  - Referencia = registro_vrp_consolidado.csv + registro_vrp_ocr.csv del REMOTO de Mirova-v1 (con sha).
    NUNCA load_mirova_alertas para el banco (descarta RUTINA y FALSO_POSITIVO). NUNCA los derivados
    (positivos, maestro_publicable, registro_<Volcan>).
  - FALSO_POSITIVO = sin informacion para el crater; control positivo de nuestras detecciones far.
  - OSF v2.5 = archivo supervisado a mano: solo definiciones por fila, nunca conteos para el NRT.
  - Formulas de papers: renderizar la pagina (page.get_pixmap) y mirarla. Ni .txt ni capa de texto.
  - Nunca keep_peak apagado solo. Nunca banda 22 sola. Nunca retirar juntos etiqueta far y tope path D.
  - Subagentes son volumen, no fuente de verdad (A48): verificar el numero central antes de repetirlo, y
    leer un IC contra las DOS hipotesis antes de aceptar un titular.
  - No clonar mirova-tif-archive completo (16,5 GB): index.csv remoto + descargas selectivas a _dl_/.
  - NADA de guiones largos ni medios. Espanol de Chile, formas de tu. Fenomeno fisico primero.

SI LA SESION NO ALCANZA: /cierre. Lo que quede a medias va commiteado con su README diciendo que falta.
```

---

## Histórico: bloque S139 (cierre de S138)

Se conserva íntegro en `tasks/BLOQUE_ARRANQUE_S139.md`. Lo que ese bloque daba por hecho y S139 corrigió:
(1) S138-H hablaba de "las 3 vistas" y `isValidDetection` existe sólo en index y mosaico, y el caso de
Tupungatito 2026-08-21 que citaba no era P5 (tenía `triggered_test1 = False`); el defecto real afectaba
2.219 records, no 195. (2) El ejemplo de PP sin la noche del 13 para S138-E se había recuperado solo.
(3) El frente D21/D22 pausado se reemplazó por el plan de paridad aprobado: S138-B, C, D y G quedaron
reformuladas en su §0 y §4.
