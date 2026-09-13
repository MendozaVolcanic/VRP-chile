# S139: por qué apagar `keep_peak` baja la razón de magnitud de 0,708 a 0,692

> Pregunta de Nicolás: *¿qué estamos haciendo mal, o es sólo que se eligen otros píxeles?*
> Datos: artefactos del A/B de S135 (runs 34173711390 y 34208191011), fusionados con
> `experiments/_s135_ab_d1d2/fusionar_chunks.py`. Ventana 2026-06-01 a 2026-08-31, VIIRS 375 m,
> 6 volcanes (Isluga, Láscar, Lastarria, Puyehue-Cordón Caulle, Planchón-Peteroa, Tupungatito),
> referencia MIROVA CONS+OCR nocturna hasta 2026-09-07.

## Control de instrumento

El evaluador de S135 (`evaluar_ab.py`), corrido sin modificar sobre los artefactos descargados,
reproduce exacto: control 0,708, brazo B 0,692, 0 noches perdidas en ambos. Los scripts de abajo
reusan sus funciones de pareo, predicado y magnitud; no las reimplementan.

## Qué pasa

**No es un cambio de composición.** El brazo B deja de publicar 32 pasadas, todas de 1 píxel, con
razón mediana 0,34 contra MIROVA. Sacar valores bajos **sube** la mediana: el control sin ellas da
0,721. B no publica ninguna pasada nueva.

**La caída viene de 71 de las 574 pasadas que publican los dos brazos**, donde la magnitud cambia:
53 bajan (mediana B/A 0,40) y 18 suben. Las que bajan están en Isluga (21), Tupungatito (11),
Láscar (9), Planchón-Peteroa (5), Lastarria (6) y Puyehue-Cordón Caulle (1). En esas 71 pasadas la
razón contra MIROVA es 0,78 con el control y 0,37 con B.

**El fenómeno.** En una noche débil el cráter tiene un foco apenas más caliente que el terreno.
- Con `keep_peak` activo, el pipeline publica el píxel más caliente del cúmulo, que muchas veces está
  a unos 3 km del cráter (2,7 a 3,0 km en los casos extremos), sobre terreno más tibio, y le da
  0,05 a 0,1 MW. Eso se parece a lo que publica MIROVA. **La paridad salía por accidente, con un
  píxel en el lugar equivocado.**
- Con `keep_peak` apagado, publica el píxel del cráter (0,1 a 0,9 km) con 0,001 a 0,01 MW: el lugar
  correcto con una energía casi nula.

**Por qué ese píxel del cráter queda casi en cero:** en las 53 pasadas que bajan, el píxel que
publica B está apenas **1,21 K** sobre el fondo del anillo (mediana; 15 % bajo el fondo). El que
publicaba A estaba 2,0 K sobre el fondo (9 % bajo el fondo). En las 503 pasadas sin cambio la
diferencia es **5,86 K**. El exceso de radiancia que integra el VRP sale de esa diferencia, así que
en noches débiles el píxel del cráter aporta casi nada.

## Lectura

- La respuesta a Nicolás es **las dos cosas a la vez**: se elige otro píxel, y el píxel correcto da
  una energía demasiado baja. El segundo efecto es el que importa, porque es el que queda cuando se
  corrige el primero.
- Es consistente con S124 (en noches débiles captamos 1 píxel y medimos la mitad) y con la
  divergencia D25 (fondo como mediana de un anillo de 5 a 25 km, no media de los vecinos). **No
  prueba D25**: falta comparar nuestro fondo con el de MIROVA (`Tot_Lmir_bk` del OSF) y con la media
  de los 8 vecinos. Eso lo mide `docs/audit_s139/MAGNITUD_DESCOMPOSICION_OSF.md`.
- Consecuencia para el plan: apagar `keep_peak` es correcto en posición, pero adoptarlo solo deja la
  magnitud más baja. Tiene que ir junto con la corrección de la energía del píxel del cráter (fondo,
  número de píxeles o área), no antes.

## Reproducir

```
python experiments/_s135_ab_d1d2/fusionar_chunks.py --c1 <artefactos run 34173711390> --c2 <artefactos run 34208191011> --out <fus>
python experiments/_s135_ab_d1d2/evaluar_ab.py --dir <fus> --out <tmp>
python experiments/_s139_audit/keep_peak_paridad/descomponer_caida_paridad.py --dir <fus>
```

Salidas: `salida.txt`, `salida_71_pasadas.txt`, `salida_fondo.txt` en esta carpeta. Los artefactos
descargados están en `experiments/_artefactos_ab/` (433 MB, no se commitean).
