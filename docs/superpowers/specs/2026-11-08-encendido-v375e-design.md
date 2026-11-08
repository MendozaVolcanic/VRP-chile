# Encendido de la vía «código MIROVA» en VIIRS 375 (V375-E): diseño

Fecha: 2026-11-08. Autor: coordinadora S176. Estado: **BORRADOR para revisión de Nicolás**, nada implementado. Pedido: «porque no publicamos
simplemente la sombra con todos los volcanes?» y, a la propuesta de adelantar VIIRS 375 con guardia K tras el verificador, «Sí, prepáralo».
Modelo: el encendido de MODIS, `docs/superpowers/specs/2026-11-01-encendido-modd-design.md` y `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md`.

## Por qué, como geólogo

MIROVA suma la energía de todos los píxeles que alerta. VIIRS 375 de producción publica el núcleo de un cúmulo que K ya recortó, con un fondo
de anillo propio: el volcán se ve con cerca de la mitad de la potencia que MIROVA le asigna, y el tablero sub-informa una anomalía real. La vía corre el código
publicado por MIROVA sobre su misma grilla, y en la sombra casi calza. Esperar la parada del 2 de diciembre mantiene tres semanas más esa sub-estimación, a cambio de más noches
de evidencia. Nicolás prefirió, como con MODIS, encender antes con K corriendo aparte como guardia.

El costo que se acepta: la vía puede callar señales débiles que K publica. Por eso la guardia y una regla de reversión escrita antes del encendido.

## Evidencia y sus límites

Salidas en `experiments/_s176_preguntas/`. Pasadas nocturnas con alerta de MIROVA, 2026-11-03 a 11-07, mismas pasadas, exploratorio:

| VIIRS 375 | Producción K | Sombra |
|---|---|---|
| Razón mediana contra MIROVA (31 pasadas comunes, verificador con el predicado real del tablero) | 0,50 | 0,99 |
| Dentro de 0,7 a 1,4 (cálculo de S176, n 32, con predicado portado) | 8 de 32 | 31 de 32 |
| Publica en negativos, con la regla D-9 | 10 de 95 | 3 de 95 |
| Alertas publicadas, etiqueta del scraper | 35 de 38 | 34 de 38 |
| Alertas publicadas, con D-9 | 32 de 34 | 31 de 34 |

Verificador limpio (`C:\Users\nmend\vrp-temporales\s176_verpr\medicion\INFORME.md`): **SE SOSTIENE EN PARTE**. La magnitud se sostiene, también sin Chillán en VIIRS 375 (0,496 y 0,989, n 26), y no hay ningún camino por el que la sombra herede el VRP de MIROVA. Corrigió el conteo de producción (35, no 36), el «0 de 91» en negativos, que era artefacto de la etiqueta del scraper, y el alcance: «ninguna pierde una alerta de 1 MW» vale sólo de noche (10 alertas diurnas de Chillán de 1 MW o más no las procesa ninguna). MODIS 1,00 es el mismo código en las dos columnas: control de identidad, no evidencia.

- Las cuatro que calla la sombra son débiles: Puyehue-Cordón Caulle 0,36 y 0,09 MW, Planchón-Peteroa 0,06 y Tupungatito 0,03 (esta última, bajo el corte D-9).
- Límites: 5 noches. El veredicto del verificador permite seguir; el encendido además pide la guardia, la regla sellada y la retrospectiva si llega antes.
- Esta mirada abrió la ventana P del lector sellado después de su sello. No encontré una regla que lo prohíba; queda declarado.

## Decisión 1: enfoque

| Opción | Qué es | Veredicto |
|---|---|---|
| (a) Dos PR, como MODIS | A: infraestructura inerte (guardia, vigilancia, audit, marca del tablero). B: sólo el flag, lo único que se revierte | **Recomendada**: el revert de B sale limpio y A da el nulo de la guardia |
| (b) Un PR | Todo junto | Descartada: S157 mostró que un revert grande choca |
| (c) El tablero lee la sombra | Sólo cambio de `frontend/` | Descartada: la sombra corre una vez al día con horas de atraso, y una vista NRT no puede depender de eso |

