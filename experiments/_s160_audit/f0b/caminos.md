# caminos.md: por donde cada afirmacion podria estar mal (escrito antes de abrir ningun archivo citado)

Verificador F0b, S160. Solo conozco titulo, scripts y seccion de LISTA.md.

## F4-H2 "K1 casi no decide en Chile: la cota inferible desde la referencia es K1 >= -0,87 y no separa -0,8 de -0,7"
1. El instrumento mide otra cosa: la "cota inferible" puede salir del NTI maximo de NUESTRAS pasadas pareadas con alertas
   de MIROVA, no del NTI que vio MIROVA (otro granulo, otra geolocalizacion, otra banda). Un NTI nuestro no es el de MIROVA.
2. La referencia no trae NTI: MIROVA publica VRP y distancia, no NTI; inferir K1 exige reconstruir el NTI, lo que mete el
   pipeline propio como vara (circular).
3. Ventana: si la ventana no contiene alertas grandes (efusivas) con NTI sobre -0,8, "no separa" es falta de sustrato,
   no propiedad de K1 (A114/A130). Chile en 2026 casi no tiene lava expuesta.
4. Sensor: K1 depende del sensor (MODIS -0,8 Tabla 1; VIIRS 750 OSF -0,7 segun memoria). Mezclar sensores borra la cota.
5. Referencia tabla sola vs combinado: la cota puede cambiar si el OCR mete alertas que la tabla no tiene.
6. "Casi no decide" en produccion: con K (S153) el Test 1 integrado esta apagado (enable_test1_path false); si el Test 1
   por pixel no corre en produccion, K1 no decide por otra razon (codigo), no por la referencia. Leer el flag desde
   pipeline.profile, no del YAML.
7. Signo y direccion de la cota: K1 >= -0,87 como cota inferior podria estar invertido (un pixel alertado con NTI -0,87
   implica K1 <= -0,87 si fue alertado por Test 1, o nada si fue alertado por Tests 2/3).
8. Numero: -0,87 puede venir de un solo par (minimo), sensible a un outlier/pareo erroneo dentro de TOL_S.

## F4-H3 "El minimo de cumbre 0,003 es inerte en los tres sensores; lo que decide en la cumbre es 5 sigma y la caja"
1. Con K (S153) la conectiva es max: C1 y mu+C2 sigma deben cumplirse ambos; "inerte" significa que mu+C2 sigma siempre
   supera 0,003. Puede que el script haya medido bajo min (perfil viejo) donde C1 si decide (A103 dice C1 = 0,003 era el
   umbral efectivo en 70 casos bajo min).
2. "5 sigma" es el test de BT (apagado desde S40, D31) o C2 del dNTI? Confusion de variable posible.
3. "La caja": enable_roi1_box_paper puede estar apagado en produccion; si lo esta, la caja no decide nada hoy.
4. Inerte en un estrato (noche) pero no en dia (0,02) o en escena (0,010).
5. Ventana: inerte en la ventana medida, pero el fenomeno (sigma chico en fondo homogeneo) puede aparecer en otra epoca.
6. El script mide sobre records persistidos (diag_*) que fueron escritos con otro detector (A104: antes/despues de K).
7. Tres sensores: puede haber medido solo dos con datos.

## F4-H5 "El OSF v2.5 no puede dar umbrales de deteccion para ningun sensor: sus pisos son los filtros de Coppola 2026"
1. Lectura del paper en TEXTO en vez de RENDER (A95): Tabla 1 de Coppola 2026 p. 8.
2. Los "pisos" del OSF pueden ser a la vez filtro de agregacion y reflejo del umbral; "no puede dar" es mas fuerte que
   "no da directamente".
3. Puede que el OSF si contenga filas sub-piso para algun sensor (entonces no son filtro duro).
4. La afirmacion puede ya estar en A105 (YA RESUELTO/sabido); verificar si es novedad.
5. El codigo MATLAB del OSF (zm62w) podria dar umbrales de deteccion; "ningun sensor" puede ser falso para VIIRS 750.

## F4-H7 "K1 diurno: el codigo usa -0,5; la rama diurna (apagada) trae -0,6 de la Tabla 1 de MODIS; el informe S158 no lo registra"
1. El -0,5 puede leerse de otro lado (perfil, constante, sensor) que el que cito el auditor; trazar caller (A6/A89).
2. "Apagada": leer el flag desde pipeline.profile; puede estar encendida para un sensor.
3. La Tabla 1 de Coppola 2016a: el valor diurno de K1 MODIS puede no ser -0,6 (leer RENDER). Puede haber confusion
   entre K1 y C1 diurno (0,02) o entre NTI absoluto y K1.
4. Si MIR solo nocturno en produccion, K1 diurno no decide nada (gravedad 1), salvo VIIRS diurno en produccion (S151
   "alertas diurnas de MIROVA con sol").
5. "El informe S158 no lo registra": puede estar registrado en otra seccion/otro doc.
6. Puede estar ya corregido en el commit d516b9d8c.

## F4-H8 "Coppola 2025 cap. 11 Tabla 2 no es evidencia para VIIRS: solo trae el NTI de MODIS, atribuido a Wright 2002"
1. Leer en RENDER; la tabla puede tener mas filas (VIIRS) en otra pagina.
2. Quien la cita como evidencia para VIIRS: si nadie en el codigo/docs vigentes la usa para VIIRS, el hallazgo es de forma.
3. Atribucion a Wright 2002 puede ser al NTI (definicion) no al umbral.
4. Version del capitulo (2024 vs 2025) distinta.

## R2-17 "Las tres vistas del tablero coinciden hoy en efecto (0 diferencias sobre 74.811 records), con divergencias latentes en el texto"
1. El script compara las funciones extraidas por regex del HTML; si la extraccion falla o toma la misma funcion de un
   archivo para los tres, 0 diferencias es trivial (instrumento muerto). Necesita control positivo (mutar una vista).
2. Datos: 74.811 records puede ser del worktree (no SHA_MAIN) o de otra fecha; el corpus crece (A90).
3. "En efecto" segun que predicado: isValidDetection / mirovaEqVrp; diario.html no usa isValidDetection (A116).
4. Version del frontend: el commit de S158 vs d516b9d8c; el frontend pudo cambiar desde S158 (p. ej. #892).
5. Comparar tres vistas sobre los mismos records pero con parametros distintos (ventana temporal, inner_radius).
6. El script puede no correr hoy (rutas).

---
sha256 (del contenido anterior a este pie): 7cef7ab0aaf39c1818ab1274dcdfa0a9e107f2729374adf81be751e331278ce0
hora del servidor: Thu, 22 Oct 2026 04:20:49 GMT
