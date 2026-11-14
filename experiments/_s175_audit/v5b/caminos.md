# caminos.md: por donde podria estar mal cada afirmacion (V5B, S175)

Escrito ANTES de abrir ningun archivo citado. Solo conozco el titulo, la cita y la gravedad de cada
afirmacion, tal como vienen en el prompt v5b.txt.

## Comunes a las cinco (el instrumento: lamina PNG Latest10NTI como vara de posicion)

C1. Sobreajuste: la regla de recorte/georreferencia del panel se ajusto mirando los mismos casos con
    TIF con que luego se valida (4 casos). Hay que ver si un parametro (margen, tamano de panel,
    centro, escala km/pixel) fue elegido por resultado.
C2. Nulo ausente: una posicion cualquiera cae a 0 o 1 celda de la mancha porque el panel es chico y
    los puntos que se comparan se concentran cerca del centro. Medir con posicion placebo: otra
    pasada, otro volcan, otro punto del mismo panel, permutacion.
C3. Denominador de validacion minusculo (4 casos), no estratificado por sensor: valida VIIRS375 y se
    usa en VIIRS750 y MODIS.
C4. Resolucion: una celda del panel vale segun sensor 375 m, 750 m, 1 km. La lamina puede estar
    remuestreada, interpolada, con un marco o rotulos. Una distancia de "1,0 km" puede ser 1 a 3 celdas:
    no resolvible frente al error de georreferencia.
C5. Proyeccion: el panel puede estar en UTM o lat/lon; la grilla puede estar orientada distinto
    (S144/A106 dice que los TIF cambiaron de EPSG). Centro del panel puede ser mirova_center o vent.
C6. El "pixel mas claro" o "la mancha" de la lamina no es el pixel alertado: paleta, saturacion,
    autoescala por panel; el NTI maximo no es el VRP maximo.
C7. Pareo de panel con pasada equivocado: el panel n de Latest10NTI puede no ser la pasada que se cree
    (lamina capturada despues, rotacion de los 10 ultimos, OCR de cabecera con error, otro satelite).
    A veces el OCR de "fecha" lee mal.
C8. Copias de datos atrasadas o distintas de la base 752d348bc (snapshot, i2_pares.csv, png_index.csv).
C9. La vara "punto que publicamos": our_lat/our_lon de i2_pares.csv puede no ser
    final_hotspot_lat/lon, ni lo que pinta el tablero (A46/A61), puede ser de otra pasada.

## 351 (cuatro protegidas VIIRS Chillan, clase iii, 1,0 a 2,5 km)

351a. El record de nuestra pasada no es de la misma pasada (TOL_S, otro satelite, NOAA20 vs NOAA21).
351b. Distancia medida al centroide del pixel entero: con error de +-1 celda, 1,02 km en VIIRS375 es
      apenas 2,7 celdas y 2,16 km en 750 son 2,9 celdas, pero la georreferencia puede estar corrida.
351c. "Protegida" segun la lamina o con otro VRP: MW de la tabla no coinciden; verificar con etiquetar.
351d. Durante erupcion hay varios focos: MIROVA marca el pixel mas caliente; nosotros otro, ambos
      reales. La clase (iii) dependeria de un solo pixel y la lamina puede tener varias manchas.
351e. "publicamos" no esta verificado con el predicado del tablero: la pasada podria no publicarse.
351f. "Pixel poco prominente" en dos de las cuatro: la clase (iii) no se sostiene en ellas.
351g. Los umbrales de clase (i/ii/iii/iv) se fijaron viendo el resultado; un umbral vecino reclasifica.
351h. El "6 MODIS (iii) sin validar" depende de 354.
351i. Geometria real distinta: la posicion en la tabla Distancia_km de MIROVA contradice la de la lamina.
351j. Ataque de nulo: con otra pasada de otra noche, misma mancha, misma distancia (el foco de MIROVA
      puede estar quieto y el nuestro quieto, y 1 km sea un offset sistematico, o de geolocalizacion).

