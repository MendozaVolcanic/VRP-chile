# O2-375: el fondo del VRP de MIROVA en MATLAB, escenas VIIRS 375 de 1 a 4 píxeles

## Para qué sirve

O2 (`experiments/_s163_o2/RESULTADO_O2.md`, rama `s163-o2-paquete`) mostró que en alertas de uno a cuatro píxeles
ningún port de `fillmissing2` reproduce a MATLAB: cada uno rellena el hueco que deja la alerta con otra triangulación, y
eso mueve el VRP hasta 0,82 relativo. El port de VIIRS 375 usa ese mismo fondo, así que la magnitud de V375-C en esas
escenas (C13 contra MIROVA) sólo se puede juzgar con la salida de MATLAB. Este paquete la pide.

## Qué contiene

| archivo | qué es | md5 (fin de línea LF, como lo sirve GitHub) |
|---|---|---|
| `MIROVA_VIIRS750_VRP.m` | copia sin cambios del OSF (licencia MIT, `LICENSE.txt`) | `b0ceebb2b7864cd27c145dc8d41968cc` |
| `MIROVA_VIIRS750_hotspot_detection.m` | copia sin cambios del OSF; sólo para el control de Etna | `ddffea3672a08e5aa17c702f72d72170` |
| `entradas_v375.mat` | 422 escenas de 134 x 134 (radiancia I4, `RAD`), sus alertas (`ALE`, `NAL`) y la escena de Etna de O2 (`ETNA_*`) | `29760e4959e07783591cd5c0c5941988` (25.908.903 bytes) |
| `correr_v375.m` | el script que hay que ejecutar | `3852fc915bc557f81eacf9657782bcf4` |
| `entradas_v375_etiquetas.json` | qué es cada escena (no hace falta subirlo) | |

Las 422 escenas son las máscaras distintas de 1 a 4 píxeles que dieron los diez brazos de ROI del port en 381 pasadas
de los lotes S159, S162 y S162b (188 de 1 píxel, 105 de 2, 73 de 3, 56 de 4). La prueba local
(`probar_paquete_375_salida.txt`) comprobó que los índices caen en los mismos píxeles del port, con la misma radiancia y
el mismo VRP del fondo del port en las 422.

## Pasos (MATLAB Online, con la Image Processing Toolbox)

1. En MATLAB Online, crea una carpeta (por ejemplo `o2_375`), entra en ella y baja los cuatro archivos con `websave`
   desde la rama (cambia `COMMIT` por el que indique la sesión que te pase esto):

   ```
   base = 'https://raw.githubusercontent.com/MendozaVolcanic/VRP-chile/COMMIT/experiments/_s162_v375/o2_375/';
   for f = {'MIROVA_VIIRS750_VRP.m','MIROVA_VIIRS750_hotspot_detection.m','entradas_v375.mat','correr_v375.m'}
       websave(f{1}, [base f{1}]);
   end
   ```

2. Comprueba los md5 dentro de MATLAB (tienen que dar los de la tabla), y ejecuta:

   ```
   correr_v375
   ```

   Tarda unos minutos. Imprime la versión, la ruta de `fillmissing2` (tiene que ser una carpeta de MATLAB, no ésta) y la
   línea de Etna: si sale **Tot_Lmir_bk 1.072886152**, MATLAB reproduce a MIROVA y el resultado sirve de vara.
3. Descarga `resultado_v375.mat` (unos 30 MB) y el texto de la ventana de comandos, y déjalos en
   `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375\o2_375\`
   (o pásale la ruta a la sesión de VIIRS 375).

## Qué no hacer

No agregues a la ruta de MATLAB ninguna carpeta con un `fillmissing2.m` propio (como el shim de Octave de O1): el
resultado dejaría de ser de MATLAB.
