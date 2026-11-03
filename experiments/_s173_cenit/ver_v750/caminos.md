# caminos.md: por donde podria estar mal cada afirmacion del auditor de VIIRS 750 (Chillan, cenit)

Escrito ANTES de abrir ningun script ni salida del auditor. Solo conozco: el enunciado de la tarea
(afirmaciones 1 a 6), los titulos y gravedades de hallazgos.csv (CV750-01 a 05), el commit de su
copia repo/ (5de08ebf62d1ea092c485c0a030f323f2cbdcf2a = origin/main de hoy) y la lista de archivos
de su carpeta.

## Afirmacion 1: 47 pasadas nocturnas de Chillan en las grillas de s159_n; 28 pareadas con alerta de MIROVA (7 bajo 30, 21 a 30 o mas)

- El «pareo» no es por pasada (mismo minuto de Fecha_Satelite_UTC) sino por noche o por hora redondeada: entonces 28 puede contar dos veces una pasada o juntar pasadas distintas.
- Tolerancia de pareo demasiado ancha (p. ej. +-30 min) que junta la pasada de SNPP con la de NOAA-20 o NOAA-21 (tres plataformas VIIRS, pasadas separadas ~50 min).
- Ventana temporal cruzando hitos de A119: referencia incompleta antes de marzo-2026 (CONS) y OCR mal calibrado hasta 2026-06-11; si la ventana entra ahi, los «no pareados» pueden ser huecos de la referencia, no ausencia de alerta.
- Ventana cruzando #535 (2026-08-28 23:00 UTC, A104): dos regimenes de mascara de nube mezclados.
- «Alerta de MIROVA» tomada del CSV sin la regla SN (VIIRS 375 <= 0,05 MW cuenta como nada) o tomando filas de VIIRS 375 o MODIS como si fueran de VIIRS 750 (el sensor del CSV puede venir con otro nombre: «VIIRS 750», «VIIRS-M», etc.).
- Nombre del volcan con variante («Nevados de Chillan», «NevadosdeChillan», «Chillan») que pierde filas (A14).
- «Nocturnas» definido por hora UTC fija y no por elevacion solar; en Chile, invierno, 23 UTC puede ser aun de dia.
- El 47 es el numero de archivos de grilla, no de pasadas: una pasada puede tener dos grillas (dos granulos) o una grilla puede estar vacia.
- Las grillas de s159_n son de una corrida de GitHub Actions (run_396...): si la corrida no termino o un chunk fallo (A108), faltan pasadas y 47 es cobertura parcial no declarada.
- Los 7 y 21 por tramo de cenit dependen de QUE cenit: ver afirmacion 3.

## Afirmacion 2: controles (identidad 47/47; brazo O = runner 47/47; control positivo 29/29; referencia corrida un dia 0/47)

- «Identidad 47/47» puede comparar el brazo consigo mismo por construccion (misma funcion, mismos datos): no puede fallar, no es control.
- «Brazo O = runner 47/47»: si compara contra el record del runner leido del MISMO archivo del que sale el brazo O, o compara con tolerancia tan ancha que todo pasa; o compara un campo que ambos derivan del mismo origen (A109).
- «Control positivo 29/29»: 29 no es 47, que paso con las otras 18? Si el control positivo solo se aplica a las pasadas con VRP > 0, el control no cubre justo el estrato donde el auditor dice que los ceros esconden la caida (afirmacion 6).
- «Referencia corrida un dia 0/47»: si el pareo es por minuto exacto, correr un dia da 0 trivialmente aun con pareo roto por otro motivo (p. ej. zona horaria): el placebo no prueba que el pareo este bien, solo que es sensible al dia. Un placebo mejor: correr 50 min (otra plataforma) o barajar los VRP de la referencia.
- Los controles pueden estar corridos sobre otra ventana o subconjunto que las mediciones principales.

## Afirmacion 3: K reproduce la caida (0,910 bajo 30, 0,285 sobre 30; Spearman -0,864 fuera del barajado)

