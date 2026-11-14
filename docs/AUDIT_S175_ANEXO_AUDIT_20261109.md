# Anexo de AUDIT_S175 (§10): el audit semanal del 2026-11-09

> Escrito en S178 (2026-11-10) para cerrar el §10 de `docs/AUDIT_S175.md`, que lo dejaba pendiente. No cambia ningún
> veredicto de la auditoría; agrega evidencia a uno (101) y corrige la hora del §10. Autor: agente de S178, sin
> verificador independiente todavía.

## 0. De dónde sale cada número

- **El audit.** Run 42684784167 del workflow «Auto-audit semanal paridad MIROVA» (cron, creado 2026-11-09 19:35:21 UTC,
  `headSha` `e79314dac`, éxito), que escribió `data/audit_continuous/latest.json` en el commit `847b39491` de main
  (2026-11-09 19:50:04 UTC, `generated_utc` 19:50:03Z) y abrió el issue #973. Corrió a las 19:35 UTC, no a las 09:00
  como decía el §10: el cron es `0 9 * * 1`, pero GitHub lo dispara con 7 a 10 h de atraso (11-02 19:15, 10-26 15:56,
  11-09 19:35; agregado S178 tras el verificador limpio). Todo número marcado **[latest]** se lee de ese archivo (`git show 847b39491:data/audit_continuous/latest.json`).
- **Reproducción.** Los diagnósticos importan `scripts/auto_audit_weekly.py` del mismo commit, sobre un árbol parcial de
  `847b39491` (`pipeline/`, `scripts/`, `data/mirova_equivalent/`, `data/mirova_reference/`, `volcanoes.yaml`,
  `frontend/cambio_detector.js`), con «hoy» fijado al 2026-11-09. Reproducen exacto los tres flags (recall VIIRS 750
  73,3 % con n 15; Chillán VIIRS 375 0,579 con n 7; Tupungatito VIIRS 375 0,373 con n 6). Scripts y salidas, fuera
  del repo: `D:\vrp-trabajo\temporales\s178_anexo\diag_1109.py` a `diag_1109_d.py`, con su `*_salida.txt`. Los números
  marcados **[diag]** salen de ahí.
- **Guardia MODIS.** `data/audit_continuous/guardia_modis_latest.json` en `847b39491` (generado 2026-11-09 01:58 UTC) y
  en `f0a3b1f1a` (2026-11-10 01:16 UTC), marcados **[guardia]**.

## 1. Qué salió fuera de banda

Veredicto **FUERA_DE_BANDA** con tres flags, los tres de **VIIRS con el detector K** (VIIRS sigue en K) [latest]:

| Flag | Valor | Banda | n |
|---|---|---|---|
| Recall VIIRS 750 | 73,3 % | 79,5 % | 15 noches |
| Magnitud Nevados de Chillán VIIRS 375 | 0,579 × | 0,7 a 1,4 | 7 noches |
| Magnitud Tupungatito VIIRS 375 | 0,373 × | 0,7 a 1,4 | 6 noches |

**Qué tramo mide cada flag (ojo con los regímenes).** El audit juzga VIIRS sólo desde el 2026-11-03: el cese de Suomi
NPP (2026-11-02 13:00 UTC, `scripts/ceses_esperados.json`) parte la ventana y lo anterior va a `plataformas.aparte`
[latest]. Los tres flags son entonces de **la ventana de 7 días calendario, 2026-11-03 a 2026-11-09, sólo NOAA-20 y
NOAA-21, todo K** (dentro de ella, n = 15, 7 y 6 noches volcán y sensor, como dice la tabla): no mezclan
detectores ni plataformas. El recall de VIIRS 750 llega justo al mínimo de 15 noches (`MIN_N_RECALL`), así que el flag
va a oscilar mientras la ventana post cese crezca (A90).

