# Bloque de arranque S170 (cierre de la coordinadora S169, 2026-10-30 ~12:00 UTC)

> **Modo de la próxima sesión: SEGUIMIENTO CON USO MÍNIMO DE TOKENS hasta el domingo 2026-11-01 12:00 UTC.**
> Nicolás está en el 88 % de su tope semanal (todos los modelos; `mcp__ccd_session_mgmt__get_usage`, 11:50 UTC). Hasta
> el reinicio: **ningún agente auxiliar, ni auditoría, ni verificador**. Sólo revisar procesos, refs y responder a las
> sesiones hijas. Lo que necesite un verificador espera al domingo después de las 12:00 UTC.
>
> **El estado se fijó con trabajo en curso**, y algo puede aterrizar encima de este commit:
> - **Nulo del lector de la sombra de V375-E**: `mutar_sombra.py --hilos 2`, lanzado 11:36 UTC desde
>   `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\agent-a105e5b5e327fb68f`
>   (rama `claude/s169-v375e-lector`, `5c121209c`). Identidad PASA, CONTROL y CONTROL_SECCION CAIDA (verificado en
>   `D:/vrp-trabajo/temporales/s169_nulo_lector/stdout.txt`). 142 corridas, 8 a 24 h. Resultados, una línea por
>   mutación, en `experiments/_s168/v375e_sombra/mutar_sombra_salida.txt` de ese worktree; si se corta, se relanza el
>   mismo comando y retoma. Hora, sha y código de salida en `D:/vrp-trabajo/temporales/s169_nulo_lector/inicio.txt`.
>   No editar ese worktree mientras corre (árbol quieto).
> - **Medidor de V750-A** (sesión `local_94f4be0d`, PID 1324, 2 hilos): M44 a M45 de 85 a las 11:57 UTC, todas
>   atrapadas.
> - **MOD-D** (sesión `local_5b198297`, rama `claude/s168-modd-f4-sello` en `6d649f626`): arreglos de la auditoría
>   aplicados; corre las 20 mutaciones del arnés y el ensayo en seco (~14 min, un hilo) y después pone el tag
>   `s169-modd-f4-candado` y queda quieto.
> - Bitácora viva: `tasks/LOOP_OBJETIVOS.md` §6, vueltas 1 a 34 de S169 (rama `loop/activo`).

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| Vigilancia de la sombra | **MERGEADA y probada en GitHub**: #928, squash `77bbb7c9c`. Revisión de la ventana día por día y por volcán y sensor, monitor con issue desde el 2026-11-03 15:00 UTC, log y cobertura como artefacto con el token tachado | run 41034796854 (Láscar `medir=true`: 27 de 27 records de la vía, artefacto sin `eyJ`); run 41036195649 («Sombra: inactivo»); `tasks/LOOP_OBJETIVOS.md` vueltas 21 a 31 |
| Workflow del humo de MOD-D | **MERGEADO**: #927, squash `5e03f0db2`. Pero MOD-D cambió el yml (P2-08, versiones fijadas): sha256 LF nuevo `4047c55a…`, así que hace falta otro PR con ese archivo antes del humo | mensaje de `local_5b198297` 11:57 UTC |
| V375-E lectura lejana | verificada (Sonnet, sin gravedad 3); **Nicolás eligió «Cercano decide»**; anotado como §10 de `PREREGISTRO_E.md` | `experiments/_s168/v375e_lectura_lejana/INFORME.md` en `claude/s168-v375e-sello` |
| V375-E lector de la sombra | tres rondas de arreglos y dos verificadores; **listo para el nulo**, nulo corriendo; falta verificador corto final, tag y Nicolás antes de abrir datos | `claude/s169-v375e-lector` `5c121209c`; `experiments/_s169/v375e_lector_verificador/` en `loop/activo` |
| MOD-D candado §11 | mutaciones reformadas 86 de 86 atrapadas; verificador del candado (VC169-01 gravedad 3) y auditoría F2 atendidos; **tag pendiente** | `experiments/_s169/modd_f4_candado_verificador/`, `experiments/_s169/audit_patrones/f2/` |
| V750-B (2026-11-03) | procedimiento del día escrito y probado (`r4/control_previo_v750b.py`); auditoría F1 cerrada **sin adenda** | `claude/s162-viirs750-2-918174` `b5551b869`; `experiments/_s169/audit_patrones/f1/` |
| ROI de V750 | rama `s169-roi-v750` `cd5aa300c` (sin merge), tag `pre-s169-roi-v750`; sólo toca `roi_v750` y dos comentarios | prueba 32 de 32, nulo 9 de 9 |
| Auditoría de los siete patrones | tres frentes auditados y verificados (F1 V750, F2 MOD-D, F3 infraestructura común) | `experiments/_s169/audit_patrones/`; memoria `feedback_s169_siete_patrones_instrumentos` |
| Congelamiento de `pipeline/` | **decidido por Nicolás**: nada que toque las vías hasta la parada de cada sombra; excepciones la ROI de V750 y emergencias del NRT | §12.6 de `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` |
| `main` | `0b5a76715` (sólo datos desde `77bbb7c9c`) | `git ls-remote` 11:57 UTC |
| Disco | C: 17 GB, D: 19 GB (Nicolás liberó el Windows viejo de D:) | `df -h` |
| #915, #813 | abiertos | `gh issue list` |

