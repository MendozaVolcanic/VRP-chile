# Caminos por los que cada afirmación de S158 (lista F0a) podría estar mal

Escrito ANTES de abrir ningún archivo citado (ni los INFORME.md de S158 ni sus scripts). Sólo conozco los diez
títulos de LISTA.md, la memoria `reference_codigo_mirova_osf.md` y las reglas del proyecto. Hora del servidor al
empezar: Thu, 22 Oct 2026 04:07:02 GMT. Commit auditado: d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956.

Vara que uso para todo lo que diga «MIROVA hace X» en VIIRS 750: los dos `.m` de OSF zm62w, copia en
`experiments/_s158_d17_diseno/osf_codigo_mirova/` (verificar hash contra `osf_metadatos_codigo.txt` de f6 o contra
lo que haya en `_s159/o1/o2_paquete/`). Para MODIS y VIIRS 375 no hay código: todo lo que se extrapole es SOSPECHA.

## F1-H4. Fuera de la cumbre el mínimo de MIROVA en NTI es 0,02 (0,0225 en nuestras unidades) y decide en 3 de cada 4 pasadas; el nuestro (0,01) decide en 6 %

1. El «0,02» puede ser un umbral sobre otra variable (dETI, dNTI con otra media, NTI absoluto) y no sobre el mismo
   diferencial que nuestro C1 = 0,010: comparar unidad por unidad en el `.m`.
2. El factor 0,0225 / 0,02 = 1,125 implica una conversión de unidades (¿9/8? ¿media 3x3 con central contra 8 vecinos?).
   Si la conversión está mal, el «decide» cambia de signo.
3. «Decide» depende de la conectiva: con `max` (producción desde S153) el piso decide cuando `C1 > μ + C2σ`. La
   fracción «3 de 4» puede estar medida con σ nuestro, no con el σ que calcula el `.m` (segundo pase que recalcula,
   3x3 con central, fondo sin recorte). Con otro σ, el reparto cambia.
4. La ventana y el denominador: ¿pasadas de qué volcanes, qué sensor (sólo V750, o también V375/MODIS por traslado),
   qué fechas? Si mezcla pre y post #535 o pre y post K (A104), el porcentaje no es de un detector.
5. El 6 % nuestro puede estar medido sobre records persistidos (que sólo existen cuando hubo detección) y no sobre
   pasadas: sesgo de selección.
6. Puede estar YA RESUELTO: la adopción de K (S153) o la ola 1 de S159 (grilla 750, port del `.m`) pudieron cambiar
   el mínimo fuera de la cumbre en `mirova_equivalent.yaml`. Leer `pipeline.profile` del commit, no el YAML.
7. El `.m` puede aplicar el 0,02 sólo en el segundo pase, o sólo en ROI2, y el rótulo ROI1/ROI2 está invertido en los
   comentarios (memoria): el auditor pudo leer el rótulo y no la matriz.

## F1-H6. Lo publicado es un cúmulo con modo de un píxel; MIROVA suma todos los alertados de la escena

1. «Lo publicado» es el predicado del tablero con node (A97): si el auditor lo reconstruyó a mano, el «modo de un
   píxel» puede ser del `primary_cluster` y no de lo que publica `mirovaEqVrp` (en V375 publica `f5_core_vrp_mw`,
   recorte al núcleo; en V750 y MODIS `pc.vrp_mw`).
2. «MIROVA suma todos los alertados de la escena» vale para el `.m` de V750 (memoria: publica la unión). Para V375
   y MODIS no hay código: Campus 2022 p. 7 lo dice en prosa. Si el hallazgo lo extiende a los tres sensores, esa parte
   es por traslado.
3. El `.m` puede sumar todos los alertados pero el producto publicado (latest.php, TIF) puede pasar por DBSCAN o
   selección de cúmulo en otra etapa que no está en el `.m` (el OSF v2.5 usa DBSCAN, A105). Lo que el `.m` suma y lo que
   la web publica pueden diferir.
