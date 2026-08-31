# Libro de cuentas — cada número declarado, recalculado

> Generado por `scripts/libro_de_cuentas.py` → `docs/LIBRO_DE_CUENTAS.json`.
> Read-only. Correr antes de cerrar sesión y después de cualquier adopción.

## Por qué existe

Las afirmaciones cuantitativas de este proyecto **no se olvidan: se pudren en
silencio**. Eran ciertas cuando se escribieron, el pipeline y los volcanes cambiaron,
y nadie volvió a medirlas porque no había nada que las recalculara.

La prueba está en el propio `CLAUDE.md`, que carga **siete reglas marcadas
«⚠️ OBSOLETA»** —A7, A13, A17, A23, A36, A42, A82— todas descubiertas a mano,
sesiones después, por casualidad. Y en S128 se sumaron cuatro más: A12 decía «Isluga
~20 K» y da 8,3 · D5 decía «1,35×» y es 0,73, **con el signo invertido** · D9 citaba
un residuo de 24-83× anterior a nadir-fijo · el `.git` de «3,1 GB» eran 10,6.

## Cómo se usa

Cada afirmación se ata a la función que la recalcula, con su banda de tolerancia.
**Salir de banda no es un error: es la señal de que hay que releer la afirmación.**
Tres desenlaces posibles, y los tres son legítimos:

1. el número derivó de verdad → actualizar el documento;
2. la definición cambió → registrarla explícitamente (ver abajo);
3. el registro estaba mal → corregir el registro.

## La lección del primer arranque

Al correrlo por primera vez marcó tres derivas. **Dos eran errores de quien registró**
—un `size-pack` confundido con el tamaño total de `.git`, y una mediana de medianas
confundida con la mediana global— y la tercera era una **ambigüedad de definición**:
«17 flags» (S125) y «28 flags» (hoy) son los dos correctos contando cosas distintas.

De ahí salió el campo que faltaba en el diseño: **la definición va dentro de la
afirmación**. Un número sin su denominador declarado no es verificable — es una cifra
suelta que la próxima sesión va a comparar contra otra cosa y va a creer que encontró
algo.

## El otro entregable: lo que NO tiene instrumento

El script también barre los documentos vinculantes y lista los números que **no** están
registrados. Hoy son **387**. Esa lista no es de errores: es el inventario honesto de lo
que el proyecto afirma sin poder verificar, y es de donde salen los candidatos a
registrar.

**Regla de crecimiento**: cada sesión que produzca un número que gobierne una decisión
lo registra acá antes de cerrar. No hay que registrar los 387 — hay que registrar los
que alguien va a citar.

## Lo que este libro NO cubre

Sirve para números. **No sirve para afirmaciones sobre lo que el código hace** — «el
flag controla el reporte», «el second-run ya lo cubre», «este paper no se leyó». Ésas se
cierran con un **guard**, que es el patrón de S127 y S128
(`tests/test_guard_*.py`): un test que falla si alguien vuelve a escribir lo que ya se
midió como falso.

Las dos mitades juntas cubren los dos modos de olvido que S128 documentó. El tercero
—preguntar con el instrumento equivocado, A89— no se arregla con infraestructura: se
arregla cruzando antes de reportar una ausencia.