## Decisión 2: la guardia

Perfil nuevo `pipeline/profiles/guardia_k_viirs.yaml`: `extends: mirova_equivalent`, `enable_v375_codigo_mirova: false` y `enable_v750_codigo_mirova: false`, sólo los dos VIIRS, carpeta propia (A47). Workflow nuevo
`guardia-k-viirs.yml` calcado de `guardia-k-modis.yml`, sólo `EARTHDATA_TOKEN` (A71). Perfil y workflow nuevos para no tocar lo que el lector de V375-E compara.
Mientras B no entre, guardia y producción deben publicar lo mismo en los dos VIIRS: ese es su nulo (A110), con **al menos tres noches** antes de pedir B.

## Decisión 3: vigilancia y regla de reversión

`scripts/vigilancia_guardia_v375.py`, reutilizando por import las funciones de la de MODIS. Regla nueva `experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md`, sellada por Nicolás antes de B.

- **Reversión**: pasada nocturna posterior al encendido, alerta de MIROVA de 1 MW o más (lectura A, D-9), la guardia K publica y la vía tiene record y calla. Revert de B el mismo día, pre-autorizado, como §4.3 de MODIS.
- **Investigación, sin reversión automática**: alertas débiles perdidas (de las que MIROVA publica y K publica), sobre-publicación en negativos limpios, y pasadas que la guardia registra y la vía no.
- **Cotas de la investigación**: VIIRS 375 tiene mucho más flujo que MODIS, así que la cota 2 de MODIS no sirve. No las elijo después de ver estos 5 días (A115): se derivan de la retrospectiva de V375-E (`experiments/_s162_v375/`, ventana O) o del criterio ya sellado en `PREREGISTRO_E.md`, lo que al escribir la regla resulte citable.
- Plazo por analogía con MODIS: 120 días desde el encendido o el número de protegidas que la regla fije.

## Decisión 4: audit semanal y marca del tablero

- `scripts/auto_audit_weekly.py` trata la vía como un único sensor (`SENSOR_VIA`, `VIA_MODIS`). Se generaliza a un detector por sensor, `VIA_V375`. **Las bandas no se recalibran.**
- `frontend/cambio_detector.js`: marca desde los datos en las series de VIIRS 375. La magnitud sube cerca del doble en esa fecha y el operador debe leer que **no es que el volcán crezca**.
- La frontera es de observación: el NRT re-escribe 8 días hacia atrás, como en MODIS.

## Decisión 5: lo que el tablero debe aguantar antes de B

| Punto | Estado | Qué falta |
|---|---|---|
| Los píxeles de la vía no traen `vrp_mw`: «Todos los pixels» rompe el mapa | #965 con verificador en curso | **Mergear #965 antes de B** |
| Los records de la vía no traen `f5_core_vrp_mw` | Por lectura de código, el tablero cae a `pc.vrp_mw`; el verificador lo comprueba | Probarlo en navegador con records V375 de la vía |
| Regla de cirrus (`t_max` bajo 273,15 K y más de 10 MW oculta el record), pendiente desde S173 para MODIS oblicuo | SIN MEDIR en V375 | Medir sobre la sombra en PR A |
| `diario.html` y `mosaico.html`, copias de helpers (S92) | SIN VERIFICAR | Replicar lo que corresponda |

## Decisión 6: la lectura sellada y el congelamiento