- El cenit no es el del volcan en esa pasada: puede ser el del pixel pico, el del centro de la grilla, el del granulo (medio), o estar leido de la referencia de MIROVA y no del record. Si el record no guarda el cenit, de donde salio?
- Signo o unidades del cenit (grados vs radianes; «sensor zenith» vs «solar zenith»: el solar de noche es > 90 y no sirve).
- Con n = 7 bajo 30 y n = 21 arriba, la mediana del tramo bajo descansa en 7 numeros: una sola pasada mueve la mediana. Poco n disfrazado.
- La razon = VRP nuestro / VRP MIROVA: el «VRP nuestro» puede ser el campo equivocado (record.vrp_mw con tope D9 o suma de escena, en vez de pc.vrp_mw; para V750 el tablero publica pc.vrp_mw: A10). El «VRP MIROVA» puede ser el OCR y no la tabla (S159: la tabla es mas creible).
- Spearman «fuera del barajado»: el barajado debe ser del cenit DENTRO del sensor y con las mismas 28 pasadas; si baraja sobre 47 o sobre otro conjunto, el nulo no es el de la medicion. 200 barajados con semilla 173: un p < 1/200 solo dice «ninguno de 200», hay que ver el rango del nulo.
- Spearman sobre 28 puntos con -0,864 es muy fuerte: posible que la razon y el cenit compartan una variable (p. ej. MIROVA tenga VRP constante o el VRP nuestro sea cero en las oblicuas y la razon sea 0 en bloque: el cero en bloque crea rango empatado y Spearman se infla). Ceros mal tratados.
- Log de la razon con ceros: log(0) = -inf; si se toman medianas de log, los ceros quedan fuera o dominan segun el tratamiento.
- «K» puede no ser el detector de produccion: si el brazo K esta reconstruido en la grilla (s159_n) y no en el granulo nativo, lo que reproduce la caida es «K en la grilla», no K de produccion (cuya salida es data/mirova_equivalent/). Comprobar que el VRP de K en la grilla coincide con el record del runner.

## Afirmacion 4: en la grilla, el fondo de anillo de K es la unica pieza que reproduce la caida (0,791 / 0,373; Spearman -0,486; fuera en 12 de 12 replicas sacando una noche); todas las demas piezas de K juntas dejan la pendiente plana (+0,061)

- El brazo «fondo de anillo» puede cambiar mas de una cosa (p. ej. fondo Y la compuerta que depende del fondo, o fondo Y la mascara de nube): atribucion contaminada (A110, A118).
- Las «demas piezas juntas» pueden no ser las demas: si el brazo que las junta omite una (remuestreo D17 no se puede ablar dentro de la grilla porque la grilla YA ES el remuestreo), la «pendiente plana» prueba poco sobre el area.
- Spearman -0,486 con n = 28: p ~ 0,009; «fuera del barajado» con 200 permutaciones. Si una pasada domina (jackknife 12 de 12 «sacando una noche»: por que 12 y no 28? 12 noches distintas? si hay 28 pasadas en 12 noches, hay pasadas de la misma noche correlacionadas y el jackknife por pasada subestima).
- 0,791 / 0,373: la mediana del tramo < 30 sigue en 7 puntos.
- La pendiente +0,061: pendiente de que contra que (log razon vs cenit en grados? por 10 grados?). Sin unidades no se compara con la de K.
- Que el fondo de anillo «reproduzca» la caida no implica que la CAUSE en produccion: si en la grilla el anillo de K toma pixeles que en el granulo nativo no existen (celdas vacias o interpoladas por el remuestreo), el efecto es del remuestreo visto a traves del anillo.
- Los ceros: si el brazo fondo-anillo da VRP negativo o cero en oblicuas (CV750-04 lo sugiere), y la razon se calcula con esos ceros como 0 (no como NaN), el Spearman cae por bloque de ceros. Dependencia del tratamiento del cero.
- El brazo «fondo de anillo» en la grilla puede usar un radio de anillo en celdas que no equivale al de K en pixeles nativos.

