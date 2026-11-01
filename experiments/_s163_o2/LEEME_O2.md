# O2: correr el código de MIROVA en MATLAB Online (opcional, para Nicolás)

## Para qué sirve

La detección de MIROVA ya quedó fijada en S159 corriendo el `.m` original en GNU Octave (ver `../INFORME.md`). Lo que
Octave no puede fijar es el fondo del VRP: el `.m` de VRP usa `fillmissing2(...,'linear')`, que sólo existe en MATLAB
R2024a o posterior, y los ports en Python (y el ensayo con Octave) eligen cada uno una triangulación distinta del
hueco que deja la alerta. En una alerta de un solo píxel esa elección mueve el VRP hasta 1,8 veces. Corriendo esto en
MATLAB se sabe cuál es la de MIROVA y cuál de nuestros modelos coincide.

## Qué contiene esta carpeta

- `MIROVA_VIIRS750_hotspot_detection.m` y `MIROVA_VIIRS750_VRP.m`: copias sin ningún cambio del código del OSF
  (licencia MIT en `LICENSE.txt`; md5 ddffea36... y b0ceebb2..., iguales a los originales).
- `entradas_o2.mat`: 311 escenas de 67 × 67 (Etna de ejemplo, las 10 pasadas chilenas de la segunda ronda S158 con sus
  variantes de interpolador, grilla y caja, y 120 escenas sintéticas).
- `entradas_o2_etiquetas.json`: qué es cada escena (no hace falta subirlo).
- `correr_o2.m`: el script que hay que ejecutar.

## Pasos

1. Entra a MATLAB Online (https://matlab.mathworks.com) con tu cuenta. Necesita la Image Processing Toolbox; si la
   licencia es la de la universidad o la de prueba, normalmente viene incluida. El script avisa si falta.
2. En el panel de archivos (MATLAB Drive), crea una carpeta, por ejemplo `o2`, y sube a ella estos cuatro archivos:
   `MIROVA_VIIRS750_hotspot_detection.m`, `MIROVA_VIIRS750_VRP.m`, `entradas_o2.mat` y `correr_o2.m` (17 MB en total;
   arrastrarlos sobre el panel funciona).
3. Haz doble clic en la carpeta `o2` para que quede como carpeta actual y escribe en la ventana de comandos:

   ```
   correr_o2
   ```

   Tarda menos de un minuto. Al final imprime la versión de MATLAB, la ruta de `fillmissing2` y una línea de Etna para
   comparar con el OSF (5 píxeles, Tot_Lmir_hot 1,965342180, Tot_Lmir_bk 1,072886152). Si el Tot_Lmir_bk de Etna sale
   1,072886152, MATLAB reproduce el número de producción de MIROVA y el resultado sirve de vara.
4. Descarga `resultado_o2.mat` (clic derecho sobre el archivo, Descargar) y déjalo en esta misma carpeta:
   `C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete\resultado_o2.mat`. Copia también el texto que imprimió
   la ventana de comandos.
5. Para leerlo (lo puede hacer cualquier sesión):

   ```
   PYTHONIOENCODING=utf-8 python C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\leer_o2.py
   ```

   Compara la detección de MATLAB con la de Octave escena a escena y dice cuál de los tres modelos de fondo (Octave,
   primer port, segundo port) coincide con MATLAB.

## Qué no hacer

No agregues a la ruta de MATLAB ninguna carpeta con un archivo llamado `fillmissing2.m`: el de
`../shim_fillmissing2/` es un modelo para Octave y, si se cuela, el resultado ya no es de MATLAB. El script imprime la
ruta de `fillmissing2` justamente para comprobarlo: tiene que apuntar a una carpeta de MATLAB, no a `o2`.