**MODIS no se juzga.** Desde la frontera de la vía (fecha de observación 2026-11-02) hay 7 noches con alerta de MIROVA,
bajo el mínimo de 15 [latest]. La vía da 7 de 7 (100 %) y Chillán MODIS 1,035 × (n 7), sin flag posible. Las noches
MODIS anteriores son de K y van a `por_detector.K` (recall 70,0 %, n 20) [latest]. Las 7 noches de la vía incluyen la
del 2026-11-02 (01:15 a 07:30 UTC), que es retrospectiva según §4.1 de la regla de reversión: sus records son de la vía
porque el producto estándar llegó después del encendido (FICHA v1.19). Un record MODIS de K quedó en noche de la vía
(`fuera_de_detector`: 1) [latest]: Planchón-Peteroa, Terra 2026-11-02 01:15, `product_version nrt`, procesado 02:28 UTC,
antes del encendido, sin VRP de cúmulo [diag d]; es la pasada que la FICHA v1.19 declara «sigue como NRT».

## 2. Por qué, flag por flag

### 2.1 Recall VIIRS 750: las 4 noches perdidas son el hallazgo 101 (cúmulo de cumbre en 0,0 MW)

Lo que pasa en el volcán: una anomalía débil (MIROVA 0,11 a 0,27 MW) en la cumbre. Lo que pasa en nuestro pipeline: el
detector **sí** la encuentra (un píxel en la pasada de MIROVA, a 0,03 a 1,04 km del centro, clase `summit`; en los dos
records leídos enteros, Isluga 11-06 y Láscar 11-05, entra por el camino de contraste dNTI),
pero su temperatura de brillo en el infrarrojo medio está **a la del fondo del anillo regional o bajo ella**, así que el
exceso de radiancia sale negativo, se recorta a cero, el cúmulo queda en 0,0 MW y el tablero no lo publica [diag a, b]:

| Noche | MIROVA (misma pasada) | Nuestro record de esa pasada |
|---|---|---|
| Isluga 2026-11-06 | 0,24 MW, 05:42 (tabla) | NOAA-21 05:42, 1 píxel, BT 270,91 K, `t_bg` 271,07 K, 0,0 MW |
| Láscar 2026-11-05 | 0,25 MW, 06:06 (tabla) | NOAA-21 06:06, 1 píxel, BT 265,77 K, `t_bg` 266,55 K, 0,0 MW |
| Láscar 2026-11-08 | 0,27 MW, 06:06 (tabla) | NOAA-20 06:06, 1 píxel en cumbre, 0,0 MW, BT bajo `t_bg` |
| Tupungatito 2026-11-07 | 0,11 MW, 05:30 (tabla) | NOAA-21 05:30, 1 píxel en cumbre, 0,0 MW, BT bajo `t_bg` |

**4 de 4** fallas del tramo juzgado tienen esa firma (en las 4, todos los píxeles del cúmulo con BT menor o igual a
`t_bg`), y **7 de 9** en el tramo aparte (2026-09-10 a 11-02, también K; las otras 2 son noches sin cúmulo: Chillán
09-28, 0,23 MW, y Cordón Caulle 09-28, 0,38 MW) [diag b]. Ninguna es protegida: las cuatro están bajo 1 MW. Es el
mecanismo de 101 (`experiments/_s175_audit/f0/INFORME.md`, 101/203), comprobado ahora en los records. **Por qué MIROVA
sí les da potencia: SIN ATRIBUIR.** Candidata no medida: su código V750 estima el fondo interpolado bajo el halo (D34,
`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`), no con un anillo regional.

### 2.2 Magnitud de Chillán VIIRS 375 (0,579 ×): SIN ATRIBUIR, con dos candidatas descartadas

- **No es la elección de la pasada.** Pareando pasada con pasada (±120 s), la razón también es baja, y cae con el cenit
  del sensor [diag c]: cenit menor que 30°, mediana 0,801 (n 5); 30° a 50°, 0,506 (n 4); 50° a 60°, 0,431 (n 3); 60° o
  más, 0,289 (n 5). El peor caso: 2026-11-09 04:54, MIROVA 36,56 MW contra 1,23 MW nuestros a 58° de cenit.
- **No es el núcleo F5 contra la suma del cúmulo.** Con `pc.vrp_mw` en vez de lo publicado (`f5_core_vrp_mw`) la mediana
  de la noche da la misma 0,579 [diag b].