## b. Decisiones que espera el dueño

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | PR del workflow del humo de MOD-D con el yml nuevo (P2-08) | mergear tras verificador / no | **Después del reinicio del domingo**: verificador limpio del candado con tag, PR con el yml del tag y frase de Nicolás; luego humo desde el tag |
| 2 | Lector de la sombra de V375-E: aprobación antes de abrir datos | aprobar tras nulo y verificador / esperar | **Tras el nulo y un verificador corto** (domingo); la primera lectura no decide antes de la parada (30 noches y 40 alertas) |
| 3 | Cerrar #915 | tras el audit del 2026-11-02 | **Tras el audit**, comprobando la lista aparte de #924 |
| 4 | VR3-01 (falso rojo MODIS con sólo pasadas diurnas) | arreglo en `scripts/revisar_sombra.py` leyendo «kept 0 of N granules (night filter)» / aceptar | **Arreglo después del reinicio**, antes de que aparezca; no toca `pipeline/` ni el S8 del lector |
| 5 | Sesiones «Scanner fondos» (mañana y noche) corriendo | detener / dejar | **Que Nicolás las revise**: no son del proyecto y consumen del mismo plan |

## c. Lo aprendido

Proyecto (a `docs/META_RULES_S80.md` o `CLAUDE.md` en la próxima revisión):
- **Un control de régimen compara lo que lee la vía, no la carpeta.** El S8 del lector de V375-E comparaba todo
  `pipeline/` y la ROI de V750 lo habría marcado; y no miraba `volcanoes.yaml`, `run_pipeline.py` ni el workflow.
- **Un nulo que escribe sus resultados al final pierde todo con un solo timeout** (VL2-01, gravedad 4). Resultado al
  disco por mutación, reanudable, y aborto si la identidad o los controles fallan.
- **Revisar la ventana día por día, no lo que escribió la corrida**: un día perdido se ve hasta que sale de la ventana.

Regla general del workspace:
- **Antes de un fan-out de agentes, mirar `get_usage` y estimar el costo.** 15 agentes auxiliares en una madrugada
  (~5,7 M tokens según sus propios reportes) dejaron el plan semanal en el 88 % a dos días del reinicio. Memoria
  `feedback_s169_fanout_y_plan_semanal`.
- **Los siete patrones de defecto** (sha con CRLF, lectura repetible, régimen mal acotado, caída como acierto, estado
  externo, salida ciega, texto contra código) se pasan como lista de chequeo antes de sellar o despachar. Memoria
  `feedback_s169_siete_patrones_instrumentos`.
- **La hora de la bitácora se toma con `date -u` antes de escribir el encabezado**: cinco veces puse una hora
  estimada y tuve que corregirla.
- **Con Nicolás en Remote Control no se pueden abrir sesiones ni mostrar tarjetas**: un relevo se hace con un
  subagente en worktree propio, que conserva su contexto entre rondas (`SendMessage` lo reanuda).
- **Un verificador que deja trabajo en segundo plano repite su informe en cada aviso**: pedir «todo en primer plano»
  y, si igual pasa, `TaskStop`.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: las dos pruebas de #928 en GitHub salieron verdes (runs 41034796854 y 41036195649).
- **CONFIRMADO**: el arranque del nulo del lector pasó identidad y controles (stdout del nulo).
- **SIN VERIFICAR**: el juicio de días de la sombra y la apertura y cierre del issue del monitor; los ejerce recién la
  corrida del 2026-11-03 15:00 UTC.
- **SOSPECHA**: VR3-01 (MODIS sin pasada nocturna da rojo hasta 8 corridas); en K, Isluga 4 de 228 días y Láscar 3.
- **SIN VERIFICAR**: el cenit del record de K y el perfil `sombra_codigo_mirova` en un record real (lector de V375-E).
- **CONFIRMADO** (por el verificador del lector): hueco declarado de la base de S8, un cambio en la vía antes del
  2026-11-03 queda coherente consigo mismo; se informa sin marcar.