4. El modo de un píxel puede ser artefacto de la ventana (post #535, post K) o del volcán dominante (Láscar).
5. Posible duplicado con D32 / A10 (ya catalogado en S147): entonces no es nuevo, es la misma divergencia ya conocida.
6. Que el cúmulo sea de un píxel no implica diferencia de magnitud si los alertados adicionales de MIROVA tienen VRP
   negativo o cero (ver F6-4): la suma puede no cambiar.

## F1-H8. Diferencias de entrada sin sustrato medible desde los records

1. Es un hallazgo de «no se puede medir»: la pregunta es si hoy sí se puede. Campos nuevos en records (S159 ola 1,
   `diag_*`, `f5_core_vrp_mw`, geo_class) pueden dar el sustrato que S158 no tenía.
2. «Entrada» puede ser L1B (radiancias, geolocación, bow tie, remuestreo D17) y eso nunca está en el record: entonces
   el hallazgo es verdadero por construcción y de gravedad 1, salvo que alguien lo use para cerrar un frente.
3. Puede estar YA RESUELTO si el oráculo de `_s158_oraculo_mirova` o el port a Octave de S159 compara entradas
   directamente (`.mat` de ejemplo).
4. Riesgo de que el auditor haya concluido «sin sustrato» por un grep que dio cero (A89): el campo puede existir con
   otro nombre.

## F1-H9. Un record sin detección vale 0,0 MW; MIROVA lo declara NaN y advierte que no es emisión cero

1. Qué hace el `.m` exactamente: NaN de salida, o error (F6-5 dice que probablemente FALLA, lo que contradice
   «declara NaN»). Los dos hallazgos no pueden ser ciertos a la vez en la misma función: leer el `.m`.
2. En nuestros datos: ¿`vrp_mw = 0.0` se escribe cuando no hubo detección, o no se escribe record? Si `store.py` no
   persiste records sin detección, el 0,0 puede ser otra cosa (cúmulo rechazado por geofencing, piso de VRP, D9).
3. El tablero: `mirovaEqVrp` puede ya tratar 0,0 como «sin dato» (no lo grafica). Entonces la gravedad para el
   operador es menor que para una métrica.
4. Métricas: la razón ours/mirova y las series de `diario.html` pueden promediar ceros como emisiones: ahí sí mueve
   algo. Buscar dónde se promedia `vrp_mw` sin filtrar.
5. El OSF v2.5 (CSV) y latest.php pueden publicar 0 o vacío, no NaN: la vara «MIROVA declara NaN» puede ser del
   código y no del producto.

## F6-3. Los umbrales de detección de VIIRS 750 no tienen contraste con ningún resultado publicado

1. Hallazgo de ausencia: «ningún resultado publicado» puede ser falso si Campus 2022 (Sensors) o Coppola 2026
   (Sci Data) traen tablas con los umbrales de V750 (Tabla 1 del OSF v2.5 trae umbrales VRP por sensor, A105).
   Distinguir umbrales de DETECCIÓN (K1, C1, C2) de umbrales de VRP mínimo.
2. El ejemplo `.mat` del OSF es un resultado publicado: si corre y da los píxeles alertados, es un contraste. S159
   ola 1 validó el port contra Octave: eso ya es contraste. Posible YA RESUELTO.
3. BIBLIOGRAPHY_SYNTHESIS tiene tabla canónica V750; si contradice el `.m` (K1 -0,8 vs -0,7), el contraste existe y
   es negativo.

## F6-4. El código no recorta ΔL, pero MIROVA nunca publica una alerta con VRP nulo o negativo

1. ΔL negativo puede ser imposible por construcción si el píxel alertado ya superó al fondo en la misma banda que
   se usa para el VRP (dNTI alto no garantiza L_MIR > L_bg del VRP si el fondo del VRP es el `fillmissing2` y no el
   del detector). Leer con qué fondo se resta.
2. «Nunca publica» es un conteo sobre el CSV del scraper: el scraper puede filtrar ceros o negativos (loader-filtro,
   A139), o el OCR no lee «0». Hay que mirar la tabla sola y el combinado, y la cantidad de filas con VRP = 0.
3. El producto web puede redondear a 2 decimales: un VRP de 0,004 sale «0.00» y no es nulo. Ver F6 M16 «escalón».
4. Puede haber un filtro en la etapa que no está en el `.m` (DBSCAN / umbral VRP mínimo de Tabla 1 del Sci Data).
5. Nuestro código: ¿recortamos ΔL a 0? Si sí y MIROVA no, divergencia nuestra; si no, somos iguales.

## F6-5. La función de VRP probablemente falla, en vez de devolver NaN, cuando la detección rechazó la escena

1. «Probablemente» = no se corrió. Se puede correr en Octave (S159 lo tiene instalado, `prueba_o2_en_octave`): con
   una máscara vacía, ¿error o NaN? Eso lo decide.
2. Octave y MATLAB difieren en índices vacíos (`max([])`, `[]` en operaciones): un error en Octave no prueba error en
   MATLAB. Declarar con qué intérprete.
3. Contradice F1-H9 («declara NaN»): uno de los dos lee otra rama del código.
4. Si el `.m` de detección devuelve antes (sin llamar al VRP) cuando no hay alertados, la pregunta es vacía.

## F6-6. El README describe otro empaquetado que el depositado

1. Hallazgo de forma. Caminos: el README puede describir una versión posterior (OSF logs: ¿hubo actualización
   después del 2026-07-24?). Ver `osf_logs_p1.json` y, con una llamada, la API de OSF si el presupuesto lo permite.
2. Puede ser que nuestra copia esté incompleta (faltó bajar una carpeta) y no que el README esté mal.

## F6-7. Algunos comentarios afirman efectos que el código no tiene

1. Forma. Confirmar cada comentario contra la línea. El riesgo real es que ALGUIEN del proyecto lea el comentario y
   lo adopte como «MIROVA hace X» (el rótulo ROI1/ROI2 invertido ya está en memoria): verificar que el informe de
   S158 y la memoria usen la matriz, no el comentario.
2. Alguna de las afirmaciones del comentario puede ser cierta por otra línea (p. ej. un efecto que se logra en el
   segundo pase).

## F6-8. La dilatación del fondo también agranda los huecos que ya trae M13, y los TIF de MIROVA traen huecos

1. Los huecos de M13 pueden ser bow tie (borde de escena) o fill values de calidad: la dilatación con `imdilate`
   sobre NaN propaga NaN sólo si la operación no los ignora; `fillmissing2` después los rellena. Si rellena, el
   «agranda» es transitorio y no llega al VRP.
2. «Los TIF traen huecos» puede ser de los TIF geográficos (EPSG:4326, remuestreados) y no del producto UTM de 8
   adquisiciones (A106): huecos de remuestreo, no del algoritmo.
3. Los TIF están congelados desde el 2026-09-22 (memoria): cualquier conteo de TIF después de esa fecha mide la
   misma imagen repetida.
4. Relevancia para nosotros: ¿nuestro fondo también dilata? Si no, el hallazgo describe a MIROVA y no mueve nada
   nuestro.

## Caminos comunes a los diez

- La afirmación puede estar YA RESUELTA o medida en `_s159/` o en f1a, f2, f3, f4, v2, v3 de esta auditoría: buscar el
  ID antes de rehacer.
- Los datos de S158 eran de la rama `s158-d17-diseno`; los de hoy son SHA_MAIN d516b9d8c. Un conteo puede haber
  cambiado por reproceso (histórico reemplazado por K, #883/#884) sin que la afirmación cambie.
- Script que corre no es script que mide lo que dice (A111 b): leer qué campo lee.
- Gravedad: 5 sólo si mueve lo que `correr_node` publica hoy; 4 si mueve una métrica usada para decidir (regla de
  adopción de K, D25); 3 si mueve un A/B pendiente; 2 exploratorio; 1 forma.

---
Sello: sha256 del contenido anterior a esta línea = e7e898e5aa2c3188e0190af8f02a4266a23c3d60f752def353583ef71b6ab6b1
Hora del servidor al sellar: Date: Thu, 22 Oct 2026 04:08:18 GMT
