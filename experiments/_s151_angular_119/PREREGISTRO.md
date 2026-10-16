# Tarea 1.19: pre-registro (escrito ANTES de correr el análisis)

Fecha: 2026-10-16. Sólo lectura sobre el repo.

## Fuentes de los ángulos (página renderizada a imagen, A95)

- `documentacion/VIIRS_Geolocation_ATBD_2014.pdf`, p. impresa 14 (§2.2.1.1) y p. 27 (§3.3.1.1), renderizadas en
  `pag/geo_35.png` y `pag/geo_48.png`: agregación 3:1 hasta ±31,589° de ángulo de BARRIDO, 2:1 hasta ±44,680°,
  1:1 hasta 56,063°.
- `documentacion/JPSS_ATBD_VIIRS_Imagery_RevE.pdf`, p. 21 (`pag/img_20.png`): mismo esquema (31,59° y 44,68°),
  altitud nominal 833 km.
- No hay en `documentacion/` un «VIIRS SDR User's Guide» (NOAA NESDIS 142). Los ángulos salen de los dos ATBD.

El OSF trae SatZen, cenit del sensor en el suelo, no ángulo de barrido. Conversión esférica
`sin θz = (R+h)/R · sin θs`, R = 6371 km, h = 833 km: **36,32°** y **52,66°** (con h = 824 km, 36,27° y 52,57°;
el borde del barrido, 56,063°, da 69,7°). Los límites en cenit quedan con ±0,1° de incertidumbre por altitud.

## Física esperada (antes de mirar)

Una fuente subpíxel reparte su exceso de radiancia MIR en el píxel nativo: ΔL · A_nativo es la cantidad que se
conserva. Al cruzar 36,32° hacia afuera, el píxel nativo pierde un tercio de su ancho a lo largo del barrido
(3 → 2 muestras), y al cruzar 52,66°, la mitad (2 → 1).

(i) OSF de MIROVA. Si MIROVA remuestrea a celdas de área fija y conserva la energía:
- **Npix** baja en el límite: factor ~0,67 en 36,32° y ~0,50 en 52,66° en el límite de fuente extensa; diluido
  hacia 1 cuando la mayoría de las detecciones son de 1 a 3 celdas.
- **VRP total**: continuo (sin salto), porque la energía se conserva.
- **VRP/Npix**: sube por el inverso del factor de Npix.
- Control nulo: las filas de 1 km (MODIS no agrega) no deben saltar en esos mismos ángulos de cenit; tampoco las
  de 375 m en ángulos placebo (p. ej. 30°, 44°, 60°), y la distribución nula de cada salto se mide barajando el
  SatZen dentro de cada volcán.
- Si en cambio Npix NO salta, MIROVA no está siguiendo la huella nativa (o la dilución por fuentes de 1 celda es
  total) y el OSF no da la firma.

(ii) Sintético. Fuente a 800 K con área fijada para VRP_verdadero = 1,0 MW y 3,0 MW
(a = VRP / (18,0 · (L_3,74(800) − L_3,74(263)))), fondo I04 263 K e I05 261 K con ruido gaussiano 0,5 K,
toda la energía de la fuente en un solo píxel nativo (sin PSF), geometría del píxel según el modelo esférico con
agregación 3/2/1 anclado en 375 m a nadir. Predicción para nuestro pipeline (área nadir fija):
VRP_nuestro / VRP_verdadero = 140.625 m² / A_nativo(θz): 1,0 a nadir, ~0,56 justo antes de 36,3°, ~0,83 justo
después, ~0,40 justo antes de 52,7°, ~0,79 justo después, ~0,25 en el borde. MIROVA, área correcta: plano en 1,0.
Si el detector agrega o pierde píxeles, la forma se aparta de esa curva y eso es lo que se mide.
