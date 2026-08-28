# Plan S125 — cerrar la brecha de magnitud (no los decimales)

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:executing-plans`.
> Checkboxes `- [ ]` para tracking. Reemplaza al plan del 27-ago, cuyas tareas
> 0-3d están cumplidas.

**Goal:** Explicar por qué reportamos ~la mitad de la magnitud de MIROVA en 4 de
11 volcanes, priorizando por tamaño del efecto y no por facilidad.

**El replanteo que ordena este plan:** los brazos de F70 mueven **0,11** cuando
el hueco es **0,53**. Cierran ~20 % y el 80 % sigue sin explicación. Optimizar
brazos que mueven decimales, mientras el sesgo de fondo es un **factor 2**, es
mirar el lugar equivocado.

**Por qué el factor 2 sí importa** (y los decimales no tanto): para **detectar**
es irrelevante — el recall es 96 % y ninguna variante lo cambia. Para
**cuantificar** no: el VRP alimenta la tasa de efusión (Coppola 2013,
`TADR ~ VRP / c_rad`), así que un factor 2 en VRP es un factor 2 en el volumen
de magma inferido. Si alguien usa nuestro VRP para estimar volumen efusivo o
comparar episodios entre volcanes, ese sesgo se propaga.

---

## Infraestructura ya resuelta (no repetir)

- **Paralelismo**: la concurrencia pasó a ser **por perfil**
  (`reproc-chunked-<profile>`), así que **N brazos corren en paralelo**. El
  límite real es el de GitHub (20 jobs concurrentes en repo público, minutos
  ilimitados): a `max-parallel: 8`, entran **2 brazos completos** con holgura
  para el cron. **No hace falta otra cuenta** — el cuello éramos nosotros.
  El push a main sigue serializado (grupo `push-main`) para no reabrir la
  carrera S25.
- **Verificar todo reproceso** con `05_verificar_reproceso.py`: un run puede
  cerrar verde sin tocar nada (bug del merge, arreglado el 27-ago).
- **Leer siempre apareado** por `(datetime_utc, sensor)`, nunca conteos de
  series completas.
- **Bootstrap obligatorio** antes de afirmar diferencias entre brazos: los IC
  del A/B anterior se solapaban en los 11 y yo leí "sin efecto" donde había
  cancelación de efectos opuestos.

---

### Tarea 1 — Brazo D + control, ventana de 4 meses (EN PARALELO)

**Pregunta:** ¿el sub-reporte viene de que nuestras celdas particionan el
terreno en el lugar equivocado? (D17)

**Evidencia que lo motiva:** el efecto de la grilla correlaciona con su
desalineación — PCC (offset 7618 m) **−0,104**; Láscar (841 m) **+0,110**;
Isluga (61 m) **+0,110**. r = −0,47 con n=8: sugestivo, sin poder para probarlo.

**Por qué 4 meses:** hoy 3 volcanes no tienen muestra (Llaima 0 alertas,
Copahue 1, NdC 3). A 4 meses el total pasa de **178 a 432** noches-alerta
(Láscar 33→84, Tupungatito 19→51, PP 11→41). A 6 meses el rendimiento decae
(1,5× más muestra por 25 % más tiempo).

**Por qué el control se re-corre:** comparar el brazo D (4 meses) contra el
control de 2 meses mezclaría ventanas — el error que ya nos mordió.

- [ ] **1.1 Leer los centros de grilla y persistirlos** en `volcanoes.yaml` como
  campo NUEVO `mirova_grid_center` (no tocar `mirova_center`, que tiene
  excepciones deliberadas — A63). Fuente:
  `experiments/_s124_cuantizacion/02_origen_grilla_por_volcan.py`.

- [ ] **1.2 Perfil `_f70_d.yaml`**: `extends: _f70_b` + usar
  `mirova_grid_center` como centro del regrid. Cambio de config, no de código
  (el regrid ya toma `center_lat/center_lon` como parámetro).

- [ ] **1.3 Criterio pre-registrado, escrito en el yaml ANTES de correr** (A66):
  - **JUEZ**: PCC y Tupungatito (offsets 7,6 y 4,8 km) deben moverse hacia 1,0
    **más que en el brazo B**. Si no, D17 se refuta.
  - **CONTROL INTERNO** (lo que al brazo B le faltaba): Isluga y Lastarria
    (offset 45-61 m) **no deben cambiar** — ya estaban alineados. Si cambian,
    el efecto no es la alineación y el brazo no prueba lo que dice.
  - **Estadístico**: el veredicto exige IC 95 % bootstrap que **no se solapen**
    con el control. Una mediana sin IC no decide nada.
  - Guardas 2-4 y A79 idénticas al brazo B.

- [ ] **1.4 Despachar LOS DOS EN PARALELO** (ya se puede):

```bash
VOLS="Lascar,Isluga,Lastarria,Llaima,Copahue,Tupungatito,NevadosDeChillan,Villarrica,Chaiten,PlanchonPeteroa,PuyehueCordonCaulle"
gh workflow run reproc-chunked.yml --ref main -f profile=_f70_d \
  -f volcanoes="$VOLS" -f start=2026-04-25 -f end=2026-08-24 -f max_days=37