## 352 (control de distancia falla por poco en 30 protegidas de Chillan)

352a. La "Distancia_km" de MIROVA esta cuantizada o medida desde otro origen (vent, mirova_center,
      centroide de cluster); el control puede fallar porque el origen del propio control esta mal.
352b. "0,018 km" es producto del recorte: el centro del panel se fija por construccion y si el pixel
      claro es el central, el 0,018 sale del redondeo, no de una medicion.
352c. "30 protegidas" puede contar otra cosa: alertas no protegidas, varias de las mismas pasadas, no solo
      Chillan. Denominador a revisar.
352d. "nuestro punto a 0,36 km (mediana)": mediana de que poblacion. El nulo: si la mancha esta en la
      celda central y nuestro punto queda cerca del crater por construccion, 0,36 km no dice nada.
352e. mirova_center y vent de volcanoes.yaml podrian no estar a 0,39 km (citar yaml de 752d348bc).
352f. El panel central puede ser un artefacto: el pixel central marcado por una cruz o el simbolo del
      volcan en la lamina, confundido con mancha.
352g. Fila elegida equivocada de la tabla para esa pasada (0,84 podria ser de otra fila/pasada).

## 353 (cobertura de laminas: 12 de 46 dias MODIS, 2 a 3 VIIRS)

353a. png_index.csv (ola 0) esta incompleto o truncado: el archivo si las tiene; el indice se hizo
      con paginacion de la API (tree truncado), o nombres distintos (Latest10NTI vs otra variante).
353b. Ventana: el indice puede haber terminado antes del 2026-11-07; el denominador 46 no coincide.
353c. "Dias sin lamina" vs "pasada sin lamina": una lamina tardia cubre 10 pasadas anteriores; la
      lamina del 11-oct puede contener las pasadas del 8 al 11. "Irrecuperable" podria ser falso.
353d. Chillan MODIS 2026-10-10 07:40 podria estar en una lamina VIIRS o de otro nombre.
353e. Los hoyos pueden ser por volcan y no "los 11 volcanes".
353f. MIROVA pudo no publicar lamina MODIS esos dias (no es fallo del archivo sino de la fuente): la
      redaccion "el archivo no capturo" atribuye causa sin evidencia.

## 354 (lamina MODIS no sirve con el pixel mas claro)

354a. El maximo del TIF no es el pixel alertado (tiene 4 de 7 sin reproducir la tabla): la vara puede ser
      la mala, no la lamina.
354b. La rutina pixel_mas_claro es la mala en MODIS (panel de otro tamano, rotulos, grilla 1 km).
354c. TIF y lamina de pasadas distintas (TIF congelado, md5 repetido, A106).
354d. 7 casos de Lascar son un solo volcan: "MODIS" no se generaliza (y Lascar tiene fondo atipico).
354e. Una proyeccion distinta en MODIS desplazaria todo sistematicamente: seria un offset corregible.
354f. "5 de 7 a 3,6 a 5,8 km" recalcular; "15 i, 6 iii, 3 iv" recontar.

## 355 (MODIS redondea el VRP y pinta marco gris)

355a. Panel equivocado: panel 1 no es la pasada 07:55; o el OCR leyo 0 de otra cosa.
355b. VRP = 0 en lamina y 0,29 en tabla puede ser otra regla (lamina toma otro campo), no redondeo.
355c. El marco gris podria significar otra cosa (dia/noche, sin dato, baja clase); "10 aciertos V750".
355d. La fila de tabla no es ALERTA_TERMICA Muy Bajo en la copia base.
355e. Un solo caso: "redondea a entero" necesita mas de un ejemplo (ver otros valores no enteros).

---
sha256 del cuerpo anterior (hasta la linea previa a este bloque): 1856f3a9c61267fae118f1ab9efa63cf6459fb18764c7f1bc21209852b614313
Hora del servidor: Date: Sun, 08 Nov 2026 13:57:43 GMT
