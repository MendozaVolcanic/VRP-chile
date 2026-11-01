# Caminos por los que cada afirmacion podria estar mal (escrito antes de abrir archivos citados)

## 180 (D18 S130: Test 1 encendido + segundo pase sin mascara)
- C180.1 El codigo de la rama 35572961810 (S146/S148) no es el codigo que corrio el A/B de S130: el run de S130 pudo usar otro commit, donde el segundo pase si recibia la caja o no existia la recaptura.
- C180.2 El Test 1 integrado podia estar apagado en el perfil del A/B de S130 (perfil propio con enable_test1_path false); el flag se lee de pipeline.profile, no del YAML de produccion.
- C180.3 R8 (segundo pase sin caja) puede no deshacer el efecto si en S130 la caja recortaba antes del segundo pase la semilla (la recaptura parte de pixeles del primer pase).
- C180.4 El veredicto NO ADOPTAR de S130 pudo apoyarse en otra metrica (magnitud, posicion) que el Test 1 no satura.
- C180.5 r8_consumidores.py puede contar por subcadena (A92) y dar falso positivo de "consumidor sin caja".
- C180.6 El frente puede no estar cerrado hoy (S151 lo reabre con prereg caja sobre K); si esta abierto la gravedad 4 no aplica.
- C180.7 La linea 1313 puede no corresponder en esa rama.

## 181 (conectiva S148 CONFIRMADA con evaluador INDECIDIBLE)
- C181.1 El evaluador reusado puede imprimir INDECIDIBLE por una regla que el pre-registro de S147 declaro no aplicable al brazo F (el pre-registro pudo fijar otro criterio de decision).
- C181.2 Los datos que bajo el auditor (D:/.../f1b/s148) pueden no ser los del run 35548121381 completos (artefacto parcial, otro brazo) -> 133 vs 137.
- C181.3 La referencia congelada de hoy no es la de S148: recall 133 vs 137 puede ser cambio de referencia (tabla pierde filas), no del evaluador.
- C181.4 El documento S148 puede decir "CONFIRMADA" sobre otra cosa (el mecanismo) y no sobre la adopcion; la adopcion real pudo ser S153 (K) con su propia regla.
- C181.5 Que la conectiva max este en produccion hoy no depende de S148 sino de REGLA_ADOPCION S151/S153; entonces gravedad 4 vs 5 cambia.
- C181.6 El control positivo "calibrado para produccion con Test 1" puede ser correcto si el evaluador lo ajusta segun brazo.

## 182 (D22/D25 S143 ventana cruza #535)
- C182.1 La ventana de los datos del run puede no ser la del parametros.json (el run pudo correr otra ventana).
- C182.2 #535 (2026-08-28 23:00) cae dentro de 2026-06-01..2026-08-31 solo por 3 dias: el peso del tramo post-535 puede ser despreciable; la falla de R10 puede ser literal sin efecto.
- C182.3 El Test 1 podia estar apagado en los brazos de S143.
- C182.4 D22 puede no estar cerrada hoy solo por S143 (S150 la rehizo sobre max, y S153 K).
- C182.5 grep 535 = 0 no prueba nada si el evaluador recibe la ventana partida de otro lado.
- C182.6 Los hitos de referencia (OCR mal calibrado hasta 2026-06-11, sin distancia hasta 06-13) pueden no afectar si el evaluador usa solo la tabla.

## 188 (diurno: G1 empata con p95; W4 cruza #535)
- C188.1 El empate puede ser de redondeo de impresion (4 decimales) y no empate real; la regla puede ser >= o >.
- C188.2 W4 puede no cruzar #535 (fechas).
- C188.3 La salida W2_W6_s154 puede no ser la que decidio.

## 189 (probes MxD03 ventana cruza #535, artefactos en %TEMP%)
- C189.1 MODIS no depende de #535 (la mascara de nube de 260 K afecta a que sensores?). Si #535 solo afecta VIIRS, cruzar es inocuo para MxD03 (MODIS).
- C189.2 Los artefactos pueden estar commiteados en el repo (no solo %TEMP%).
- C189.3 La ventana real puede ser otra.

## Celdas FALLA (general)
- CF.1 Fila R9 (saturacion por Test 1): FALLA solo si el Test 1 estaba encendido en el brazo control Y podia actuar sobre la metrica (publicacion VIIRS en negativos). Si la metrica es magnitud, posicion o MODIS sin Test 1, es literal sin efecto.
- CF.2 Fila R10 (regimen #535): FALLA solo si la ventana de los DATOS cruza 2026-08-28 23:00 UTC y el sensor esta afectado.
- CF.3 Fila R14 (referencia): el instrumento pudo informar tabla sola y combinado aunque el auditor no lo encontro (otro archivo).
- CF.4 Fila R1 (pre-registro): el pre-registro pudo existir con fecha/commit anterior al resultado en otro archivo.
- CF.5 Fila R16 (nombre): falla de forma, gravedad 1.
- CF.6 La rubrica R1-R17 que uso el auditor puede no ser la del plan (R7 reemplazada por 11.2b).

---
sha256 del contenido anterior a esta linea: 4978bf466b59f14a46eacc3d3fd83f3b39b2c440118a491fafbdf23e890e5490
Hora del servidor (header Date de api.github.com): Thu, 22 Oct 2026 04:30:40 GMT
