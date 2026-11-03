# Verificación limpia del PR #940 (instrumental de la prueba retrospectiva del paquete)

Verificador: Fable 5.1, contexto limpio (no escribí el código ni conozco la conclusión del autor). Hora del servidor
de GitHub al cerrar: 2026-11-03 20:45:59 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera `Date`).

- Regla sellada: `experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md` en `origin/loop/activo` `799d22e6c`,
  tag `s173-prereg-retro-sellado` = `26c970564`; blob del archivo `9c58997a3` (igual en el tag y en la punta de
  `loop/activo`; copia en `C:/Users/nmend/vrp-wt/ver940_informe/PREREG_SELLADO.md`, 749 líneas).
- Instrumental: PR #940, rama `claude/s173-retro-paquete`, punta `6e93764bf`, base `main` (merge-base `82b55de0d`;
  `origin/main` `8deb8bbea` sólo agrega commits de datos de la sombra de los 34 desde la base:
  `git diff --stat 82b55de0d origin/main -- . ':!data'` vacío).
- Worktree de lectura: `C:/Users/nmend/vrp-wt/ver940` (detached en `6e93764bf`). Sólo lectura: no comenté, no
  pusheé, no despaché, no toqué `data/`, `frontend/` ni `pipeline/`.
- El PR no toca `data/`, `frontend/`, `pipeline/*.py`, `scripts/` ni `volcanoes.yaml`
  (`git diff --stat origin/main...HEAD -- data frontend pipeline/*.py scripts volcanoes.yaml` vacío); agrega 13
  archivos, 4.276 líneas.
- Suite del PR corrida por mí: `tests/test_leer_retro_s172.py`, `tests/test_perfil_retro_paquete_s172.py`,
  `tests/test_retro_paquete_workflow_s172.py`: **73 pasan en 197 s** (`pytest_pr.txt`, exit 0; node presente, la
  prueba con el predicado real del tablero no se saltó).
- El PR es borrador; su check `pytest` de GitHub estaba `pending` al cerrar.

## Veredicto

**MERGEABLE CON CAMBIOS** como instrumental. Los perfiles, el workflow y el plan de trozos implementan lo sellado con
fidelidad verificable (flags leídos de `pipeline.profile`, padre mutado, sin push, sólo token, pyproj comprobado,
conteos 3/47/30/176 reproducidos). El lector cubre la tabla del §8.1, los controles principales y las lecturas; las
copias de las reglas selladas son byte a byte las de sus tags. Hay tres cosas que pueden dar un veredicto equivocado
sin dar error y que conviene arreglar antes del merge (VPR940-01, 02 y 08), y varias de gravedad 2 que son lecturas
abiertas o controles que no pueden fallar.

**Lo que falta para poder LEER** (distinto de mergear), confirmado contra el código:

1. **C-montaje**: no está construido. El lector lo recibe como JSON externo (`--montaje`) y sin él queda
   `ROJO: sin resultado de C-montaje (L3)` en los tres sensores (`leer_retro.py:1022`, `veredicto()` l. 872 a 874 lo
   lleva a la fila 1). Rehúsa el veredicto: sí. Pero no valida el contenido: cualquier JSON con `"estado": "OK"` lo
   satisface (VPR940-06).
2. **Manifiesto del candado (§11)**: no existe en el PR. `main()` exige `--manifiesto` o `--ensayo` (grupo mutuamente
   excluyente, l. 989 a 991); con `--ensayo` el candado sale `OK (ENSAYO: sin candado, NO DECIDE)` y el lector sigue
   (VPR940-15: la línea impresa por sensor no dice ENSAYO). Lo que sí está candado internamente: los seis módulos de
   reglas (`MANIFIESTO_REGLAS`, l. 82 a 91) se comprueban por sha256 LF antes de importarlos y el lector no sale si
   difieren (l. 155 a 157). Faltan del manifiesto externo: `leer_retro.py`, `clase_mirova.py`, `banco_paridad.py`,
   `referencia_mirova_unificada.py`, referencias congeladas, OSF, `frontend/index.html`, los dos perfiles, el texto de
   V750-A en `aa5583646`.
3. **Excepciones nombradas de C-K (R-15)**: `--excepciones-ck` es opcional; sin archivo, C-K exige 0 diferencias y
   cae con cualquiera (l. 539 a 543). Correcto: la ausencia equivale a «no se tolera ninguna». Lo que falta es
   escribirlas antes de leer F26 si D3 muestra diferencias.
4. **K-gemelo**: `--kgemelo` es opcional; sin él, C-K y el nulo de runner salen `ROJO: sin K-gemelo` (l. 530, 552) y
   todo queda INDECIDIBLE. Rehúsa: sí. Pero no comprueba que cubra lo que D3 manda (VPR940-03).
5. **Caja de VIIRS 750** (`--caja-v750`, de V750-B): sin ella VIIRS 750 es INDECIDIBLE (l. 917). Rehúsa: sí.
6. **Unión de los trozos**: no hay script ni instrucción en el PR para pasar de 47 + 30 + 176 artifacts
   (`trozo-<vol>-<idx>-...`) a las carpetas `--via`, `--kgemelo`, ni para exportar K de `origin/main` al tag
   (`git archive`). `cargar_carpeta` une por la clave `volcano` del JSON (presente en los 11 de K, `scan_k_disco_salida.txt`)
   y marca repetidas, pero nada impide mezclar un trozo de otro perfil (VPR940-18).

## 1. Tabla de cobertura (regla sellada contra el PR)

Leyenda: SÍ coincide; PARCIAL implementa parte; FALTA no está; ABIERTA el pre-registro no lo fija y el PR decidió.