- Con B, la lectura sellada de V375-E (30 noches y 40 alertas, tag `s172-v375e-lector-resellado`) **deja de decidir** el encendido: la reemplazan guardia y regla, igual que pasó con la sombra de 28 noches de MODIS. Se conserva el lector y se corre como informativo. Es decisión de Nicolás.
- El flag toca `mirova_equivalent.yaml`, dentro del congelamiento del §12.6 del programa: necesita su excepción, como MODIS.
- A comprobar en PR A, con control positivo: que el flag de V375 no marque régimen en el lector de V750-A (#964) ni le cambie la sombra de VIIRS 750 ni el NRT de MODIS.
- Durante B se mide el tiempo del NRT: el peor job hoy dura 16 min y el techo es 50 por paso; la vía agrega remuestreo a la grilla.

## Orden

1. Verificador de la medición: SE SOSTIENE. Si no, esto se detiene.
2. Tag `pre-s176-adopcion-v375e`. PR A en borrador, verificador limpio de otro modelo, frase de merge.
3. Guardia corriendo como identidad, al menos tres noches.
4. #965 en main. Audit del lunes leído.
5. Regla sellada. PR B en borrador, con ficha SDA, `docs/MISSION.md`, `CLAUDE.md` y marcas A113. Verificador limpio. Sí de A45 y frase de merge.
6. Vigilancia diaria desde la primera corrida del NRT con la vía.

Si todo sale limpio, B cabría hacia el 2026-11-13 a 11-14. Es una estimación, no un compromiso.

## Lo que no entra

Los 34 volcanes (sección aparte, otra decisión).

## Decisión 7 (2026-11-08): VIIRS 750 entra al mismo plan, con su propio flag

Nicolás: «porque no lanzar todos los sensores con la nueva via?». MODIS ya corre con la vía desde #934; queda VIIRS 750. No hay razón física para dejarlo atrás: en la sombra da 1,00 (n 14, 12 de Chillán) y en la retrospectiva 0,999 [0,978; 1,007] (`experiments/_s162_v750c/INFORME.md`). Lo que le falta es instrumentación, igual que a VIIRS 375, y la guardia con regla la reemplaza del mismo modo.

- PR A cubre los dos VIIRS. PR B se parte en **B1 (VIIRS 375) y B2 (VIIRS 750)**, un flag cada uno, para revertirlos por separado.
- Condición propia de B2: **vara MATLAB del §4.1 en verde** (`experiments/_s162_v750a/vara_matlab_v750a.py`; la candidata dio 311 de 311 iguales). Es la prueba de que el código portado es el de MIROVA. Hoy la vara con Octave da roja por una decisión ya tomada (S163).
- Límites de VIIRS 750 que la vigilancia debe mirar: la región sensible `sens` sólo corre en Cordón Caulle y Tupungatito, desde #939, con pocas pasadas (9 y 8); en Cordón Caulle la sombra publicó 1 vez contra 4 de producción, sin saber aún si esas 3 son sobre-publicación de K.
- #964 y el sello de V750-A dejan de bloquear el encendido; su lectura queda informativa.

## Decisión 8 (2026-11-08): reprocesar la historia

Nicolás: «el reprocesamiento cuando podria hacerse?». Son dos cosas:

- **En carpeta aislada, sin publicar: despachado por tramos (Nicolás, «Sí, despáchalo»).** `reproc-retro-paquete.yml` sigue el pre-registro sellado (`experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md` §10.3): D1 humo, D2 F26 y DM, D3 control K, D4 2025. Son 4.327 volcán-día y **34 a 41 h de pared** según su tabla §10.4 (ESTIMACIÓN; la vía aún no se mide con D1). Faltan los tramos fuera de esa prueba, unos 2.900 volcán-día con la vía (enero, abril a septiembre y desde el 17 de octubre de 2026, y Tupungatito antes del 23 de febrero de 2026): se despachan aparte si el reemplazo los necesita. El humo D1 es el run 42507360401, desde el tag `s172-retro-d1`.
- **Reemplazar lo publicado: después de cada encendido.** Precedente: K se adoptó el 2026-10-18 y #883 reemplazó la historia el 10-21. MODIS ya podría (su historia sigue en K hasta el 2026-11-02); los VIIRS, tras B1 y B2, con tag y frase. Si la retrospectiva corre antes, el reemplazo es aplicar lo ya calculado.
- Sus artefactos duran 30 días en Actions: el reemplazo debe ocurrir antes de que venzan.
