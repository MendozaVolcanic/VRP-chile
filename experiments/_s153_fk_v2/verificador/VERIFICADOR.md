# Verificador con contexto limpio: A/B F/K, V2 y combinado (regla de adopción de K, PR #848)

Sólo lectura sobre el repo (rama `loop/activo`, HEAD `ccc881137`). Todo lo de este informe sale de scripts y salidas
guardados en `C:\Users\nmend\AppData\Local\Temp\claude\verif_fk_v2\` (scripts en `scripts\`, reproducción en `rep\`).

## Veredicto: CONFIRMADO, con cuatro reservas que no lo cambian

El CUMPLE combinado de K con la lectura A, con la regla original y con SN, se reproduce exacto, sale del instrumento
fijado, descansa sobre uniones legítimas y el evaluador sí ve las fallas sembradas sobre los datos reales de V2. No
encontré nada que lo refute. Lo que el CUMPLE no dice (sección 5) es justamente lo que el ciclo del §4 tiene que mirar:
el veto es de Láscar, la magnitud empeora y P3 no lo ve, con el OCR V2 quedaría PENDIENTE por una pasada de Lastarria,
y P4 falla.

## 1. Reproducción

- `evaluar_fk.py --ventana V1 --raiz v1_38639658446\union_2766 --logs i3\logs` y `--ventana V2 --raiz
  v2a_38648773684\union_2766 --raiz v2b_39033530622\union --logs v2a\i2\logs --logs v2b\logs_union --ruido-de
  rep\v1.json`: **0 claves distintas** en `v1.json` y `v2.json` contra `experiments\_s153_fk_v2\`; los logs ordenados
  son idénticos y `combinado.log` también (`scripts\jdiff.py`).
- V1 re-evaluada contra la evaluación de S151 (`resultado_v1\v1.json`): 1 diferencia, sólo `sha256_index_html`; el
  cambio de `frontend/index.html` entre las dos no mueve ninguna decisión.
- Combinado: K lectura A CUMPLE (V1 CUMPLE, V2 «CUMPLE | con auditoría espacial pendiente (P4)»); con SN, SE y las
  variantes de 0,04 también CUMPLE. K lectura B: NO CUMPLE (veto) por V1 (no decide, D-4).

## 2. Instrumento y uniones

- **Instrumento**: `git diff 2766c198 HEAD` vacío para `evaluar_fk.py`, `unir_intentos.py`, `armar_tabla.py`,
  `scripts/` (banco_paridad, clase_mirova, calidad_referencia), `_s146_ab_sin_test1/evaluar.py`,
  `frontend/index.html` y `pipeline/`; la copia de trabajo difiere de HEAD sólo en fin de línea (autocrlf; sha sin CR de
  index.html = el de git).
- **Fechas**: PR #848 mergeado 2026-10-18 00:06:05Z; #847 (2766c198) 2026-10-17 23:34:29Z; las carpetas temporales de la
  evaluación de V2 son de 02:35Z. Que nadie viera un veredicto de V2 antes: SIN VERIFICAR más allá de esas horas.
- **Código de los runs** (`gh api`): V1 `402447f3`; V2a, V2b y la repetición 39068999603 `7b74435e`.
- **Origen de cada record de la unión** (`scripts\a2_intentos.py`, `a2\origen_flags.json`): los 19.280 de V1, 11.752 de
  V2a y 12.294 de V2b son idénticos (salvo campos de proceso) a un record de algún intento; ninguno es fabricado.
- **Cableado de cada intento que aporta records**: leí la línea `FLAGS_BRAZO` del log propio de cada brazo, volcán e
  intento (V1 i1 e i3, V2a i1 e i2, V2b i1 e i2): perfil, directorio, los 5 flags declarados y los 2 extra, **0
  problemas**. La desviación de `logs_union` de V2b no oculta nada: cada archivo es copia exacta del log de i1 o de i2 y
  la línea `FLAGS_BRAZO` es idéntica entre intentos en los 4 volcanes repetidos.
- **Diferencias escondidas entre intentos** (`scripts\a2c_pub.py`, independiente de `unir_intentos`: corre
  `armar_tabla` con un intento como control y otro como brazo, mismo brazo): en 4.312 a 5.825 pasadas comunes por brazo
  y ventana, **0** decisiones del tablero distintas, **0** magnitudes mostradas distintas, **0** cúmulos distintos. Esto
  además mide el determinismo de V2, que no tiene gemelo (2.346 a 5.825 pasadas por brazo, 0 cambios).
- Fusión V2a+V2b: 0 claves repetidas entre mitades, 0 records fuera de su mitad, 0 colisiones de clave por sensor.

## 3. ¿Las métricas miden lo que dicen en V2? Siembras sobre los datos reales (`scripts\sembrar_v2.py`, `siembras_resumen.txt`)

| siembra | esperado | obtenido |
|---|---|---|
| K oculta la protegida A Láscar VIIRS375 2026-05-02 06:12 | PENDIENTE (sin gemelo) | P1 PENDIENTE; combinado PENDIENTE |
| la misma, con `--repeticion` que la vuelve a perder | VETADO | P1 VETADO; combinado NO CUMPLE (veto), también con SN |
| K pierde la protegida MODIS Láscar 2026-04-20 01:30 (sin cúmulo, VRP 0) | PENDIENTE | P1 MODIS PENDIENTE; combinado PENDIENTE |
| K oculta una protegida Láscar VIIRS375 de marzo | no decide (A119 b) | CUMPLE: VIIRS desde abril funciona |
| K recibe el record de C0 en 1.126 negativos VIIRS375 que C0 publica | PIERDE | 889 contra 863, NO CUMPLE (suma). Con SN gana por 2 (893 contra 891): la siembra quedó en el borde, no es defecto |
| log de K Láscar en V2b con banda 22 apagada | K mal cableado | INDECIDIBLE en todo |

Tabla sola: confirmado en código (`evaluar_fk.py:109-120`, OCR reemplazado por su encabezado) y en el sustrato (alertas
VIIRS375 426 sin OCR, 614 con OCR). Láscar domina: protegidas A que deciden en V2, VIIRS375 36 de 38 (Isluga 1, Puyehue
1), VIIRS750 39 de 42 (Puyehue 3), MODIS 6 de 6 (las que C0 publica); en V1, Chillán 10 de 12, 9 de 10 y 2 de 3.

## 4. Lo pendiente antes del ciclo

**P4** (`scripts\a4_p4_mag.py`, `a4_p4_mag.txt`). V2: 54 movidas (43 en pasadas que deciden; el evaluador cuenta también
el VIIRS de marzo), 30 hacia el cráter y 24 hacia afuera en radio. VIIRS375 25 (Lastarria 18: 12 afuera, 6 adentro;
Isluga 5; Tupungatito 4, las 4 hacia el cráter), VIIRS750 16 (Láscar 8, Isluga 6 adentro, Puyehue 2), MODIS 6 (Láscar 5
afuera, 1 adentro). Movimiento mediano 1,15 km, máximo 4,06 km; **ninguna cruza el `inner_radius_km`** en ninguna
dirección; 10 son protegidas A (5 MODIS y 4 VIIRS750 de Láscar, 1 Isluga). V1: 8 movidas, 4 y 4, ninguna cruza el
inner. Es radio, no posición (A93): la auditoría A61 sigue pendiente.

**Cruce de 1 MW (§5)**: protegidas A que C0 muestra en 1 MW o más y K deja bajo 1 MW o calla: **0** en los tres sensores
de V1 (3, 12 y 8 de base) y de V2 (5, 21 y 21), y 0 en V2 con OCR. Hacia arriba, 2 en V2 (Láscar MODIS 04-05, 0,77 a
1,09; Isluga VIIRS375 06-10, 0,01 a 1,08). En V1 cruzan hacia abajo 2 alertas VIIRS375 no protegidas. Por la regla por
defecto, la magnitud no bloquea.

**Magnitud que P3 no ve** (`a5_mag.txt`): P3 vuelve a anularse (VIIRS375 n 400, d mediana 0 [0, 0]). En los pares que
cambian, K queda bajo C0: V2 VIIRS375 127 de 144, media de d +0,031 [+0,012, +0,049], signos p = 7,8e-5, razón mediana
0,762 a 0,669; V2 VIIRS750 10 de 10, +0,055 [+0,018, +0,098], p = 0,021, 0,594 a 0,534; MODIS sin señal (7 pares).
V1 VIIRS375 igual que el verificador de V1 (+0,048, p = 0,00035).

## 5. Lo que el CUMPLE no dice

1. **Poder fuera de Láscar y de Chillán en erupción**: en las dos ventanas deciden 8 protegidas en los otros nueve
   volcanes (V1: Villarrica MODIS 1, Planchón VIIRS375 1, Puyehue VIIRS750 1; V2: Isluga 1, Puyehue 4). Con 8, una
   pérdida de hasta 18 % pasa sin verse con 20 % de probabilidad. Fuera de Láscar lo medido es el costo (MODIS: 18 de
   2.173 negativos publicados con K contra 242 con C0).
2. **V2 con tabla sola**: con `--solo-tabla no`, V2 queda **PENDIENTE DE REPETICIÓN** con la lectura A por una pérdida
   que no es de Suomi NPP: **Lastarria VIIRS375 2026-04-18 04:42, NOAA-20, MIROVA 1,29 MW, alerta sólo del OCR**. C0
   publicaba un píxel de 0,055 MW a 2,77 km por el Test 1; K ve 0,53 MW a 19,6 km y lo calla como `far`. La tabla no
   tiene fila VIIRS375 de esa pasada y la fila del OCR trae Distancia_km 0 (antes del 2026-06-13 el OCR no medía
   distancia). Parece el patrón «C0 publicaba otro objeto», pero es SIN VERIFICAR: hay que mirar la imagen. No decide
   por la regla (§4.2 manda listarla). Las 39 protegidas VIIRS de marzo (75 con OCR) que no deciden: K no pierde ninguna.
3. **P3 ciego**: su CUMPLE es letra del pre-registro; la magnitud de VIIRS sí se aleja de MIROVA (sección 4).
4. **El ruido de P2 en V2 es el del gemelo de V1** (0 discordantes); con márgenes de 863 contra 63, 420 contra 46 y 268
   contra 25 no importa.
5. Siguen abiertos de V1: las 2 protegidas de Tupungatito de Suomi NPP (segundo lector) y K sobre el `main` de hoy (§4.5).
