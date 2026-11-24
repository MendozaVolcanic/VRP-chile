# S197, issue #1106: por qué no publicamos Chaitén MODIS 2026-11-19 02:30 UTC

Pre-registro (escrito antes de despachar): `PREREGISTRO.md`. Todo número sale de un script de esta carpeta, con su
salida al lado. Nada de producción cambió.

## Resumen

| Pregunta | Respuesta |
|---|---|
| ¿El record está al día (A8)? | Sí: la vía re-corrida en Actions sobre el gránulo da lo mismo que el record de main en las 5 pasadas (`control_produccion` vacío), y la copia del detector del arnés es igual al módulo (`control_copia_igual`) |
| ¿Lo explica el piso de D36 (0,02 contra 0,01 de la Tabla 1)? | **No (H1 refutada).** Ningún brazo (A, B, B1, B2) alerta la pasada |
| ¿Dónde está lo que vio MIROVA? | Un núcleo tibio chico al suroeste del cráter. Su celda más caliente (fila 27, col 22) está a 3,61 km del **centro de la grilla**, la distancia que publica MIROVA, y a 2,83 km del cráter |
| ¿Por qué no lo publicamos? | Caso de borde doble: (1) esa celda queda una columna fuera de la caja sensible de 5 × 5, que en MODIS está centrada en la grilla y no en el cráter (el cráter cae en la celda (25, 24), el centro es (25, 25)); (2) aun moviendo la caja al cráter, la celda pasa el NTI (0,007163 contra 0,0058) pero no el ETI por 0,15 % (0,004068 contra 0,004074) |
| Categoría física (A54) | **SIN ATRIBUIR**, lo más probable transitorio o artefacto: no es el foco del domo (ese está a ~0,4 km y lo vemos igual que MIROVA en VIIRS 375 todo el año), vale unas 5 veces lo que el domo, la vista era oblicua (51°) con la escena muy nublada, y ningún VIIRS lo vio 2,5 a 4 h después |

## 1. El fenómeno

Chaitén tiene un foco térmico débil y persistente en el domo de 2008, a unos 0,4 km del cráter, de 0,05 a 0,3 MW: MIROVA
lo publica en VIIRS 375 casi todas las semanas de 2026 y nosotros lo publicamos igual (cruce de la tabla de MIROVA con
`data/mirova_equivalent/Chaiten.json`, hecho en la sesión; no se guardó como script). La alerta del 19-nov es otra cosa:
MODIS Terra, cenit 51°, 1,07 MW (OCR: entre 1 y 2 MW), clase «Bajo», a 3,61 km. Es la primera alerta MODIS nocturna de
MIROVA en Chaitén desde marzo (D36 contó 0, `experiments/_s190_d36/p1_pasadas.json` en main). Esa noche VIIRS (05:06,
06:06, 06:48 UTC) no vio nada, ni MIROVA ni nosotros, y la miniatura de MIROVA de esa pasada muestra una escena muy
nublada con el mar tibio al suroeste.

## 2. El mecanismo en el detector

`campo_chaiten.py` corre la vía de producción sobre el recorte nativo del gránulo (artefacto del run 45290835369,
`nativos/Chaiten_A2026323.0230_MOD021KM.npz`, retención 30 días) y guarda el contraste de cada celda
(`campo_chaiten_salida.txt`). El núcleo tibio está al suroeste y al sur del cráter: fila 27, columnas 21 a 23 (dNTI 0,0038,
0,0072 y 0,0041) y fila 26, columnas 22 a 26 (0,0022 a 0,0049). La caja sensible de MODIS («def», 5 × 5 al centro de la grilla) cubre las columnas 23 a 27: la celda más caliente,
la 22, cae en la región conservadora, donde el umbral es 0,02 (o μ + 10σ ≈ 0,0116 con la Tabla 1). Con 0,0072 no llega con
ninguno de los dos números, y por eso B y B2 tampoco alertan.

`cajas_5_pasadas.py` (salida `cajas_5_pasadas_salida.txt`) prueba la misma vía con la caja sensible movida al cráter
(«crater») y con todo el anillo sensible («sens»): la celda (27, 22) pasa a ser la decisiva, con margen 0,998 (el NTI
pasa; el ETI queda 0,15 % bajo su umbral). Ninguna de las 3 negativas de Chaitén ni Villarrica 2026-09-25 cambia con
ninguna caja.

Lo que no se puede saber: qué caja y qué detalle numérico usa MIROVA en MODIS (su código MODIS no es público; el `.m`
de OSF es de VIIRS 750). Que la distancia de MIROVA sea exactamente la de esa celda al centro de la grilla sugiere que
alertó esa celda; con nuestra grilla, eso exige que su caja sensible la incluya y que su ETI la pase, o que su
geolocalización la ponga una celda al este.

## 3. Por qué la auditoría sigue fuera de banda

El recall MODIS de 94,6 % (35 de 37 noches) junta dos pérdidas: esta y Villarrica 2026-09-25 08:05 (0,9 MW, no
protegida, margen 0,20 en la cumbre), que sale de la ventana de 60 días el 2026-11-24. Con una sola pérdida el recall
vuelve a banda, pero la regla de alerta protegida sin publicar («cualquiera, sin mínimo de noches») mantiene el flag
cada semana hasta que la pasada salga de la ventana (mediados de enero), salvo que se agregue a `PERDIDAS_ACEPTADAS`
de `scripts/auto_audit_weekly.py`, que es decisión de Nicolás con su issue.

## 4. Lo que queda para decidir (Nicolás)

- **Recomendado:** aceptar la pérdida (`PERDIDAS_ACEPTADAS`, clave exacta Chaiten, MODIS, 2026-11-19 02:30) sin cambiar
  el detector: ni el piso de D36 ni mover la caja la habrían publicado, y la señal no parece del volcán.
- **Alternativa (medir, no adoptar):** A/B de la caja sensible de MODIS centrada en el cráter contra centrada en la
  grilla, con los recortes nativos de D36 (330 pasadas, artefactos del run 44016042341 hasta ~2026-12-17), en local y sin
  red. Sólo vale la pena si se quiere saber si la caja al centro le cuesta algo a MIROVA en otros volcanes donde el
  cráter no está en la celda central.

## 5. Procedencia

- Arnés: `experiments/_s190_d36/p1_runner.py` y `brazos.py` (este PR ajusta `brazos.py` para la firma de
  `detectar_mirova` de S195 y S196: `zona_a`, `s_a` y `piso_a` se exigen en None y se descartan; los controles locales
  siguen 40 de 40 iguales a producción). Se corrió desde la rama desechable `s197-1106-probe` (5 pasadas en
  `p1_pasadas.json` y `s173-cenit-modis.yml` reescrito sólo allí), run 45290835369; resultado en
  `probe_resultados_run45290835369.json`.
- Corridas fallidas antes de esa: 45285422432 y 45289859244 (HTTP 401: el token del secreto había sido revocado el
  2026-11-23 ~23:02 UTC; Nicolás lo rotó a las 23:35:59 UTC) y 45290270468 (el arnés sin el ajuste de firma).
- Los scripts leen los recortes desde `D:\vrp-trabajo\temporales\s197\probe4\` (copia local del artefacto).
