# Caminos por los que cada afirmación podría estar mal (escrito ANTES de abrir ningún archivo citado)

Verificador: ver_s172_relector. Sólo conozco los títulos y dónde mirar de A1 a A5.

## A1. Las cinco claves sólo afectan a MODIS o VIIRS 750

1. Nombre en el punto de uso distinto del de la definición (A89): la clave se lee con otro nombre
   (parámetro vs clave YAML), de otra sección (raíz vs `thresholds:`), o con alias.
2. Una de las cinco claves la lee un módulo compartido (`pipeline/profile.py`, `geo_utils`, `store.py`,
   `fetch.py`) que sirve también a VIIRS 375; el efecto en V375 pasa por el caller (A6), no por el
   procesador de MODIS.
3. Herencia de perfiles: `sombra_codigo_mirova` hereda de `mirova_equivalent` (u otro); una clave del padre
   cambia lo que publica el hijo aunque su nombre suene a MODIS.
4. La clave tiene efecto sobre cómo el lector etiqueta pasadas V375 (filtro por sensor, por fecha, por
   volcán, clasificación de plataforma Suomi NPP) sin tocar el pipeline.
5. Una clave de las cinco existe en `thresholds:` con un nombre distinto en `origin/main` hoy (copia
   local atrasada, rama del worktree anterior a main): la lista del lector no coincide con lo que main lee.
6. La clave cambia un valor por defecto compartido (p. ej. una bandera `enable_*` que además de MODIS
   activa un camino genérico, como la banda 22 primaria, que la K de V375 también lee).
7. Una clave "de MODIS" gobierna máscara de nube, área nadir o conectiva `max` que `process_viirs.py`
   también consume.
8. La clave de VIIRS 750 (V750) aparente se lee en `process_viirs_mod.py`, pero el caller de V375 comparte
   la función (`process_viirs.py` importa de `process_viirs_mod`).
9. Clave presente en el YAML pero leída de `pipeline.profile` con un fallback distinto por sensor.

## A2. perfil_sin_otro_sensor / cambio_significativo marcan todo salvo esas cinco claves y fallan cerrado

1. Comparación por claves quita las cinco claves en CUALQUIER sección (no sólo `thresholds:`): una clave
   homónima en otra sección (raíz, `sensors:`, `volcanoes:`) se descartaría sin marcar.
2. Se quita la clave pero no su valor cuando es anidada/lista; o se comparan las cadenas tras quitar
   líneas por regex (texto) y una línea con sangría distinta, comentario o ancla YAML se cuela o se pierde.
3. Parseo YAML: claves duplicadas (la última gana), anclas/merge `<<:`, tipos (`true` vs `"true"`,
   `1` vs `1.0`), YAML 1.1 (Norway: `on`/`no`), claves no string (`on:` como booleano True).
4. Un cambio de comentario o de orden de claves marca régimen (marca de más: aceptable) o, al revés, un
   cambio real (valor de una clave de otro sensor que NO está en la lista) no marca.
5. Falla cerrada incompleta: perfil que no existe en la referencia, perfil vacío, YAML inválido, perfil
   cuyo contenido es `None`, excepción capturada que devuelve "sin cambio".
6. Herencia entre perfiles (`extends`/`inherits`): un cambio en el padre que no está en PERFILES_REGIMEN.
7. `PERFILES_REGIMEN` incompleto: falta un perfil que V375 realmente lee (p. ej. el que usa el workflow
   `sombra-codigo-mirova.yml`) o falta el tercero heredado.
8. Cambios a archivos que no son perfil y sí afectan a V375 (workflow, `pipeline/*.py`) no los cubre la
   comparación de perfiles: depende de otro control del S8 (¿lo hay?). Lo de A4 (editar la aserción del
   workflow) pasa por ahí.
9. El control compara contra una base equivocada (la del tag y no la de `main`), así que "no marca"
   puede ser por comparar contra sí mismo.
10. Se quitan las claves del perfil de AMBOS lados pero el valor de la clave cambia lo que la vía publica
    si la clave pasa a ser leída por V375 en el futuro (una clave "de otro sensor" hoy no lo será mañana):
    el control S8 no ve el cambio de código que vuelve compartida a una clave.

## A3. S0 no depende de `main`