| § | regla, control, ventana, umbral o veredicto | dónde en el PR (archivo:línea) | coincide |
|---|---|---|---|
| §2 | brazo VIA = perfil `_s172_retro_paquete`, K de producción + 3 vías, MxD03 apagado | `pipeline/profiles/_s172_retro_paquete.yaml:20-26`; prueba de identidad con la sombra `tests/test_perfil_retro_paquete_s172.py:56-66` (todas las constantes en mayúsculas de `pipeline.profile`, en subproceso) | SÍ |
| §2 | VIA-radiante, VIA-cercano, VIA-pico desde el record (`distancias_desde_record`) | `leer_retro.py:105-107, 296-300` con `LP.distancias_desde_record` y `LP.variante` (copia del tag) | SÍ |
| §2 | K = records de `data/mirova_equivalent/` en el tag, de `origin/main` | `--k DIR` (l. 977); no hay script de exportación ni control de que esos records sean K (sin marca) | PARCIAL (VPR940-02, 18) |
| §2, §10.1 | K-gemelo = perfil `_s172_retro_k`, vías apagadas | `_s172_retro_k.yaml:20-26`; `tests/test_perfil_retro_paquete_s172.py:69-77` (difiere de retro sólo en las tres vías) | SÍ |
| §2 | PLACEBO = K × 1,2 en toda magnitud | `leer_retro.py:108, 323` con `F4.escalar` (`evaluar_f4.py:128-141`: vrp_mw, pc.vrp_mw, píxeles) | SÍ |
| §3.1 (b) | pasadas miradas por nombre; lectura con y sin ellas; si cambia, fila 4 | `PASADAS_B` l. 124 a 136 (21 pasadas; las horas de VIIRS 750 verificadas en `experiments/_s158_audit_r2/ra1/contar_ceros_v750.txt` l. 71, 100 a 105, 137, 150; Lastarria en `febrero_pasadas_nombradas.txt`; las de 2025 en `pasadas_2025_nombradas.txt`); `es_pasada_b` l. 860; `cambia_sin_pasadas_b` l. 933 a 935 → motivo de fila 4 | SÍ |
| §3.1 | P1-OSF y magnitud R25 con y sin (b) | `candidatas_osf_sin_pasadas_b_informa` l. 947 a 951, sólo candidatas; la magnitud de R25 sin (b) no se calcula | PARCIAL (informa) |
| §3.2 | tramos F26-V, F26-M, F26-M3, R25, DM (VIIRS sin 12 y 13), enero fuera | `TRAMOS` l. 95 a 103, `tramo_de` l. 199 a 205 | SÍ |
| §3.2 | Tupungatito desde 2026-02-23 y fuera de R25 | `leer_retro.py:221`; `plan_trozos.py:112-117` (prueba `test_tupungatito_desde_el_23_de_febrero_y_fuera_de_2025`) | SÍ |
| §3.2 | NOAA-21 `sin_info` en F26; no entra a nada que decida | por etiquetado (sin fila de la tabla → `sin_info`), no hay regla explícita; en R25 cuesta y se corre (declarado) | SÍ (implícito) |
| §3.2, §4.1 | sólo noche, elevación solar del proyecto | `es_noche` l. 1008 con `bp.es_pasada_diurna_descartada`; en el OSF `leer_osf` l. 670 | SÍ |
| §3.3 | F26-V se lee por satélite (rótulo NOAA-20 y Suomi NPP oblicuo; curva por satélite) | rótulo en `nombre_fila6` l. 894; la curva de cenit no se parte por satélite (sólo `plat` entra a la razón doble) | PARCIAL (VPR940-12) |
| §4.1 | decide la tabla sola (CONS); OCR informa; pérdida sólo OCR → fila 4 | `etiquetar_tabla` l. 256 (canal `tabla` = `source == "CONS"`, que incluye las capas histórico y respaldo de `referencia_mirova_unificada.py:172-179`); `solo_ocr_perdidas` l. 358 → `extra` l. 925 → fila 4 | SÍ |
| §4.1 | etiquetas de `banco_paridad`/`clase_mirova` con SN y lectura A | `etiquetar_tabla` l. 258 (`regla_minimas="SN"`), l. 266 (`alerta_protegida(lectura="A")`) | SÍ |
| §4.1 | referencia congelada por sha256 antes del despacho | sólo vía manifiesto externo (no existe) | FALTA (lo que falta para leer, punto 2) |
| §4.2 | OSF: noche del proyecto, `class` 1, VRP ≥ 1e6 W, píxel más caliente a ≤ inner del cráter (R-1), pareo ±120 s misma resolución | `leer_osf` l. 652 a 672 (vent de `volcanoes.yaml`, haversine), `p1_osf` l. 689 a 691 | SÍ |
| §4.2 | lejana OSF (class 1, ≥ 1 MW, fuera del radio) informa E_lejana; ambiguas (class 0 dentro) listadas | l. 692 a 696, 737 | SÍ |
| §4.2 | bajo 1 MW OSF informa (SN por analogía en 375) | no se calcula | FALTA (VPR940-13, informa) |
| §4.3 | razón de R25 sólo cota, no decide | `razon_cota_mediana` l. 730 a 733; no entra a ninguna fila | SÍ |
| §5 | «publica» y magnitud = predicado de `frontend/index.html` con node (A97) | `F4.predicado_node` → `bp.correr_node` (`banco_paridad.py:71, 143`), `tabla_publica` l. 316 a 337; prueba con el predicado real (`test_el_predicado_real_...`, corre, no se saltó) | SÍ |
| §5.1 MODIS | §7 de MOD-D fase 4 (P1, P1b, P2, P2', M) sobre VIA-radiante, tramo F26-M | `regla_modis` l. 382 a 400 con `F4.p1/p1b/p2/m/veredicto` (copia del tag); brazo `V` l. 904; `TRAMO_DECIDE` l. 102; marzo sólo control (`control_f26_m3` l. 944 a 945) | SÍ |
| §5.1 VIIRS 375 | §5.4 (a) a (d) de V375-E con N-3 y el código del §9.7 (`criterios_retro`), cercano decide, radiante al lado con la misma regla; si difieren, fila 4 | `regla_v375` l. 422 a 452 (`LP.criterios_retro`, `E.lecturas`, `E.p2`, `LP.p2_con`, `LP.magnitud`); brazo `V-cercano` l. 904; radiante l. 938 a 940 → `cercano_y_radiante_difieren` → fila 4 | SÍ (fila 3 extendida por L1: VPR940-07) |
| §5.1 VIIRS 375 | (d) informa; SIN SUSTRATO si < 8 noches | `curva_cenit` l. 752 (`CC.veredicto` tiene `n_min=8`) | SÍ |
| §5.1 VIIRS 750 | §6 punto 2 de V750-A (texto `aa5583646`), sólo decide si sellado; si no, techo fila 4 (R-12); radiante por defecto (R-3) | `regla_v750` l. 455 a 476; `--v750a-sellado` obligatorio l. 983; `--posicion-v750` l. 984 | SÍ en estructura; M con «separa» dentro (VPR940-01) |
| §5.1 VIIRS 750 | diff de §6, §6 bis, §6 ter contra `aa5583646` si se sella en otro commit | no hay mecanismo (el texto de V750-A no se carga) | FALTA (manual) |
| §5.1 | M de V750-A banda [0,9; 1,1] en todas las protegidas que P publica, publique K o no | `F4.razon_protegidas` (`evaluar_f4.py:308-314`: «publique K o no») | SÍ |
| §5.2 | P1-OSF: vía no y K sí → candidata (fila 4); ni uno ni otro → lista; vía sí y K no → defecto del lector | `p1_osf` l. 713 a 727; `extra["candidatas_osf"]`, `extra["defecto_lector_osf"]` l. 931 a 932 → fila 4 | SÍ (defecto va a fila 4, no a INDECIDIBLE: VPR940-10) |
| §5.2 | recall de la vía por sensor, por volcán y sin Láscar | `por_volcan` cuenta protegidas, no recall; `pub_via` total | PARCIAL (VPR940-13) |
| §5.3 | razón por pasada, mediana con IC bootstrap de noches, por tramo de 10°, por volcán; F26-V por satélite | `curva_cenit` l. 757 a 762: mediana y n por tramo de 10°; sin IC, sin volcán, sin satélite | PARCIAL (VPR940-12) |
| §5.3 | Spearman con 200 barajados, semilla 172 | l. 765 a 771 (`SEMILLA=172`, `N_BARAJADOS=200`), p95 del nulo | SÍ |
| §5.3 | razón doble dentro de la noche, seis nombres de V375-E §5.3; CAE MÁS → fila 4 | `CC.resumen/veredicto` (copia sellada, `curva_cenit.py:137-175`); `curva_cae_mas_que_mirova` l. 928 a 929 → fila 4 sólo con controles de cenit OK | SÍ |
| §5.3 | corte de 30° (encargo S173) sólo informa | `CORTE_CENIT_INFORMA` l. 115, 763 a 764; no entra a ninguna fila | SÍ (L5, no la fija el pre-registro; inocuo) |
| §5.4 | lectura B por volcán: recall protegidas con lista, bajo 1 MW, negativos con Wilson, razón; una fila por volcán | `lectura_b` l. 813 a 833 (wilson de `evaluar.py`) | SÍ |
| §5.5 | noche protegida / noche limpia (todas las pasadas con fila) | `noche_operador` l. 836 a 857 (exige `len(ev) == len(fs)`) | SÍ |
| §5.6 | censo con pesos 1 | `filas_v375e` l. 415 (`"w": 1.0`) | SÍ |
| §5.6 | C-via R25: record sin marca sale de los dos brazos a SIN DATO; > 10 % por clase cae | `_evaluable` l. 321 (sale de todos los brazos); `c_via(..., "R25")` l. 495 a 499 por `lab_osf` | SÍ (clases: VPR940-17) |
| §5.6 | SIN SUSTRATO de P2 en 375 → fila 5 aunque §9.7 lo mapee a CUMPLE | l. 446 a 447; mutación M4 atrapada | SÍ |
| §5.6 | 750: SIN SUSTRATO → fila 5, BLOQUEA → fila 4 (D-45 `regla_signos_p2`) | l. 465 a 470; `F4.p2` usa `D.regla_signos_p2` (`evaluar_d25.py:552`, `MAX_B_SIN_SUSTRATO_P2 = 4`) | SÍ |
| §6 C-via | F26 y DM 100 % con marca; R25 10 % por clase | `c_via` l. 488 a 502; `c_via_dm` l. 909 a 911 (sólo si hay DM: VPR940-16); runner: `controles_via.py` + workflow l. 129 a 134 | SÍ |
| §6 C-cobertura | VIA contra K por volcán, día y sensor antes de leer; SIN DATO en los dos brazos; protegida SIN DATO que K publica → fila 2 en F26, fila 4 en R25; > 10 % por clase que decide cae; alertas de la tabla sin pasada nuestra listadas; trozo que falla dos veces → SIN DATO en la primera línea | `armar_pasadas` l. 231 a 240; `c_cobertura` l. 505 a 522; `protegidas_sin_dato_que_k_publica` → fila 2 (l. 875); `p1_osf` candidatas l. 714 a 716; `alertas_sin_pasada` l. 281; `--sin-dato-trozos` l. 988, 1001 (primera línea) | SÍ en F26; en R25 falta el 10 % por clase (VPR940-09) |
| §6 C-K | misma publicación y `pc.vrp_mw` a 0,001 MW; a lo más 3 excepciones por sensor con empate de argsort | `c_k` l. 525 a 544 (`TOL_VRP_CK=1e-3`, `TOPE_EXCEPCIONES_CK=3`, exige `empate_argsort`) | SÍ (sin control de cobertura del K-gemelo: VPR940-03) |
| §6 C-montaje | DM contra los A/B; explicada sólo por hunk o `otro_granulo` | JSON externo sin validar, l. 1022 | FALTA (VPR940-06) |
| §6 C-pareo | ±120 s y ninguna protegida OSF pareada a dos pasadas | l. 691 (`VENTANA_S=120`), `dobles` l. 706 a 707, `c_pareo` l. 734 | SÍ |
| §6 C-cenit | \|cenit − SatZen\| ≤ 2° en R25 | l. 698 a 699, 735 (`TOL_CENIT_OSF=2.0`) | SÍ |
| §6 PLACEBO | P1 y P2 sin discordancias salvo filtros del tablero; M de D-28 no da MEJORA (MODIS, 375); en 750 el comparador separa | `c_placebo` l. 563 a 569: sólo M de D-28 (`dprima_da_mejora`); P1 se calcula y no decide; P2 no se calcula; «separa» está en `regla_v750` | PARCIAL (VPR940-01, 05) |
| §6 Nulo de runner | B = 0 salvo nombradas; control contra PLACEBO con B > 0 o M distinta | `nulo_runner` l. 547 a 560 | PARCIAL (no excluye las nombradas: VPR940-04) |
| §6 Nulo del lector | K contra K 0 diferencias; protegida quitada → veto; 50 negativos inyectados suben P2 en 50 | `nulo_lector` l. 572 a 615 (`N_INYECTADOS=50`, `inyectar_cumulo` l. 303) | SÍ |
| §6 Controles de cenit | pares < 5° con razón doble que contiene 1; ganancia pareja no mueve; creciente sube | `controles_cenit` l. 788 a 810 | SÍ |
| §6 Candado | sha256 LF de lector, referencias e index.html contra el manifiesto, antes de correr | `candado` l. 625 a 631 (LF: `sha256_lf` quita `\r`); manifiesto externo inexistente | PARCIAL (falta el manifiesto) |
| §6 | C-via y C-cobertura impresos por trozo en el runner y otra vez en la lectura | `controles_via.py`, workflow l. 129 a 134; lector `c_via`, `c_cobertura` | SÍ |
| §7 | sorteo de etiquetas K contra K por estrato (fracción de barajados GANA o EMPATE por azar) | no está (`grep baraj` sólo en Spearman) | FALTA (VPR940-11) |
| §8.1 | filas 1 a 6 en ese orden; fila 4 antes que la 5 | `veredicto` l. 868 a 887; mutación M1 atrapada | SÍ |
| §8.1 fila 6 | nombre con alcance (alertas, silencio, satélites) | `nombre_fila6` l. 890 a 895 | SÍ |
| §10.1 | `extends` un nivel: los seis flags escritos; prueba con padre mutado roja antes y verde después; control negativo | perfiles l. 20 a 26; `test_los_seis_flags_no_siguen_al_padre`, `test_control_negativo_...` (`_load_profile` real sobre un directorio temporal) | SÍ |
| §10.1 | ninguno marca régimen en el lector de V375-E (batería antes del merge) | no hay prueba en el PR | SIN VERIFICAR |
| §10.2 | pyproj instalado y comprobado; sólo `EARTHDATA_TOKEN` con corte; sin merge; artifacts 30 días; `"on":`; ubuntu-24.04; grupo propio; `controles_via.py` por trozo; trozos 20 y 10; rehúsa perfiles ajenos | workflow l. 22, 43 a 48, 52, 74, 86 a 94, 98 a 108, 129 a 134, 144 a 161; `plan_trozos.py:86-87, 109`; pruebas `test_retro_paquete_workflow_s172.py:43-104` | SÍ |
| §10.2 | flags leídos de `pipeline.profile` en el runner | workflow l. 109 (`VRP_PROFILE=... python -c "import pipeline.profile as p; assert ..."`), probada con los cuatro perfiles (l. 99 a 104 del test) | SÍ |
| §10.3 | D1 3, D2 47, D3 30, D4 176 jobs; `max-parallel 6`; tope 256 | reproducido por mí con `plan_trozos.py` (3, 47, 30, 176); workflow l. 77; `MAX_JOBS=256` | SÍ |
| §10.3 | despachos de a uno | grupo de concurrencia por perfil: D2 y D3 pueden solaparse | PARCIAL (VPR940-14) |
| §11 | manifiesto; TDD rojo antes de verde; batería por fila del §8.1 y regla del §5.6; mutaciones por aserción con control de caída; verificador limpio | mutaciones: `mutar_leer_retro.py` (ver §3); TDD estricto: el PR declara que no; batería: las filas 2 a 6 y los controles tienen prueba (`test_leer_retro_s172.py`); manifiesto: no | PARCIAL (declarado por el autor) |
| R-3, R-12, R-13, R-15 | radiante en 750 por defecto; D2 sin sello con techo fila 4; cercano y radiante distintos → fila 4; tope 3 | l. 984, 467 a 468, 940, 112 | SÍ |

## 2. Respuestas a los seis puntos del encargo

**1. `_s172_retro_k.yaml`.** Sí lo manda el pre-registro, en cuatro lugares: §2 (fila K-gemelo: «el código del tag
con el perfil `_s172_retro_k` (vías apagadas)»), §6 (C-K y nulo de runner), §10.1 («`_s172_retro_k.yaml`: lo mismo
con las tres vías en `false`. Carpeta `_s172_retro_k`») y §10.3 (despacho D3). Es correcto: los seis flags escritos
en `thresholds:` (l. 20 a 26), carpeta propia (`data_subdir: _s172_retro_k`), y la prueba de identidad muestra que
resuelto por `pipeline.profile` difiere de `_s172_retro_paquete` exactamente en las tres constantes de las vías
(`test_retro_k_es_retro_con_las_tres_vias_apagadas`, pasa). Sí es «el K que escribió K de disco» en cuanto a flags:
K de disco de F26, DM y R25 fue escrito el 2026-10-18 a 10-21 (`processed_utc`, `scan_k_disco_salida.txt`), antes
de que producción encendiera la vía de MODIS (`33f889bc5`, 2026-11-02). Las demás diferencias de código entre #883 y
el tag del despacho son justo lo que C-K mide.

**2. Decisiones de lectura del autor.**

| decisión | el pre-registro | mi lectura |
|---|---|---|
| L1: en VIIRS 375, P2-L PIERDE y silencio ENCIENDE DE MÁS van a la fila 3 (PEOR QUE K) | fila 3 dice «no cumple por P2 PIERDE»; fila 4 nombra BLOQUEA y «DECIDE NICOLÁS». V375-E §5.4 (b) sellado agrupa en un solo criterio «P2 GANA o EMPATE (no PIERDE ni BLOQUEA) y el silencio no da ENCIENDE DE MAS», y su §9.7 (`criterios_retro`, copia del tag l. 505 a 515) da NO CUMPLE por P2-L PIERDE o BLOQUEA y por el silencio | **ABIERTA**. Defendible (el criterio (b) es el de P2), pero el propio L1 dice «lo no previsto pasa a Nicolás» y aquí eligió la fila más dura; BLOQUEA de P2-L sí va a la 4. La decide Nicolás (VPR940-07) |
| L2: caja de VIIRS 750 obligatoria por parámetro; cada record debe traer esa `roi` | no fija la caja (sale de V750-B); C-montaje incluye el brazo «con la ROI elegida» | no la contradice; es instrumentación sana. El campo existe (`pipeline/mirova_v750_codigo.py:705-708`) |
| L3: C-montaje como JSON externo, rojo sin él | §6 lo define como control obligatorio con criterio de «explicada» (hunk u `otro_granulo`) | el pre-registro lo fija; el PR lo difiere. Falta construirlo y validarlo (VPR940-06) |
| L4: N-3 en 375 y 750, no en MODIS | §5.1 lo fija: V375-E §8.13 para 375 y V750-A §6 ter para 750 (texto no sellado, aplicado como anexo); MOD-D no lo tiene | **la fija**; coincide. `es_n3` l. 352 (`"SNPP" in sensor`, antes del 2026-10-09, protegida sólo en la unión) |
| L5: corte de 30° informa | no está en el pre-registro (encargo de S173) | no la fija; inocuo mientras no decida (no decide: l. 763 a 764) |
| «el comparador separa» en VIIRS 750 = `mejora_d28(vía) and not mejora_d28(placebo)`, dentro de M | §6 PLACEBO: «en VIIRS 750, el comparador de V750-A §6.2 separa la vía de K × 1,2» es un **control** (si falla, «instrumento roto»). V750-A `aa5583646` l. 152 a 155 y 233: «M sólo dice «P mide mejor» si separa a P de K y de K×1,2»; no define «separar» en código | **ABIERTA en su definición y CONTRADICHA en su lugar**: el PR lo pone en M (fila 3 si falla), el pre-registro lo pone en PLACEBO (fila 1). Qué significa «separar» lo decide Nicolás con V750-A (VPR940-01) |

**3. Flags desde `pipeline.profile`.** Sí: la prueba vuelca `vars(pipeline.profile)` en un subproceso con
`VRP_PROFILE` (`test_perfil_retro_paquete_s172.py:37-47`), la herencia se prueba con `_load_profile` real sobre un
directorio temporal (l. 81 a 100), y el workflow comprueba en el runner `p.PROFILE_NAME`, `p.DATA_SUBDIR`, las tres
constantes de las vías y las tres de MxD03 antes de correr (l. 109); esa línea se ejecuta en la prueba con los cuatro
perfiles (`test_la_linea_de_asserts_del_paso_acepta_solo_los_perfiles_de_la_retro`). Lo único que lee el YAML a ojo es
`plan_trozos.py:93` (`data_subdir`) y `test_los_seis_flags_estan_escritos_en_thresholds_del_yaml_propio`, los dos
como guarda adicional, no como fuente.

**4. sha256 LF de las copias.** Coinciden con sus tags, por sha256 LF y por blob:
- `reglas/evaluar_f4.py`: disco `8a1edc14…c30c` = `s170-modd-f4-candado:experiments/_s166_modd_f4/evaluar_f4.py`
  (`tr -d '\r' | sha256sum` sobre `git show`), blob `d78139e6` en los dos.
- `reglas/leer_posicion_v375e.py`: disco `a40364ab…ce06` = `s170-v375e-lector:experiments/_s162_v375/e_adenda2/leer_posicion_v375e.py`,
  blob `4100cfc1` en los dos.
- Los otros cuatro del `MANIFIESTO_REGLAS` (`evaluar.py` `2126b743…`, `curva_cenit.py` `7fdd8e40…`,
  `evaluar_d25.py` `2e557697…` = blob `1dbabf65`, `evaluador_comun.py` `c151b29f…`) coinciden con el disco y con
  el tag `s170-v375e-lector` (`git diff` vacío). Los archivos en disco están en CRLF (`core.autocrlf = true`); el
  lector quita `\r` antes de hashear (l. 139 a 140), así que el candado interno no depende del checkout.
  `test_las_copias_de_las_reglas_son_los_blobs_de_sus_tags` lo vigila.

**5. Mutaciones.** Ver §3 (corrida por mí).

**6. Lo que falta.** Ver «Lo que falta para poder LEER» arriba. Rehúsa el veredicto sin C-montaje (rojo → fila 1),
sin K-gemelo (rojo), sin caja de 750 (rojo en 750), y sin manifiesto exige `--ensayo` (que no bloquea: VPR940-15). Las
excepciones de C-K son opcionales por diseño correcto.

## 3. Mutaciones, corridas por mí

Comando: `python experiments/_s172_retro_paquete/mutar_leer_retro.py` en el worktree, salida en
`C:/Users/nmend/vrp-wt/ver940_informe/mutar_salida_verificador.txt`.

Resultado, reproducido por mí sobre la punta `6e93764bf` (árbol quieto, `git status` limpio al terminar, copia
`_mut_*` borrada): **12 de 12 mutaciones reales ATRAPADAS por aserción; el control de caída (NameError en
`regla_modis`) sale CAE** (`resumen: {'ATRAPADA': 12, 'CAE': 1}`). Coincide con `mutar_leer_retro_salida.txt` del PR
(ronda 1 con M9 SOBREVIVE y ronda 2 con la prueba agregada; en mi corrida M9 es ATRAPADA por
`test_v750_sin_sello_la_regla_misma_pone_el_techo`). Las doce atrapan por aserción y no por caída: ninguna aparece con
mensaje de excepción. Lo que las mutaciones NO cubren, y es donde están mis hallazgos de gravedad 3: no hay mutación
sobre la pureza de K (VPR940-02), sobre la cobertura del K-gemelo (VPR940-03), sobre el lugar de «separa» (VPR940-01)
ni sobre el contenido de C-montaje (VPR940-06); una batería que no ejerce un control no puede atraparlo.

Sobre el instrumento de mutación (`mutar_leer_retro.py`): clasifica ATRAPADA sólo si alguna prueba falla con mensaje
que empieza por `AssertionError` o `assert` (l. 87); CAE si hay fallas de otro tipo; el control de caída es un
`NameError` deliberado (l. 66 a 67). Cada mutación es una copia aparte (`_mut_leer_retro_<pid>.py`) y el original no
se edita (A112). Una mutación en que algunas pruebas fallan por aserción y otras caen cuenta como ATRAPADA: es
aceptable, porque al menos una aserción la vio.

## 4. Caminos por los que el instrumento daría un veredicto equivocado sin fallar

| camino | comprobado | resultado |
|---|---|---|
| control que no puede fallar | C-K con un K-gemelo de una pasada da OK (l. 528 a 544); C-montaje acepta cualquier `{"estado":"OK"}`; PLACEBO no mira P1 ni P2 | VPR940-03, 06, 05 |
| régimen mal acotado | C-via del runner exige records en los tres sensores por trozo (exit 4 si uno está vacío) y el trozo no se sube si el paso falla: en jobs de 1 día (D1) o de 3 días sueltos (D3) un sensor sin record legítimo deja el job rojo | VPR940-08 |
| archivo leído de otra parte que la sellada | las seis reglas se cargan por ruta con sha256 LF previo (l. 155 a 166; comentario l. 162 a 163 sobre el `evaluar.py` equivocado que entraba antes); `index.html` se lee del disco del checkout (`banco_paridad.py:71`): depende del manifiesto externo | OK con manifiesto; sin él, SIN CANDADO |
| perfil que hereda por `extends` de un nivel | seis flags escritos; prueba con padre mutado y control negativo | OK |
| workflow que vuelve a K en silencio sin pyproj | `pip install ... pyproj` l. 92 y `Comprobar pyproj` l. 93 a 94 antes de procesar; C-via por trozo l. 129 a 134 (100 % en 2026) | OK |
| credenciales distintas de `EARTHDATA_TOKEN` | sólo el token, corte si viene vacío (l. 98, 105 a 108); el texto no nombra USERNAME/PASSWORD (prueba) | OK |
| carrera de escritura sobre `data/` | sin push, sin job merge, `permissions: contents: read`; cada job escribe su propio checkout y sube artifact (l. 153 a 161); la unión «en local en un solo proceso» (A47) no tiene script | OK en el runner; VPR940-18 en la unión |
| empates (`argsort` entre CPU, S152) | C-K exige el empate escrito por excepción, tope 3 por sensor; nulo de runner no las descuenta | VPR940-04 |
| CRLF en sha256 | `sha256_lf` quita `\r` (l. 139 a 140); `evaluar_f4.blob` normaliza CRLF (l. 56); archivos en CRLF en disco y hashes iguales a los tags | OK |
| K de disco que no es K | ningún control mira `via_codigo_mirova` en `k_rec`; producción tiene la vía de MODIS encendida desde el 2026-11-02 y R25 no está en C-K | VPR940-02 |
| etiqueta decide la unión en vez de la tabla | canal `tabla` = `source == "CONS"`; mutación M7 atrapada | OK |
| pareo vía contra K | por clave exacta (volcán, sensor, `datetime_utc`) (l. 188); la vía y K salen del mismo gránulo y del mismo `store`, así que la clave coincide; una pasada de la vía sin K queda `sobra_en_via` y se lista, no decide | OK (conservador) |
| D2 y D3 a la vez | grupo de concurrencia por perfil (l. 47): dos despachos de perfiles distintos corren juntos (12 jobs) | VPR940-14 |

## 5. Hallazgos

Gravedad: 4 invalida la prueba; 3 veredicto equivocado posible sin error; 2 control más débil que lo sellado o lectura
abierta; 1 informa o cosmético.

**VPR940-01 (3). VIIRS 750: «el comparador separa» vive dentro de M y no en el control PLACEBO, y su definición es
propia.** `leer_retro.py:459-468`: `separa = _mejora_d28(m_v) and not _mejora_d28(m_pl)`; `m_ok = banda and separa`;
con V750-A sellado, `not m_ok` → fila 3 (NO SE SOSTIENE: PEOR QUE K). El pre-registro §6 (fila PLACEBO) pone «en VIIRS
750, el comparador de V750-A §6.2 separa la vía de K × 1,2» como control: si falla, «instrumento roto» → fila 1. Y
V750-A `aa5583646` l. 152 a 155 y 233 dice «separa a P de K y de K×1,2» sin definirlo en código. Efecto: una vía en
banda [0,9; 1,1] cuyo d′ no dé MEJORA (NEUTRO, por ejemplo) saldría «peor que K» y «no avanza hacia producción» (§8.2)
cuando el texto sellado diría «instrumento roto» o nada. Hoy el camino sólo se activa con `--v750a-sellado si`
(R-12: sin sello, fila 4 de todos modos). Arreglo: en `regla_v750`, `m_ok = banda`; mover «separa» a `c_placebo`
para el sensor 750 (ROJO si no separa), y que Nicolás fije qué es «separar» antes de que V750-A se selle.

**VPR940-02 (3). K de disco sin control de pureza.** No hay ninguna línea que compruebe que los records de `--k`
no traigan `via_codigo_mirova` True (`grep` vacío). Hoy están limpios: 0 marcas en 50.467 records de F26, DM y R25 de
`origin/main` `8deb8bbea` (`scan_k_disco.py`, salida en `scan_k_disco_salida.txt`), todos con `processed_utc`
2026-10-18 a 10-21. Pero producción enciende la vía de MODIS desde `33f889bc5` (2026-11-02): cualquier reproceso de
histórico entre hoy y D4 escribiría records de la vía en `data/mirova_equivalent/`, el lector los tomaría como K, y en
R25 (sin C-K) mediría la vía contra la vía sin error. Arreglo: en `armar_pasadas`, estado `k_con_marca:<valor>` si
`rk.get("via_codigo_mirova") is True`, y un control `c_k_puro` rojo con una sola. Cinco líneas.

**VPR940-03 (2). C-K no comprueba la cobertura del K-gemelo.** `c_k` l. 528 compara sólo las pasadas que el
K-gemelo trae. Con un `--kgemelo` de una pasada da OK. El §6 exige DM entero, Láscar y Chillán en F26 enteros y tres
días de cada otro volcán (D3). Arreglo: contar pasadas de K-gemelo contra K por volcán y tramo sobre las ventanas de
D3 (reusar `plan_trozos`) y poner ROJO si falta alguna ventana.

**VPR940-04 (2). El nulo de runner no descuenta las excepciones nombradas.** `nulo_runner` l. 547 a 560 exige
`B == 0` sobre todas las pasadas; el §6 dice «B = 0 en P2 salvo las pasadas nombradas de C-K», y el docstring de la
función dice lo mismo que el texto, pero el código no las excluye. Con una excepción legítima (empate escrito, dentro
del tope) el nulo queda ROJO y los tres sensores INDECIDIBLES. Conservador, pero contradice la regla y obliga a
«arreglar y repetir». Arreglo: quitar de `con` las pasadas nombradas antes de calcular `p`.

**VPR940-05 (2). PLACEBO sólo mira M.** `c_placebo` l. 563 a 569 decide por `mejora_d28` del placebo; calcula
`p1_placebo` y no lo usa; no calcula P2 de PLACEBO contra K. El §6 pide «P1 y P2 sin discordancias salvo las que
explican los filtros del tablero que miran la magnitud (nota L7 de V750-A §7)». Un predicado del tablero que
publicara distinto con K × 1,2 (`t_max` bajo 278,15 K, tope de 50.000 MW) pasaría sin verse. Arreglo: listar las
discordancias de publicación K contra placebo y ponerlas en ROJO salvo las dos causas de L7.

**VPR940-06 (2). C-montaje no construido y no validado.** `leer_retro.py:1022` carga `--montaje` y lo pasa tal cual a
`veredicto()`; l. 872 sólo mira `estado.startswith("OK")`. No se exige la lista de diferencias ni el criterio del
§6 (hunk que la reproduce u `otro_granulo`). Lo declara el PR. Arreglo mínimo: exigir claves (`diferencias`,
`explicadas_por`, cada una con `hunk` u `otro_granulo`, `tags`, `diff_listado`) y ROJO si hay una sin explicación.

**VPR940-07 (2). L1 extiende la fila 3.** `leer_retro.py:442-443`: `p2lv == "PIERDE" or sil == "ENCIENDE DE MAS"`
→ fila 3. Ver la tabla del punto 2. ABIERTA: Nicolás decide si P2-L PIERDE y ENCIENDE DE MÁS son «PEOR QUE K» (fila
3, la vía no avanza) o van a la fila 4 con la lista. Recomendación: fila 3 es coherente con V375-E §5.4 (b), pero
escribirlo como marca A113 fechada en el pre-registro, como pide la cabecera del lector (l. 5 a 6).

**VPR940-08 (2). C-via del runner deja rojo un trozo con un sensor vacío y el trozo no se sube.**
`controles_via.py:68-73` devuelve 4 si un sensor tiene 0 records, salvo `--permitir-sensor-vacio`, que el workflow no
pasa (l. 133 a 134); «Guardar el trozo» (l. 153 a 160) no tiene `if`, así que no corre si el paso de C-via falló. En
D1 (tres jobs de un día) y en D3 (nueve jobs de tres días sueltos) basta que la vía descarte sin record las pasadas
de un sensor ese día (regla de cobertura, `mirova_v750_codigo.py` l. 798 a 808, citada en §6 C-cobertura) para que el
job salga rojo con datos válidos y el JSON no quede como artifact. El log sí se sube. Arreglo: `--permitir-sensor-vacio`
cuando `dias <= 3` (el plan ya sabe `dias`), o que el sensor vacío sea aviso y lo decida C-cobertura en la lectura.

**VPR940-09 (2). En R25 no se aplica el 10 % SIN DATO por clase de C-cobertura.** `c_cobertura` (l. 505 a 522) se
calcula sólo sobre `filas` del tramo que decide (l. 903, 908). En R25 una protegida SIN DATO que K publica sí va a
candidata (l. 714 a 716), pero «más de 10 % SIN DATO en una clase» no se mide; `c_via_r25` sí lo hace para la marca.
Arreglo: `c_cobertura` sobre las filas de R25 con `lab_osf` como clase.

**VPR940-10 (2). «Defecto del lector» va a DECIDE NICOLÁS.** `extra["defecto_lector_osf"]` (l. 932) entra a
`motivos4` (l. 882) → fila 4. El §5.2 dice que «la vía sí y K no» «no puede ocurrir» y «si ocurre es un defecto del
lector»: eso es un control (fila 1), no una decisión de Nicolás. Arreglo: moverlo a `ctl`.

**VPR940-11 (2). Falta el sorteo de etiquetas K contra K por estrato (§7, último párrafo).** Ningún código lo hace
(`grep baraj` sólo da el Spearman). Informa, pero el §7 lo pide «antes de leer».

**VPR940-12 (1). Curva de cenit sin IC, sin volcán y sin satélite.** §5.3 punto 1 pide mediana con IC bootstrap de
noches, por tramo de 10° y por volcán, y en F26-V por satélite. `curva_cenit` l. 757 a 785 da mediana y n por tramo y
por el corte de 30°; `CC.mediana_ic` existe y no se usa. Informa.

**VPR940-13 (1). R25 no informa bajo 1 MW OSF ni recall por volcán sin Láscar.** `p1_osf` cuenta protegidas por
volcán (l. 704) y `pub_via` total; §4.2 y §5.2 piden más. Informa.

**VPR940-14 (1). Concurrencia por perfil permite D2 y D3 a la vez.** Workflow l. 46 a 48. §10.3 dice «de a uno»; con
NRT 8 + 12 se pasa el tope de 20 si el plan es Free (SIN DATO). Operativo: basta no despachar D3 hasta que D2 termine,
o un grupo único.

**VPR940-15 (1). ENSAYO no se ve en la salida por sensor.** `main` imprime `{sensor}: fila N | veredicto` (l. 1033)
igual con `--ensayo`; sólo el JSON (`ensayo: true`) y el estado del candado lo dicen. La cabecera promete «la salida
dice ENSAYO y no decide». Arreglo: prefijo `ENSAYO (NO DECIDE)` en cada línea.

**VPR940-16 (1). C-via de DM sólo si hay filas de DM.** l. 909 a 911: sin DM no hay control ni aviso. Hoy lo cubre
C-montaje (rojo sin JSON). Arreglo: ROJO «sin DM» si `dm` está vacío.

**VPR940-17 (1). Clases de C-via en R25.** l. 496 a 497 usan `protegida_osf` contra `sin_osf` (todo lo demás). No
afloja el control (todo lo no protegido es una sola clase con el mismo 10 %); sólo no distingue bajo 1 MW ni lejana.

**VPR940-18 (1). No hay unión de artifacts ni exportación de K.** Ver «Lo que falta», punto 6. El lector une por la
clave `volcano` de cada JSON y detecta repetidas (l. 189 a 191, 518), pero no comprueba que todos los JSON de `--via`
vengan del perfil `_s172_retro_paquete` ni que `--k` sea el `git archive` del tag. Arreglo: un script `unir_trozos.py`
que lea los artifacts, verifique `profile`/`data_subdir` del JSON si el `store` lo escribe, y escriba la carpeta; y
anotar en el manifiesto el commit de K.

## 6. Lo que NO encontré (y comprobé)

- Los perfiles no filtran a los 34 ni cambian umbrales: idénticos a la sombra salvo nombre y carpeta (prueba).
- El workflow no puede pisar `data/` de main (sin push, permisos de lectura).
- Las copias de las reglas son las de los tags, byte a byte.
- Las 21 pasadas de §3.1 (b) están en `PASADAS_B` con horas que coinciden con sus fuentes.
- Los conteos de jobs del §10.3 se reproducen.
- `extends` de un nivel está cubierto por los seis flags y la prueba con padre mutado.
- C-cobertura en F26 lleva una protegida SIN DATO que K publica a la fila 2 (prueba `test_protegida_sin_dato_que_k_publica_es_fila_2`).
- El nulo del lector tiene control de que puede fallar (`test_nulo_del_lector_cae_si_el_predicado_no_publica_lo_inyectado`).

## 7. Decisiones que son de Nicolás, no del instrumento

1. L1 (VPR940-07): si P2-L PIERDE y ENCIENDE DE MÁS en VIIRS 375 son «PEOR QUE K» (fila 3) o «DECIDE NICOLÁS» (fila 4).
2. Qué significa «el comparador separa a P de K × 1,2» en VIIRS 750 (VPR940-01), y que sea control y no parte de M,
   como dice el §6; vale sólo cuando V750-A se selle (R-12).
3. Si «defecto del lector» en P1-OSF es fila 1 o fila 4 (VPR940-10; el texto dice defecto del lector).
4. Los tres puntos del encargo ya resueltos por el PR no son de Nicolás: el perfil K lo manda el pre-registro; N-3 lo
   fija §5.1; el corte de 30° sólo informa.

## 8. SIN VERIFICAR / SIN EVIDENCIA

- §10.1 último punto (ningún perfil marca régimen en el lector de V375-E): sin prueba en el PR; SIN VERIFICAR.
- Que la vía de 375 escriba `anomaly_pixels[].dist_km` y `hotspot_dist_km` en todos los records (lo que necesita
  `distancias_desde_record` para el brazo cercano): no lo medí sobre datos; si falta, `_variante` devuelve el record
  radiante sin aviso (l. 299 a 300). SIN VERIFICAR; conviene un contador «cercano no calculable» en C-via.
- El comportamiento real del runner (tiempos, cortes de NASA): no se despachó nada.
- El check `pytest` del PR en GitHub: `pending` al cerrar.

## Esfuerzo declarado

Trabajé con esfuerzo alto: leí el pre-registro entero (749 líneas) y el lector entero (1.043), los perfiles, el
workflow, el plan, los controles, el script de mutaciones y los tres archivos de pruebas; leí las funciones de las
reglas selladas que el lector llama (`evaluar_f4.py`, `leer_posicion_v375e.py`, `evaluar.py`, `evaluar_d25.py`,
`banco_paridad.py`, `referencia_mirova_unificada.py`) y el texto de V750-A y V375-E en sus commits; corrí la suite
del PR, el plan de trozos para los cuatro despachos, el barrido de K de disco en `origin/main` y las mutaciones.
No usé subagentes.
