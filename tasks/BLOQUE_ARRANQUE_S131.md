# Bloque de arranque S131

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S130. Esa sesión aplicó las cuatro decisiones que
Nicolás tenía pendientes y corrió DOS A/B hasta el veredicto: los dos dieron
NO ADOPTAR, por razones distintas y ambas instructivas.

Leé en este orden:
  1. tasks/BLOQUE_ARRANQUE_S131.md   (el bloque completo — esto es un resumen)
  2. docs/s130/VEREDICTO_AB_D18.md   (el A/B que se cerró, y por qué erré 50×)
  3. docs/s130/GRADIENTE_CENITAL.md  (el frente que queda: el remuestreo)
  4. docs/MIROVA_DIVERGENCES.md      (D18 y D17 tienen anotaciones nuevas)

═══════════════════════════════════════════════════════════════════
NO HAY NADA CORRIENDO. S130 cerró sus dos A/B.
═══════════════════════════════════════════════════════════════════

EL A/B DE D18 SE CORRIÓ Y SE LEYÓ: NO ADOPTAR (docs/s130/VEREDICTO_AB_D18.md).
Ni daño ni beneficio. El control pasó —366 de 5.551 records cambiaron, PCC 17,98 %—
pero la caja da MÁS en 166 y MENOS en 200: redistribuye, no recorta.

  · ningún límite de no-adopción se cruza: Lastarria 0,0 %, PCC 0,8 %, CERO noches
    MIROVA-confirmadas perdidas. La caja NO destruye cat-b.
  · el criterio de adopción tampoco: el offset debía bajar en los tres nevados y
    Villarrica SUBE 1 m sobre 2,63 km. Sólo se mueve la paridad, +0,040 en PCC y
    +0,020 en Copahue, nulo en los otros cuatro.

⚠️ LA PREDICCIÓN PREVIA ERRÓ POR 50×. Se había medido «42 % de las detecciones summit
en riesgo» y lo que se pierde es 0-0,8 %. El error fue de QUÉ SE CONTABA: dónde cae
el clúster, no si la detección SOBREVIVE al umbral estricto. Casi todas sobreviven.

EL HALLAZGO REAL, más útil que el veredicto: EL UMBRAL LAXO DEL ROI1 CASI NUNCA ES LO
QUE DECIDE. Las detecciones pasan con margen como para no depender de N·σ = 5 vs 10.
La diferenciación summit/scene es fiel al paper en sus valores y casi INERTE en la
práctica — por eso Llaima, Villarrica y Láscar, con círculos de 3,1× el área del
paper, no cambian NADA.

D18 sigue ABIERTA como divergencia de fidelidad literal; lo que cambió es su
PRIORIDAD. El flag queda OFF en el código con sus 7 tests.

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
  · el 42 % de las detecciones summit tienen su clúster fuera de la caja del paper
    — ⚠️ pero eso NO es lo que se pierde: el A/B midió 0-0,8 %. Contar el ámbito de
    un mecanismo sobrestima cuánto DECIDE.
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

**PRs**: #569 a #580, todos mergeados. **Tags defensivos**: `pre-s130-quitar-piso-vrp`,
`pre-s130-d18-roi1-caja`.

**Nada corriendo**: los dos A/B de la sesión llegaron a veredicto.

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
| **La caja del paper casi no cambia nada** | 0-0,8 % de detecciones perdidas, 0 noches MIROVA; el umbral laxo del ROI1 casi nunca decide |

### El patrón que ordena la sesión

**Medir si el mecanismo tiene ocasión de actuar cuesta un minuto y ahorra horas.** El
A/B de los fondos gastó cinco horas de CI para descubrir que sus flags no tenían
sustrato. La misma pregunta, hecha antes, habría costado un barrido de un diagnóstico
ya persistido.

Aplicada después, la lección rindió tres veces en la misma sesión: D18 pasó el control
antes de lanzarse, su hipótesis sobre el far→summit se refutó en cinco minutos en vez
de en un reproceso, y el gradiente cenital se convirtió en conclusión gracias a mirar
numerador y denominador por separado.

**Y el A/B de D18 agregó la otra mitad de la lección.** Ahí el sustrato sobraba —6,59 %
de los records cambiaron— y el A/B salió vacío igual, porque el mecanismo **no era el
que decidía**. Son dos formas distintas de que un experimento no mida nada, y sólo la
primera se detecta contando ocurrencias. Para un A/B de umbrales, la pregunta correcta
no es «¿cuántos casos caen bajo esta regla?» sino **«¿cuántos están lo bastante cerca
del umbral como para que cambiarlo los mueva?»**.