1. Los sha256 se calculan sobre archivos del checkout del lector pero el lector lee otros archivos de
   `main` por ruta de disco (p. ej. `Path(__file__).parents[N]` apunta al repo compartido, no al
   worktree/tag).
2. S0 lee `pipeline/profiles/*.yaml` o `frontend/index.html` del árbol del cwd en vez del tag.
3. Normalización de finales de línea (CRLF vs LF; autocrlf): el sha256 cambia entre checkouts de la misma
   ref (A169/S163: md5 y autocrlf).
4. El sha256 esperado está escrito en el propio lector o en un archivo que `main` puede cambiar.
5. "Siempre que el lector se corra desde un checkout de su tag" es una condición no verificada por el
   propio lector: ¿detecta que corre desde otro commit?
6. S0 incluye en su lista de archivos sellados alguno que el PR de MODIS toca (mirova_equivalent.yaml o
   frontend/index.html): si lo incluye, cae.

## A4. Escenario con MODIS encendido + guardia + perfil nuevo + workflow nuevo no marca; editar l. 110 del workflow sí

1. La línea 110 del workflow en origin/main no es la aserción (el número envejeció; A101).
2. El workflow `sombra-codigo-mirova.yml` no está entre lo que el S8 compara, así que editar la aserción
   NO marcaría (afirmación falsa), o marca por una razón distinta (hash del archivo completo).
3. Un perfil nuevo o un workflow nuevo pueden marcar por la regla de "perfil que aparece" (falla cerrada)
   si PERFILES_REGIMEN se calcula por glob.
4. La guardia nueva modifica un archivo comparado (tests, pipeline) y marca.
5. Sólo la clave nueva en mirova_equivalent.yaml: ¿la clave se llama exactamente así en las cinco? La
   clave `enable_modis_codigo_mirova` puede no estar entre las cinco: entonces marcaría. Si está
   entre las cinco en una lista y el escenario real del PR cambia además otra cosa (comentarios,
   cabecera, valores), marca.
6. El escenario real del PR del dueño puede traer más que la clave nueva (cabecera FICHA, comentarios):
   la afirmación habla sólo de la clave.
7. Comprobar con perfiles reales de origin/main editados (no con perfiles sintéticos que el propio auditor
   armó) para evitar medir contra el caso fácil.

## A5. Pruebas nuevas y S01 a S08 bastan; retirar R07 no deja nada sin vigilar

1. Una mutación "atrapada" porque la prueba cae por otro motivo (excepción, import roto), no por la
   aserción que debía (mutación que cae no es atrapada, S152).
2. Mutaciones S01 a S08 no cubren el hueco A89 (clave homónima en otra sección, alias, anclas YAML).
3. R07 vigilaba algo que sólo R07 vigilaba: comparar el contenido de R07 (prueba/control retirado) con
   las pruebas que lo reemplazan; qué aserción desaparece.
4. La batería pasa en verde por un control que no puede fallar (falta control positivo; nulo no medido).
5. La batería tarda 20-25 min; su resultado puede variar con árbol no quieto (A112); sha256 del árbol
   antes y después.
6. Las pruebas "S8 (S172)" usan perfiles sintéticos y no reales de origin/main.
7. La batería depende de red/estado externo (fetch de main) y da verde sin datos.
8. Mutación y prueba comparten el mismo helper: si el helper está roto, ambas pasan (instrumento
   circular).
9. Diff entre tag y commit contiene cambios fuera de lo declarado (p. ej. el lector cambió algo más que
   las claves: orden de controles, tolerancia).

## Caminos transversales

- La copia local atrasada: usar `origin/main`, y comprobar con `git rev-parse origin/main` y fecha del
  servidor; el prompt dice que el fetch ya está hecho, pero A5 de la regla de proyecto (frescura) manda
  consultar el remoto. Puedo usar la API de GitHub (hasta 20 llamadas de sólo lectura).
- El worktree en el commit equivocado (HEAD distinto del indicado) o con cambios sin commitear.
- Que las rutas del worktree contengan archivos no versionados que el lector lea.
- Vara: el código de `origin/main` hoy; verificar que el archivo del perfil en main sea el que el
  workflow de la sombra realmente usa.

---
sha256 del contenido anterior a esta linea (sin estas 3 lineas finales): dccca35353dc9760940a843cf7741baca5791491b4e9db74a3097941388f0216
Hora del servidor: 2026-11-01 23:23:50 UTC
