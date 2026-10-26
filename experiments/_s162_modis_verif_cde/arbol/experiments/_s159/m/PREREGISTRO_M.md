# Pre-registro S159, frente M: MODIS con MxD03 contra `_interp_geo`

Escrito y commiteado **antes** del primer despacho del probe (2026-10-21). Los números de hipótesis y refutación son
los del plan, `docs/superpowers/specs/2026-10-21-pruebas-post-auditoria-s158-design.md` l. 69, no se inventan acá
(A115).

## Pregunta

El pipeline ubica cada píxel MODIS estirando la grilla de 5 km del propio L1B con `scipy.ndimage.zoom`
(`pipeline/process_modis.py:385-396`, llamada en `:292-293`) y no lee el MxD03 que baja y exige
(`process_modis.py:513`: «geo_path is accepted for API compatibility but not used»). S151 midió en Láscar que eso
corre el píxel del cráter hasta 2,6 km hacia el sensor de un lado del barrido. **Lo que no está medido es si eso
cambia lo que se publica**: la clase `summit`/`far`, el fondo del anillo y la magnitud.

- **Hipótesis (plan)**: la geolocalización interpolada corre los píxeles 1 a 1,7 km hacia el nadir y cambia clase y
  fondo.
- **Refutación (plan)**: con MOD03 las posiciones cambian menos de 0,5 km, o no cambia ninguna clase.

## Qué se corre

`probe_m.py`, en GitHub Actions (pyhdf), sobre los objetivos de `objetivos.json` (armados por
`armar_poblacion.py` desde `data/mirova_equivalent/`, todas las fechas, 11 Tier A). Por cada record corre la función
de producción `process_modis.calculate_vrp` y después `store.append_record` (con `store.DATA_DIR` en un temporal) tres
veces sobre el mismo L1B:

- **A**: tal como producción.
- **A2**: igual que A (nulo de ejecución).
- **B**: igual que A, salvo que `read_modis_l1b` devuelve la lat/lon por píxel de MxD03. Nada más cambia: ni los
  ángulos, ni las bandas, ni el perfil.

Estratos (conteos de `armar_poblacion.py`, lado del barrido por la regla de S151 que se comprueba después con el frame
real):

| estrato | definición | n |
|---|---|---|
| S1 | `summit`, lado del frame 0, cenit > 40° | 38 |
| S2 | `summit`, lado contrario, cenit > 40° (contraste) | 25 |
| S3 | `summit`, cenit < 10° (4 por lado; control de efecto chico) | 8 |
| S4 | `far`, lado del frame 0, cenit > 40° (dirección far a summit) | 12 |
| S5 | Chillán del #864: 2026-10-12 07:20 y 2026-10-15 01:05 UTC | 2 |
| S6 | Láscar `MYD021KM.A2026073.0705` (control positivo de S151) | 1 |

Por posición dentro del gránulo: **extremo** si el píxel del cráter cae a menos de 400 líneas del principio o del fin
(el desfase de traza previsto pasa de 1,2 líneas), **centro** en otro caso.

## Métricas primarias

1. **Desplazamiento del píxel caliente**: para el píxel de máxima BT del cúmulo publicado por A, MxD03 menos
   `_interp_geo` en el mismo (i, j), en km y con rumbo. **Mediana** por estrato (A70), nunca media.
2. **Cambios de clase**: número de records cuyo `distance_class` publicado difiere entre A y B, sobre S1 + S2 + S4.

Se informan además, sin entrar al veredicto: desplazamiento del centroide del cúmulo (A contra B, que incluye cambios
de detección), cambio del conjunto de píxeles detectados, Δ `t_bg_k`, Δ `primary_cluster.vrp_mw`, si cambia lo que el
tablero publica (`mirovaEqVrp` de `frontend/index.html` ejecutada con node, A97), y para Chillán: si el gránulo está en
CMR, si el pipeline lo procesó y si aparece el volcán con MxD03.

## Veredicto (fijado ahora)

- **Instrumento válido** sólo si: (a) en S6 la componente hacia el sensor en el píxel del cráter reproduce la de S151
  (2,581 km, run 38733452917) dentro de 0,05 km; (b) el nulo de geometría (`_interp_geo` contra sí misma) da 0 en todos
  los records; (c) A y A2 dan el mismo record publicado en todos. Si falla cualquiera: **INSTRUMENTO ROTO**, no hay
  veredicto.
- **REFUTA** si la mediana de la métrica 1 queda bajo 0,5 km en S1 **y** en S2, **o** si la métrica 2 da 0.
- **CONFIRMA** si la mediana de la métrica 1 en S1 es 1,0 km o más **y** la métrica 2 da 1 o más.
- **PARCIAL** en cualquier otro caso. **INCOMPLETO** si falta algún gránulo (el script sale con código 2).

Además, sin entrar al veredicto: cuántos records de A reproducen el record publicado hoy en `data/` (la mayoría se
escribió con `codigo_sha` 3695f675; si A no lo reproduce, la comparación A contra B sigue valiendo porque los dos brazos
corren el mismo código, pero se dice).

## Las dos preguntas del instrumento

1. Si la geolocalización estuviera completamente rota, ¿se vería? Sí: B cambia las posiciones por píxel, y la prueba
   sintética (`probar_m.py`) muestra que la métrica 1 mide 3,0 km donde el defecto lo pone y < 0,01 km donde no lo hay.
2. Si el instrumento estuviera muerto, ¿el resultado se vería distinto? El nulo A contra A2 y el de geometría tienen
   que dar exactamente 0, y el control S6 distinto de 0: un cero en la métrica 2 con S6 en 2,58 km no es «no medí».