gh workflow run reproc-chunked.yml --ref main -f profile=_f70_control_4m \
  -f volcanoes="$VOLS" -f start=2026-04-25 -f end=2026-08-24 -f max_days=37
```

Requiere crear `_f70_control_4m.yaml` = clon de `mirova_equivalent` con
`data_subdir` aislado (el workflow rehúsa correr contra el operacional).
**~9 h de pared, los dos a la vez.**

- [ ] **1.5 Verificar** ambos con `05_verificar_reproceso.py`, leer apareado con
  bootstrap, y escribir veredicto. **Presentar a Nicolás.**

---

### Tarea 2 — El 80 % del hueco que nadie explica (EN PARALELO con la 1)

**Por qué existe esta tarea:** aunque D17 salga positiva, cierra ~20 % del hueco.
Hay que atacar el resto **en paralelo**, no después — y esta tarea no consume CI,
así que corre mientras la 1 usa los runners.

**Lo ya descartado con datos** (no reabrir, anti-A8): halo de MIROVA (su Npix
mediano es 1) · atribución de cluster · second-run · piso VRP · fondo del anillo
solo · sustrato geométrico alineado a nuestra ancla.

- [ ] **2.1 Descomponer la brecha por régimen, no por volcán.** El hallazgo
  bimodal de S124 (débil sub-integra 0,4-0,7; difuso sobre-integra 12-99×) se
  midió sobre NdC. Repetirlo en los 4 sub-reportadores estratificando por
  `n_anomalous_pixels`: si el déficit vive solo en el modo de 1-2 píxeles, el
  problema es de **integración sub-píxel**, no de fondo.

- [ ] **2.2 Cruzar contra el TIF de MIROVA a nivel píxel** en las noches donde
  ambos detectan. Tenemos `test_r2_pixel_level.py` (9 casos pasando) y el
  archivo local. Pregunta: en la MISMA celda, ¿cuánta radiancia reporta cada
  uno? Eso separa "medimos distinto el fondo" de "medimos distinto el foco" —
  que es la bifurcación que ningún brazo ha resuelto.

- [ ] **2.3 Revisar la cadena de magnitud completa contra Coppola Eq. 6-8** con
  lectura file:line, como se hizo con la detección en S114. La detección se
  auditó línea por línea; **la magnitud nunca**.

---

### Tarea 3 — Deuda que ya está diagnosticada (cuando haya hueco)

- [ ] **3.1 D14 — máscara de nube <260 K**: `MISSION.md` la declara removida y
  está activa; ciega el 23 % de las pasadas; confunde nieve con nube. No cuesta
  recall (2 % vs 23 % base), así que es deuda, no urgencia. A/B con perfiles
  `_d14_mask_{on,off}` — ahora paralelizable.
- [ ] **3.2 Celda de referencia del `Distancia_km` en UTM** (D15, pendiente
  menor): repetir la inferencia con los 903 pares proyectados a UTM.
- [ ] **3.3 Test de determinismo** y **manifiesto de cobertura por corrida**:
  diseños aprobables, sin implementar.

---

## Sobre el gráfico de Nevados de Chillán

**El veredicto no lo afecta.** La figura usa el perfil operacional y el
experimental; ninguno lleva la grilla, y no adoptamos nada. Lo que sí cambió fue
el reproceso v2 (esta vez verificado): el foco pasó a **23 noches** y las 3
alertas comparables de MIROVA se reproducen **3/3**.

**Y NdC está entre los mejor alineados**: offset de 140 m, 3º de 11 (mediana de
la flota 607 m). O sea, aunque D17 resulte cierta, **NdC no es de los que se
beneficiarían** — su grilla ya coincide. Los que cambiarían son PCC,
Tupungatito y Planchón-Peteroa.

Implicación honesta para lo que estás mirando: la figura de NdC está en su mejor
estado y **no depende del resultado de F70**. Si el gráfico de NdC es el
entregable que importa ahora, esa parte ya está cerrada.