## Afirmacion 5: en el granulo nativo con fondo y suma de MIROVA (brazo F), queda cerca de la mitad logaritmica de la caida (-0,662); que eso sea area/remuestreo es SOSPECHA

- «Mitad logaritmica»: mitad de que? log(0,285/0,910) = -1,16; la mitad seria -0,58; -0,662 no es la mitad, hay que ver la definicion.
- El brazo F puede no estar en el granulo nativo sino en la grilla con otro fondo; o puede usar el area nadir fija de K (A66/A67) y entonces lo que queda no es «area».
- Si el brazo F corre con la suma de todos los pixeles alertados (MIROVA suma todo, A10 rebajada) pero con la deteccion de K, la suma depende de la deteccion que a su vez depende del cenit (bow-tie, pixeles mas grandes al borde: menos pixeles alertados, D25).
- n del brazo F puede ser menor que 28 (pasadas donde F da 0 excluidas): poco n o seleccion (afirmacion 6 aplicada a F).
- Cenit en el granulo nativo: el pixel del volcan en la grilla y en el granulo pueden tener cenit distinto (centro de grilla vs pixel nativo).

## Afirmacion 6: medir la razon solo donde el brazo da VRP positivo esconde la caida

- Es una afirmacion sobre el instrumento: puede estar bien pero depender de como se tratan los ceros en el OTRO sentido: si los VRP negativos del fondo de anillo se cuentan como 0 y entran como razon 0, la caida «aparece» por construccion (una razon 0 no es una medicion de magnitud, es una no-deteccion). Entonces lo que esconde o muestra la caida es una decision de tratamiento, y las dos lecturas deben reportarse.
- Si las 6 pasadas con VRP negativo son todas oblicuas, hay que ver si MIROVA las alerto con VRP alto (entonces es perdida) o bajo (entonces es ruido). Y si el VRP negativo viene de un fondo mal medido (anillo con nube), no del cenit.
- La magnitud negativa no existe en produccion (el pipeline la pone en 0 o la descarta): comparar el brazo con negativos contra MIROVA que solo publica positivos compara poblaciones distintas.

## Caminos transversales (aplican a todas)

- La copia repo/ (git archive de 5de08ebf) puede no ser el codigo que produjo las grillas de s159_n (corridas de un run anterior, con otro commit): comparar el commit de la corrida con el de la copia.
- Los helpers de src/s162 y src/s172 son de otras sesiones: pueden haber envejecido respecto al detector K de hoy (flags, conectiva max, banda, umbrales).
- El cenit, el pareo o la razon pueden venir de un helper del auditor que lea un CSV intermedio de otra sesion (s172) en vez de los records de hoy.
- Las salidas (s0X_salida.txt) pueden no corresponder a la version final de los scripts (editado despues de correr).
- La referencia MIROVA local puede estar atrasada respecto al remoto (regla 5 del mapa): pasadas de octubre-noviembre sin filas aun.
- Flags leidos del YAML en vez de pipeline.profile (A89).
- Disco: D: con 4,7 GB; si un script del auditor escribe en D:, al re-correrlo puedo llenar el disco.

## Como pienso medir por otro camino

1. Pareo propio por pasada desde data/mirova_equivalent/Nevados_de_Chillan (o el nombre que tenga) y los CSV de referencia, sin helpers del auditor: contar pasadas nocturnas VIIRS 750, alertas pareadas al minuto, por tramo de cenit (cenit del record si existe).
2. Comprobar de donde sale el cenit (campo del record) y si es el del volcan.
3. Re-correr s01 a s04 copiados a mi carpeta (uno a la vez), comparar salidas con las del auditor.
4. Spearman propio con dos tratamientos del cero (NaN y 0) y con jackknife por noche.
5. Placebo propio: correr la referencia 50 minutos y barajar VRP de la referencia.

---
sha256 (antes de esta linea): 8b9d509e61721ae31d52ddb2bfb185eb661eba7c47a6d4667e6b99a53e304706
hora del servidor (gh api, header Date): Tue, 03 Nov 2026 00:57:27 GMT