- Es el mismo patrón de cenit de S154 (Chillán cae con el cenit, atribución vigente SIN ATRIBUIR) y de F2-202 de esta
  auditoría (pérdidas concentradas en cenit de 50° o más). Ni este anexo ni esas mediciones aíslan el mecanismo.
- Pista exploratoria, no evidencia de este anexo: el bloque de arranque S178 (§a) anota una comparación de producción
  contra la sombra de la vía en la misma pasada, 2026-11-03 a 11-09, con VIIRS 375 K 0,485 contra vía 0,993 (n 47),
  **sin verificador** (`C:\Users\nmend\vrp-temporales\s177_cmr\magn_1109\m.py`). Si se confirma, el déficit es del
  detector K y no del sensor.

### 2.3 Magnitud de Tupungatito VIIRS 375 (0,373 ×): SIN ATRIBUIR

Régimen muy débil: MIROVA entre 0,06 y 0,35 MW en las 6 noches; nosotros un cúmulo de 1 o 2 píxeles en cumbre, de 0,0 a
0,086 MW en las pasadas pareadas con MIROVA (0,104 MW es una pasada sin alerta de MIROVA; corrección S178 del
verificador limpio: el texto decía «0,007 a 0,104»); el máximo publicado de cada noche va de 0,037 a 0,104 MW [diag b]. Misma pasada, por cenit: menor que 30°, 0,662 (n 2); 30° a 50°, 0,279 (n 3); 50° a 60°, 0,32 (n 2);
60° o más, 0,118 (n 1) [diag c]. El n por tramo es demasiado chico para leer una curva. El núcleo F5 tampoco explica:
0,373 contra 0,372 con `pc.vrp_mw` [diag b]. El antecedente que cita el issue (déficit de régimen débil de S124) es eso,
un antecedente: no está medido aquí.

## 3. ¿Son los mismos de #936 (2026-11-02) y #915 (2026-10-26)?

| Métrica | #915 | #936 | #973 (este) |
|---|---|---|---|
| Recall VIIRS 750 (K) | 74,0 % (n 50) | 79,2 % (n 53) | 73,3 % (n 15, sólo post cese) |
| Chillán VIIRS 375 (K) | 0,662 × (n 21) | 0,605 × (n 27) | 0,579 × (n 7) |
| Tupungatito VIIRS 375 (K) | 0,41 × (n 20) | 0,371 × (n 25) | 0,373 × (n 6) |
| Recall MODIS | 62,5 % (K) | 72,7 % (K) | sin juzgar (vía 7 de 7, bajo el mínimo) |
| Chillán MODIS | 0,56 × (K) | 0,401 × (K) | sin juzgar (vía 1,035 ×, n 7) |
| Chillán VIIRS 750 | 0,683 × | 0,666 × | 0,704 × (n 7), en banda por 0,004 |
| Cordón Caulle VIIRS 750 | 0,375 × | 0,512 × | 0,446 × con n 3, bajo el mínimo de 5: sin flag |
| Protegidas MODIS de Chillán sin publicar (K) | 3 | 4 | las mismas 4, sin flag |

Valores de #915 y #936 tomados del cuerpo de cada issue; los de #973, de [latest].

- **Ningún flag nuevo.** Los tres de #973 ya estaban en #915 y #936, en el mismo sentido. La diferencia es de tramo: los
  de #973 miden sólo 7 noches post cese, los anteriores 60 días con Suomi NPP. No se comparan como serie (A90, A104).
- **El recall de VIIRS 750 es el mismo mecanismo en lo que se pudo mirar.** En la parte de la ventana de #936 que cae
  dentro de la de este audit (2026-09-10 a 11-02), 7 de 9 fallas son cúmulos de cumbre en 0,0 MW [diag b]. Lo de #936
  anterior al 2026-09-10 y lo de #915 no se re-midió.
- **Lo de MODIS no se arregló: dejó de juzgarse.** Los flags MODIS de #915 y #936 eran de K. Con la vía vigente, el
  audit juzga MODIS sólo desde el 2026-11-02 y todavía no junta 15 noches. Las 4 protegidas MODIS de Chillán perdidas
  por K (2026-10-12 07:20, 10-15 01:05, 10-25 07:20 y 10-30 07:15) **siguen en `alertas_protegidas.lista` como
  `sin_publicar`**, pero no salen ni como flag ni en «informado aparte» del issue, porque son de un detector que ya no es
  el vigente [latest; diag c]. Es el diseño de S156 («juzga sólo el vigente»); se anota para que nadie lea su ausencia
  en #973 como recuperación. La de 10-30 existe sólo en el OCR (decisión 9 de AUDIT_S175).
