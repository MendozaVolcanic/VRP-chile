# Bloque de arranque S131

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S130. Esa sesión aplicó las cuatro decisiones que
Nicolás tenía pendientes, refutó un A/B que llevaba dos sesiones abiertas, y dejó
otro corriendo.

Leé en este orden:
  1. tasks/BLOQUE_ARRANQUE_S131.md   (el bloque completo — esto es un resumen)
  2. docs/s130/PREREGISTRO_AB_D18.md (los criterios del A/B que quedó corriendo)
  3. docs/MIROVA_DIVERGENCES.md      (D18 y D17 tienen anotaciones nuevas)

═══════════════════════════════════════════════════════════════════
LO PRIMERO: EL A/B DE D18, QUE QUEDÓ CORRIENDO
═══════════════════════════════════════════════════════════════════

Run 33456630043 — seis volcanes × dos brazos, ventana 2026-05-29 a 08-24.

    gh run view 33456630043 --json status,conclusion
    gh run download 33456630043 --dir <scratchpad>/d18

⚠️ EL WORKFLOW NO COMMITEA (heredado del de S129). Artefactos, 14 días. Vienen como
`s130d18-<perfil>-<volcán>/`; hay que reordenarlos a `<dir>/<perfil>/<volcán>.json`
antes de leerlos.

LA LECTURA YA ESTÁ ESCRITA (A16): experiments/_s130_d18/veredicto_d18.py
Arranca por el CONTROL DE INSTRUMENTO: si los brazos no difieren en ningún record,
imprime INCONCLUSO y se detiene. No leas nada más si eso pasa.

QUÉ PREGUNTA. Coppola 2016a dice que el ROI1 es una CAJA de 5×5 km igual para todos;
el nuestro es un círculo de 3 a 20 km por volcán. El ROI1 decide qué umbrales rigen.

EL CRITERIO NO ES «CERO PÉRDIDAS» — acá se ESPERA perder detecciones, esa es la
dirección del cambio. La pregunta es cuáles. LA FIRMA QUE ARBITRA ES LA ESPACIAL:
si la caja recorta ARTEFACTO topográfico, el clúster se ACERCA al cráter en los
nevados; si recorta SEÑAL real, se pierden detecciones sin que la posición mejore.

NO ADOPTAR si: el recall cae >3 puntos y el offset no mejora · Lastarria pierde >20 %
(es el canario del cat-b: su offset N es el Lazufre, dato de campo, A84) · PCC
pierde >50 % (su lacolito es feature real de 707 km²).

ADOPTAR es decisión de Nicolás, no del A/B.

═══════════════════════════════════════════════════════════════════
LO QUE S130 CERRÓ — no reabrir (anti-A8)
═══════════════════════════════════════════════════════════════════

· EL A/B DE LOS FONDOS ESTÁ REFUTADO, y no por su resultado sino por su diseño.
  Los dos chunks completos (882 noches, 13.766 records) dieron las cuatro firmas
  IDÉNTICAS: `pool` no movió ninguna de las suyas. La causa no es el flag —los
  perfiles resuelven bien y los tres procesadores los consumen— sino que NO HAY
  SUSTRATO: el umbral K1 (NTI > −0,8) se cruza en el 0,09 % de las pasadas MODIS,
  0,12 % de V750 y 1,36 % de V375. Láscar 4,82 % es el único con material; Chaitén
  tiene CERO en 5.865 records. El A/B eligió cinco volcanes de los cuales cuatro no
  tenían sobre qué actuar.
  → GAP #A queda DOCUMENTADO Y DIMENSIONADO por decisión de Nicolás. Sigue siendo
    divergencia real de fidelidad literal; su alcance empírico es <0,1 % en MODIS.

· A81: la discrepancia 2.527 → 9.196 ERA EL DENOMINADOR. S120 metió el backfill de
  2025 y triplicó el corpus; 8.038 de los 9.196 son ANTERIORES al corte de S113 y la
  tasa está plana en 15-17 % mensual desde feb-2025. → A90 nueva.

· D18 NO CURA EL far→summit. Medido: el píxel que roba la etiqueta está a 22 km de
  mediana, ninguno dentro del ROI1 ni de la caja. Es ORTOGONAL. Eso cierra la única
  vía nueva que le quedaba a la brecha MODIS (A82 fue rebajada en S124 sólo por el
  hueco geométrico) — volver por la vía espectral es lo que A82 prohíbe.

· EL PISO VRP SE FUE, con el ciclo A45 completo y verificación: 0 noches
  MIROVA-confirmadas perdidas, VIIRS750 82,52 → 84,55 %, 582 records invisibles → 0.
  Dato que apareció: el piso de MODIS NUNCA actuó (0 de 11.717).

═══════════════════════════════════════════════════════════════════
LO QUE QUEDA MEDIDO Y SIN IMPLEMENTAR
═══════════════════════════════════════════════════════════════════

EL REMUESTREO — confirmado en VIIRS, no probado en MODIS
(docs/s130/GRADIENTE_CENITAL.md). El ratio nuestro/MIROVA cae de 0,740 cerca del
nadir a 0,253 más allá de 50° en VIIRS375 (n=2.767, monótono en 5 bins). Y el
CONTROL lo decide: MIROVA es PLANO (0,23-0,27) y lo nuestro cae 2,7×. VIIRS750
repite. En MODIS los bins no son monótonos y tienen 17-21 pares: no se puede afirmar.

