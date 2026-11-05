# Verificación limpia del PR #946 (seguimiento de #940)

Verificador sin contexto del autor. Worktree: `D:/vrp-trabajo/wt/ver946` en `7df31d9f1` (punta del PR, borrador, base `main`).
Sólo lectura sobre el repo; nada de push, comentarios ni despachos. Temporales en `D:/vrp-trabajo/temporales/s173-ver946/`.

## Veredicto: MERGEABLE CON CAMBIOS

No hay gravedad 3. Los cuatro hallazgos que el PR dice arreglar con código (VPR940-01, 10; VPR940b-02, 07) están arreglados y las mutaciones del PR
caen por aserción en la muestra que repetí. Lo que no cierra: (a) dos controles que el PR dice añadir o que ya existían no están cableados o no tienen
aserción (VPR946-01, 02, 03) y (b) tres hallazgos del segundo verificador quedan en parte (b-01, b-03, b-06). Ninguno hace que el lector dé OK donde
hoy da rojo; sí hay un caso (C-cenit) donde el instrumento da fila 6 donde el pre-registro manda fila 1, preexistente de #940.

## Lo que corrí
- Suite relevante en el árbol quieto: `tests/test_leer_retro_s172.py`, `test_retro_seguimiento_s173.py`, `test_perfil_retro_paquete_s172.py`,
  `test_retro_paquete_workflow_s172.py`: **99 pasan en 410 s** (`pytest_pr.txt`). La suite completa del repo (3.217 que declara el PR): SIN VERIFICAR.
- Cobertura del diff: `leer_retro.py` (todos los hunks leídos: `git diff origin/main...HEAD`, 418 líneas), `armar_manifiesto.py`, `armar_montaje.py`, `mutar_leer_retro.py`
  (conteo de caídas), dos baterías. `git diff 108104480 7df31d9f1` sólo agrega la salida de mutaciones: el código medido por la ronda 4 es el de la punta.
- Pin del sello: sha256 LF del pre-registro en el tag `s173-prereg-retro-sellado` y en `origin/loop/activo` = `b58a2254…3c91` (igual al del PR).
- Sondas propias: `probe_cenit.py`, `probe_b03.py`, `probe_manifiesto.py`.
- Mutaciones propias (clasificadas con el mismo clasificador del PR; control positivo Gm2 del PR: ATRAPADA, el harness funciona):

| mut | qué rompe | resultado |
|---|---|---|
| G1 | `armar_manifiesto` no corta con exit 3 si el pre-registro cambió | SOBREVIVE |
| G2 | `armar_montaje` hace `git diff despacho despacho` | SOBREVIVE |
| G3 | el OSF no entra al manifiesto | SOBREVIVE |
| G4 | `armar_montaje` no exige un tag por origen | SOBREVIVE |
| X1 | `main` no exige --cons/--ocr/--osf en el manifiesto | SOBREVIVE |
| X2 | referencia fuera del repo no deja el candado en rojo | SOBREVIVE |
| X3 | `_excepcion_valida` no exige la hora al minuto | SOBREVIVE |
| X4 | el M de D-28 del placebo vuelve a aplicarse en 750 | ATRAPADA por aserción (`test_v750_separa_es_control_del_placebo_no_parte_de_m`) |
| X5 | `cobertura_kgemelo` ignora "sin K en DM" | SOBREVIVE |
| X6 | `validar_montaje` acepta tag vacío | SOBREVIVE |

Salidas: `mut_gen_salida.txt`, `mut_leer_salida.txt`. No repetí las 42 del PR (cada una corre la batería entera, 5 a 10 min); su cifra "42 de 42 por aserción" queda SIN VERIFICAR salvo la muestra (Gm2, X4 como vecino).

## Hallazgos previos: ¿arreglados?

| id previo | grav. | estado | dónde |
|---|---|---|---|
| VPR940-01 (separa dentro de M) | 3 | ARREGLADO | `m_ok` sólo mira la banda (`leer_retro.py:~494`); "separa" vive en `c_placebo` (l.676-710), sin valor por defecto; prueba y 3 mutaciones S01. Residuo: VPR946-06 |
| VPR940-02 (K de disco sin pureza) | 3 | ARREGLADO en #940 (`c_k_puro`, l.~267); #946 deja `is True` a Nicolás (b-04) | `armar_pasadas` l.261 |
| VPR940-07 (L1 fila 3) | 2 | ARREGLADO como decisión: sin cambio de código, prueba + 2 mutaciones; la aprobación no es verificable (VPR946-07) | `regla_v375` |
| VPR940-10 (defecto del lector a fila 1) | 2 | ARREGLADO | `c_defecto_lector_osf` (l.1172-1176), prueba y S10 |
| VPR940b-01 (sorteo sin poder) | 2 | EN PARTE | informa "SIN PODER", no cambia el §7 (VPR946-13) |
| VPR940b-02 | 1 | ARREGLADO | `c_k` usa `_nombradas` (l.~633) |
| VPR940b-03 | 1 | EN PARTE | faltan claves: rojo; `sensor` no string cae (VPR946-04) |
| VPR940b-04 (`is True`) | 1 | NO ARREGLADO, declarado | decide Nicolás |
| VPR940b-05 (cabecera) | 1 | ARREGLADO | cita `experiments/_s173_aud/ver940/INFORME.md` @ `6e3af852e` |
| VPR940b-06 (C-montaje) | 1 | EN PARTE | un tag por origen y DM sí; el resto sigue pendiente (VPR946-05) |
| VPR940b-07 | 1 | ARREGLADO | rojo por Tier A sin F26 en K y `sobras_kgemelo` (más estricto que lo pedido); X5 deja a la vista otro hueco vecino |
| VPR940b-08 | 1 | ARREGLADO | aviso "R25 sin OSF" en salida y JSON |
| VPR940b-10, 11 | 1 | ARREGLADO | docstrings |
| VPR940b-12 | 1 | ARREGLADO | `mutar_leer_retro.py` imprime caídas junto a ATRAPADA |
| VPR940b-09 | 1 | sin cambio (sellado) | correcto |
| VPR940-12, 13, 14, 16, 17, 18 | 1 | NO TOCADOS ni reclamados | siguen abiertos |

## Hallazgos nuevos (hallazgos.csv)
- VPR946-01 (2): C-cenit de R25 y controles de cenit no llegan al veredicto. Preexistente.
- VPR946-02 (2): el candado con las referencias de `main` no tiene aserción (X1, X2, G3).
- VPR946-03 (2): la compuerta exit 3 del generador del manifiesto no tiene aserción (G1).
- VPR946-13 (2): VPR940b-01 abierto, decisión de Nicolás.
- VPR946-04, 05, 06, 07, 08, 09, 10, 11, 12 (1): ver CSV.

## Qué pediría antes de leer F26 (no todo bloquea el merge)
Cablear C-cenit y controles de cenit; pruebas de `main --manifiesto` y de los cortes de `armar_manifiesto`; sumar `volcanoes.yaml` al manifiesto; que el candado en rojo corte la lectura; resolver b-01, b-04 y los tags de C-montaje con Nicolás.