- **La vía MODIS, en lo que hay:** 13 de 13 protegidas MODIS desde el 2026-11-02 publicadas, todas de la vía [diag c].

## 4. Contra la regla de reversión (§4 de `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md`)

El audit semanal no es el disparador de la regla (§4.3 lo da la vigilancia de la guardia), pero dice lo mismo:

- **Sin candidata a reversión.** Guardia VERDE en las dos lecturas que rodean el audit, `reversion` vacío,
  `protegidas_sin_record_produccion` vacío, `borde_del_encendido` vacío, sin avisos ni caídas a K [guardia].
- **Plazo (§4.6):** 8 protegidas vistas por la guardia de 29 al 2026-11-09 01:58 y 11 al 2026-11-10 01:16; vence el
  2027-03-02 20:11 UTC [guardia].
- **Investigación (§4.4):** Muy Bajo 0 de 0 (cota 2); sobre-publicación diferencial 0 de 128 y luego 1 de 152 (Láscar
  2026-11-08 08:00; cota 3, no dispara); nulo 167 pares, 0 distintos [guardia].
- La lista `protegidas_sin_publicar_produccion` de la guardia trae las mismas protegidas de Chillán de octubre, con
  `prod_via: false`: son anteriores al encendido y la regla no las juzga.

## 5. Qué cambia respecto de lo que #955 ya decía

1. **El §10 queda cerrado con este anexo.** El sustituto de F1 (VERDE, vía 100 % en 2 noches, 3 protegidas publicadas)
   coincide en MODIS con el audit real (7 de 7, 13 de 13), pero el veredicto real es FUERA_DE_BANDA por VIIRS, que el
   sustituto no miraba. Ningún veredicto de la auditoría cambia.
2. **101 (gravedad 3, decisión 8) gana peso, no gravedad.** Explica 4 de 4 noches perdidas del flag de recall VIIRS 750
   de este audit y 7 de 9 del tramo anterior. Sigue sin perder ninguna protegida. La decisión 8 («darle un camino nuevo
   dentro del programa de V750») es hoy lo que movería ese flag; con la vía de VIIRS 750 en curso (#975, B2), medir si
   la vía publica esas 4 pasadas es la pregunta barata siguiente (no medida aquí).
3. **F2-202 se repite en Chillán y Tupungatito VIIRS 375** después del cese: la razón cae con el cenit también con sólo
   NOAA-20 y NOAA-21. La causa sigue SIN ATRIBUIR.
4. **Nuevo para el lector del audit:** con el cese, VIIRS se juzga sobre una ventana que arrancó el 2026-11-03; el recall
   de VIIRS 750 está en el mínimo de n y los ratios por volcán quedan con n 3 a 7. Un flag que aparezca o desaparezca en
   las próximas semanas puede ser n, no volcán.
5. **Hora del audit:** corrió 19:35 UTC (cron), no 09:00 UTC como dice el §10.

## Verificación (S178, 2026-11-10)

Verificador limpio de otro modelo (Sonnet, sin el contexto del autor): ANEXO CORRECTO en lo sustantivo. Reprodujo
`latest.json` byte a byte con `auto_audit_weekly.py` de `847b39491` y «hoy» = 2026-11-09, los tres flags, las 4 noches
del hallazgo 101 (BT bajo `t_bg`, cúmulo en 0,0 MW), las razones de Chillán y Tupungatito por pasada y por cenit, y la
tabla contra #915 y #936. Corregido aquí: «7 noches» (son 7 días; n 15, 7 y 6), el rango de Tupungatito (0,0 a 0,086 MW
en pasadas pareadas) y el atraso del cron. SIN VERIFICAR por él: el 0,485 contra 0,993 de la sombra (exploratorio) y la
cita completa de F2-202 (también dice «en Suomi NPP»).