⚠️ EL BRAZO FIEL ES BOW-TIE + REGRID EN ESE ORDEN. Coppola 2012 §3.2 pone el bow-tie
como paso (i); regridear sin de-solapar duplicaría píxeles calientes e inflaría la
magnitud en dirección CONTRARIA al error. Es cirugía de núcleo, no un flag — por eso
S130 lo dejó medido y no implementado a medias.

COROLARIO QUE CAMBIA CÓMO SE LEE D5: el sub-reporte global (0,73) NO ES PAREJO. Es
0,74 a nadir y 0,25 en oblicuo. Cualquier mediana sobre todos los ángulos promedia
dos regímenes.

═══════════════════════════════════════════════════════════════════
NÚMEROS QUE CAMBIARON — no citar los viejos
═══════════════════════════════════════════════════════════════════

  · far→summit: 9.196 hoy, no 2.527 (era otro corpus). 9.192 de ellos son MODIS =
    78,5 % de todos los records MODIS.
  · recall del dashboard vs noches-ALERTA MIROVA: MODIS 12,20 % · VIIRS750 84,55 %
    (era 82,52 con piso) · VIIRS375 93,93 %.
  · en MODIS el pipeline encuentra el cráter el 97,6 % de las veces y el dashboard
    cuenta 12,2 %: esa brecha es ETIQUETADO (A46), no detección.
  · gradiente VIIRS375 en 35-50°: 0,389, no 0,570 como decía el bloque de S130.
  · sustrato K1: MODIS 0,09 % · V750 0,12 % · V375 1,36 %.
  · el 42 % de las detecciones summit quedan fuera de la caja del paper.
  · suite: 1033 tests.

═══════════════════════════════════════════════════════════════════
REGLAS DE ESTA ETAPA
═══════════════════════════════════════════════════════════════════

  · A90 NUEVA — un conteo absoluto sobre un corpus que crece no es comparable
    consigo mismo entre sesiones, y falla EN SILENCIO. Registrá la proporción además
    del total, o la ventana junto al conteo. Antes de tratar como hallazgo la
    diferencia contra un informe viejo, RECONSTRUÍ el corpus que ese informe pudo
    ver. El corpus puede crecer HACIA ATRÁS, que es el caso que menos se sospecha.
  · ANTES DE GASTAR CI EN UN A/B, MEDÍ EL SUSTRATO — cuántas veces el mecanismo bajo
    prueba tiene OCASIÓN de actuar, estratificado por volcán. Se responde con un
    barrido de un diagnóstico ya persistido, en un minuto. No hacerlo costó, en
    S129-S130, dos chunks y más de cinco horas de CI para tres records de diferencia.
  · Toda sonda que juzgue al sistema necesita control de instrumento — y el control
    del gradiente cenital (mirar numerador y denominador por separado) fue lo que
    convirtió un ratio ambiguo en una conclusión.
  · A89 sigue vigente y me pasó a mí en esta sesión: usé 'MODIS'/'VIIRS750' donde
    `bucket()` devuelve 'modis'/'v750', y la tabla salió vacía.
  · Verificá flags leyendo `pipeline.profile`, NUNCA el YAML.
  · Los cambios de frontend se verifican en NAVEGADOR REAL (puerto 8091), y después
    en el sitio publicado.
  · Todo número sale de un script que lo persiste, y se registra en
    scripts/libro_de_cuentas.py CON SU DEFINICIÓN.
```

---

## Estado al cerrar S130

**Suite**: 1033 tests. **NRT**: sano. **Dashboard**: publicado y verificado en vivo —
las once tarjetas coinciden entre `index` y `mosaico`.

**PRs**: #569 a #578, todos mergeados. **Tags defensivos**: `pre-s130-quitar-piso-vrp`,
`pre-s130-d18-roi1-caja`.

**Corriendo**: run `33456630043` (A/B de D18).

### Lo que quedó probado

| hallazgo | cómo se probó |
|---|---|
| **El piso VRP no costaba nada quitarlo** | 0 de 1.218 noches MIROVA-confirmadas perdidas; 582 records invisibles → 0 |
| **El piso de MODIS nunca actuó** | 0 pisados de 11.717 records |
| **`auto_audit_weekly` era ciego al piso** | mide `primary_cluster.vrp_mw`; el piso escribe `record.vrp_mw` |
| **El A/B de los fondos no podía medir nada** | cuatro firmas idénticas + sustrato K1 del 0,09-1,36 % |
| **A81 era el denominador** | 8.038 de 9.196 anteriores a S113; backfill de S120 fechado en git |
| **D18 es ortogonal al far→summit** | el píxel culpable está a 22 km de mediana; ninguno dentro del ROI1 |
| **El sub-reporte es geométrico** | MIROVA plano con el ángulo, lo nuestro cayendo 2,7× |

### El patrón que ordena la sesión

**Medir si el mecanismo tiene ocasión de actuar cuesta un minuto y ahorra horas.** El
A/B de los fondos gastó cinco horas de CI para descubrir que sus flags no tenían
sustrato. La misma pregunta, hecha antes, habría costado un barrido de un diagnóstico
ya persistido.

Aplicada después, la lección rindió tres veces en la misma sesión: D18 pasó el control
antes de lanzarse, su hipótesis sobre el far→summit se refutó en cinco minutos en vez
de en un reproceso, y el gradiente cenital se convirtió en conclusión gracias a mirar
numerador y denominador por separado.
