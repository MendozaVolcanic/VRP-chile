# Lectura de D25 sobre K (S162, 2026-10-24)

Leída el 2026-10-24 (servidor ~12:20 UTC) con el evaluador del tag **`s161-d25-lectura`** (`a7418e01d`), sin
cambiarlo: `evaluar_d25.py` sha256 `93c26d6262cee07c7bd2e78c295bed6c8e6d195193255fb529c4fbac5c04fec2`, igual al del
traspaso. numpy 2.4.4, Python 3.12.10 (D-47, `salidas/versiones.txt`). Calibración `--calibracion simetrica`.

## Veredicto combinado (el que decide): DECIDE NICOLÁS

Evaluado sin el 2026-10-13, 17, 18, 19 y 20 (D-29). Ningún criterio da NO CUMPLE y ninguno da CUMPLE:

| prueba | V1 (2026-08-29 a 10-18, tabla y OCR) | V2 (2026-04-01 a 06-12, tabla sola) |
|---|---|---|
| controles (cobertura, versión, cableado, determinismo, referencia) | OK (4.610 pasadas por brazo; K' = K en 2.271 y 2.253) | OK (6.769 pasadas por brazo) |
| P1 veto | CUMPLE en los dos sensores (24 y 22 protegidas, 0 perdidas) | CUMPLE (38 y 42, 0 perdidas) |
| P1b cruce de 1 MW | **2 en Chillán**: V375 2026-10-11 05:36 (K 1,225 → D 0,909; MIROVA 1,38) y V750 2026-10-14 06:18 (K 1,173 → D 0,632; MIROVA 2,0) | sin cruces |
| P2 VIIRS 375 | EMPATE (original y SN) | EMPATE (original); **BLOQUEA con SN** (neto +1, 11 noches, p 0,50) |
| P2 VIIRS 750 | **BLOQUEA** (neto +6, 26 noches, p PIERDE 0,16) | EMPATE (neto −2, 43 noches) |
| M V750 cenit ≤ 40° | **MEJORA** (d −0,132 [−0,348; −0,036]; d′ −0,099 [−0,240; −0,007]; 3 de 3 volcanes) | NEUTRO: d mejora, d′ no («sube en promedio, no en los pares correctos») |
| M V750 cenit > 40° | NEUTRO (MEJORA de un solo volcán, Chillán; d′ neutro) | NEUTRO (un solo volcán, Láscar; d′ neutro) |
| M V375 sin kernel ≤ 40° | NEUTRO (d mejora, d′ no) | NEUTRO (d mejora, d′ no) |
| M V375 sin kernel > 40° (sólo bloquea) | NEUTRO, no bloquea | NEUTRO, no bloquea |
| estado de la ventana | DECIDE NICOLÁS | DECIDE NICOLÁS |

Por la tabla del pre-registro §8 d: M mejora en una sola ventana (V1) y P2 bloquea en V1 (VIIRS 750) y en V2
(VIIRS 375, sólo con SN). Ninguna fila lleva a CUMPLE ni a NO CUMPLE.

## Lo que informa sin decidir

- **Tabla de latest.php sola en V1** (`envoltorios/v1_solo_tabla.py`, sólo cambia `VENTANAS` en memoria): mismo
  veredicto; P2 de VIIRS 375 con SN pasa de EMPATE a BLOQUEA (neto +2, p 0,40); P1 con 22 y 21 protegidas.
- **Estrato 203** (V750, cúmulo de cumbre de K en 0,0 MW): V1 44 pasadas, D recupera 10 alertas y enciende 16
  negativos limpios; V2 82 pasadas, recupera 23 y enciende 21. Ahí está casi todo el P2 de VIIRS 750.
- **Ganancia típica de D sobre K (ĝ)**: ×1,3 a ×1,9 según estrato; por volcán va de ×1,04 (Chillán V375) a ×5 a ×22
  (Láscar V750 en V1, Tupungatito V750 en V2, con pocos pares).
- **Chillán** (informa): V375 razón 0,578 → 0,601; V750 0,385 → 0,556 (V1, SN).
- **V375 con kernel**: d ≈ 0 como se predijo; en V2 con cenit > 40° d = +0,003 [+0,002; +0,004] (EMPEORA en un estrato
  que sólo informa).
- **P4**: 1 cúmulo movido en V1 y 3 en V2, ninguno protegido; 8 y 6 pasan de `far` a `summit`. **P5**: un `d9_capped`
  nuevo en V1; ningún `discarded_reason` cambia; los filtros del tablero no apagan nada.
- **Placebo K×1,2** da MEJORA por d en V750 ≤ 40° y V375 ≤ 40° (por eso existe el comparador d′).

## Brazo del 17 al 19 de octubre (D-35, run 39756261926): NO ENTRA AL VEREDICTO

Evaluado con la configuración de V1 vaciando en memoria la exclusión de D-29 (`envoltorios/s17_sensibilidad.py`):
271 pasadas por brazo, controles OK, P1 CUMPLE (6 y 6), P2 SIN SUSTRATO (0 y 1 noches), M INDECIDIBLE: la calibración
de d queda mal calibrada (cola EMPEORA 0,055 contra 0,05) en VIIRS 375 sin kernel con cenit > 40°, 7 pares en 4 noches
(corregido por el verificador, V162-01; la primera versión lo atribuía a d′ en un estrato de 6 pares). Chillán V375
0,456 → 0,493, V750 0,447 → 0,508. Igual con la tabla sola. Comando: `python envoltorios/s17_sensibilidad.py --ventana
V1 --desde 2026-10-17 --hasta 2026-10-19 --raiz <S17> --logs <S17>/logs --calibracion simetrica --out s17.json`
(agregar `solo_tabla` como primer argumento para la variante con la tabla sola).

## Cómo se reproduce

Artefactos `s146ab-todo` de los runs 39530508296 (V1, el del intento 2, 13:55 UTC del 2026-10-21), 39575542584 (V2a),
39612909810 (V2b) y 39756261926 (17 a 19-oct), descomprimidos cada uno en su carpeta. Desde la raíz del worktree:

```bash
python experiments/_s157_prereg_d25/evaluar_d25.py --ventana V1 --raiz <V1> --logs <V1>/logs --calibracion simetrica --out v1.json
python experiments/_s157_prereg_d25/evaluar_d25.py --ventana V2 --raiz <V2a> --raiz <V2b> --logs <V2a>/logs --logs <V2b>/logs --ruido-de v1.json --calibracion simetrica --out v2.json
python experiments/_s157_prereg_d25/evaluar_d25.py --combinar v1.json v2.json
```

Salidas completas en `salidas/` (logs, JSON y la cobertura de cada run).

Notas del verificador: el run de V1 figura en `failure` sólo porque el intento 2 no pudo publicar su rama de salidas
(push rechazado); su artefacto y la cobertura están completos (V162-02). El sha256 `93c26d62...` es el del archivo con
CRLF del checkout de Windows; el blob de git (LF) da `2e557697...`, con contenido idéntico al del tag (V162-03).

## Verificación

Verificador con contexto limpio (Fable 5.1, high): re-corrió el evaluador sobre V1, V2, V1 con la tabla sola y el brazo
del 17 al 19, y los cinco JSON y el combinado salen idénticos bit a bit; recomputó P2 por enumeración exacta (V1 VIIRS
750 p PIERDE 0,1635 contra 0,1619 por sorteos). Afirmaciones (a) a (e) CONFIRMADAS; (f) y (g) CONFIRMADAS EN PARTE por
los detalles corregidos arriba. Informe completo en `verificacion/INFORME.md`.
