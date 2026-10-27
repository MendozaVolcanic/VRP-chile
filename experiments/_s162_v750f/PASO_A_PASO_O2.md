# V750-F: correr O2 en MATLAB Online (lo haces tú, ~15 minutos)

## Por qué ahora

El código de MIROVA calcula el fondo de cada alerta rellenando el hueco con `fillmissing2`, una función que sólo
existe en MATLAB. Nuestros ports la imitan, pero en una alerta de **un solo píxel** la forma de rellenar el hueco
cambia el VRP hasta 1,8 veces (S159 O1). La ablación V750-C confirmó que en un píxel el fondo es justamente lo que
decide la magnitud (sin el halo del código la razón cae a 0,846). En Chile la mayoría de las alertas débiles son de un
píxel, así que esta corrida fija cuál de nuestros ports es la vara para la métrica de magnitud M del paquete V750-A.
No bloquea nada de la publicación.

## Qué hacer

El paquete ya está armado y comprobado (md5 del código de MIROVA iguales a los del OSF, verificado hoy):
`C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete\`.

1. Entra a https://matlab.mathworks.com con tu cuenta (necesita la Image Processing Toolbox; el script avisa si falta).
2. En MATLAB Drive crea una carpeta `o2` y arrastra estos cuatro archivos de la carpeta de arriba:
   `MIROVA_VIIRS750_hotspot_detection.m`, `MIROVA_VIIRS750_VRP.m`, `entradas_o2.mat` (17 MB) y `correr_o2.m`.
3. Entra a la carpeta `o2` (doble clic) y escribe en la ventana de comandos: `correr_o2`
4. Tarda menos de un minuto. Revisa la última línea de Etna: si dice `Tot_Lmir_bk 1,072886152`, MATLAB reproduce el
   número de MIROVA y el resultado sirve.
5. Descarga `resultado_o2.mat` (clic derecho, Descargar) a
   `C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete\resultado_o2.mat` y copia el texto que imprimió la
   ventana de comandos en un archivo `salida_matlab.txt` en la misma carpeta.
6. Avísale a cualquier sesión: «O2 listo». Lo lee `C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\leer_o2.py`.

Lo único que no hay que hacer: agregar a la ruta de MATLAB una carpeta con un archivo `fillmissing2.m` (el script
imprime la ruta de `fillmissing2` para comprobarlo; tiene que ser una carpeta de MATLAB, no `o2`).

Detalle completo: `C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete\LEEME_O2.md`.