## e. Lo que ya está cerrado y no hay que rehacer

- La auditoría de los siete patrones en los tres frentes y sus verificadores (no repetir sin cambio nuevo).
- #927 y #928 mergeados; las pruebas manuales de #928.
- La elección del brazo de V375-E (cercano decide) y su §10.
- El procedimiento del día de V750-B y su control previo; no hace falta adenda.
- El congelamiento de `pipeline/` (§12.6).

## f. Prompt para la próxima sesión

```text
Retoma VRP Chile como sesión S170 de SEGUIMIENTO (relevo de la coordinadora S169, cierre del 2026-10-30 ~12:00 UTC).
Hasta el domingo 2026-11-01 12:00 UTC el uso de tokens es MÍNIMO: nada de agentes auxiliares, auditorías ni
verificadores; vueltas espaciadas (60 min o más) y sólo para revisar y responder. Empieza con la skill retomar, pero
corto: no leas archivos grandes enteros.

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (loop/activo); date -u; df -h /c /d; mcp__ccd_session_mgmt__get_usage para ver el plan.
2. Lee sólo tasks/BLOQUE_ARRANQUE_S170.md y la última entrada de tasks/LOOP_OBJETIVOS.md §6.
3. Procesos: Get-CimInstance Win32_Process. Deben estar vivos el nulo del lector de V375-E (mutar_sombra.py, worktree
   .claude/worktrees/agent-a105e5b5e327fb68f) y el medidor de V750-A (PID 1324). Progreso del nulo: wc -l de
   experiments/_s168/v375e_sombra/mutar_sombra_salida.txt en ese worktree (142 líneas al terminar más la cabecera).
   Si el nulo murió sin terminar, relánzalo con el mismo comando desde ese worktree (retoma):
   PYTHONIOENCODING=utf-8 C:/Users/nmend/AppData/Local/Programs/Python/Python312/python.exe -I experiments/_s168/v375e_sombra/mutar_sombra.py --hilos 2
4. git ls-remote origin 'refs/tags/s169-*' 'refs/heads/claude/s168-modd*' 'refs/heads/claude/s169-*': cuando aparezca
   el tag s169-modd-f4-candado, anótalo; NO lances su verificador hasta después del reinicio.
5. Escríbeles con SendMessage que ahora reportan a S170 (tu id): MOD-D local_5b198297-ad3f-4aca-850a-c5dd3d856b80,
   V750 local_94f4be0d-2b32-4570-b711-3a6f14cc8a0a. V375-E local_438070ff quedó relevada (no editar el lector).

Después del reinicio del domingo 12:00 UTC (no antes):
- Verificador limpio del candado de MOD-D con tag; PR a main con el yml nuevo del humo (sha256 LF 4047c55a…), frase de
  Nicolás y humo desde el tag.
- Con el nulo del lector terminado: verificador corto (otro modelo), tag del lector y llevárselo a Nicolás antes de
  abrir datos de la ventana P.
- VR3-01 en scripts/revisar_sombra.py (sin tocar pipeline/).
- 2026-11-02: audit semanal; revisar #915 y la lista aparte de #924; proponer cerrarlo.
- 2026-11-03: V750-B con el procedimiento de experiments/_s162_v750b/r4/INFORME.md §3 y §4 (unset VRP_PROFILE con eco,
  control_previo_v750b.py datos con el data/ de main del día, nunca --leer-con-faltantes con censo FALLA), despacho
  desde tag; C-06 del cese de Suomi NPP en CMR; a las 15:00 UTC, primera sombra con datos: revisar el run, el commit en
  data/sombra_codigo_mirova/, la línea de revisión por volcán y sensor y el monitor (18:30 UTC).
- Después de V750-B: la ROI elegida con scripts/roi_v750b_a_grillas.py --brazo <elegido> --escribir en la rama
  s169-roi-v750, PR y frase de Nicolás (excepción permitida del congelamiento §12.6).

Reglas duras: pipeline/ congelado durante la sombra (§12.6; excepciones ROI de V750 y emergencias del NRT); nada en
pipeline/, data/ ni frontend/ sin tag y sí explícito de Nicolás (A45); merge a main sólo con frase de Nicolás y
gh pr merge --match-head-commit <sha>; sólo EARTHDATA_TOKEN (A71); despachos de a uno desde tags; verificador limpio
de otro modelo antes de aceptar un resultado; máximo 2 procesos pesados locales; temporales en D:; git add por
archivo; nunca git stash; date -u antes de cada encabezado de bitácora; español de Chile sin voseo ni guiones largos;
rutas absolutas. Si la sesión no alcanza o el contexto pasa el 50 %: commitea, anota qué quedó corriendo y cierra con
/cierre.
```
