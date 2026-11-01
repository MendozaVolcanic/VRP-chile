# Caminos por los que el arreglo v3 podria no atrapar un port roto

Escrito ANTES de leer el diff v2 -> v3 y antes de leer el evaluador.
Hora del servidor: Sat, 24 Oct 2026 20:12:27 GMT (gh api -i repos/MendozaVolcanic/VRP-chile, header Date).

1. El control se compara consigo mismo: la referencia "M14 de S162" se toma de los
   mismos artefactos del run B2 (o de la cache recalculada en el mismo run) en vez de
   los artefactos del run 40116289866. Un port roto da el mismo M14 roto en ambos lados y
   coincide.
2. La referencia sale del dato que se quiere probar: si el CTL se compara contra el
   brazo recalculado (cache_lote.json) y no contra lo que el runner escribio en S162,
   la comparacion mide la cache, no el port.
3. Port que no detecta nada: M14 = 0 en todo. Si la comparacion es "coincide dentro de
   tolerancia" y S162 ya tenia M14 = 0 en muchas de las 20 pasadas (noches limpias con
   pocos positivos), un port muerto podria coincidir en 18 de 20 por azar de seleccion.
   El control solo sirve si las 20 pasadas de CTL tienen M14 > 0 (o algun M14 > 0 en
   numero suficiente) en S162.
4. Port que detecta todo o magnitud multiplicada: si el control compara una metrica
   binaria (publica si o no) y no la magnitud, un port que multiplica la magnitud pasa.
   Y si compara presencia, un port que detecta todo pasa en las pasadas donde S162 ya
   detectaba.
5. Port que se cae en parte de las pasadas: si las pasadas caidas del CTL no se cuentan
   como "no coincide" sino como "sin dato" y se excluyen del 18 de 20, un port que se
   cae en 10 de 20 pasa con 10 de 10. Y si la regla del 10 % sin dato se aplica solo al
   lote que decide y no al CTL, el CTL caido no invalida.
6. Umbral 18 de 20: deja pasar 2 fallas; si el port esta roto solo para una clase de
   pasada (por ejemplo las de cenit alto, o las de una plataforma) y el CTL tiene pocas
   de esa clase, pasa.
7. El NO DECIDE no se aplica al veredicto: la regla del 10 % se calcula pero el veredicto
   impreso en "VEREDICTO B" sigue siendo CUMPLE / NO CUMPLE.
8. La linea "VEREDICTO B" dice otra cosa que la regla: toma el veredicto de otra seccion
   (4a) o no refleja INVALIDO POR INSTRUMENTO cuando el CTL falla.
9. Los ids 5000 a 5019 entran a algun denominador por descuido (por ejemplo a la
   cobertura del lote que decide o al conteo de negativos publicados), moviendo el
   veredicto.
10. Orden de evaluacion: si el evaluador decide B antes de evaluar el CTL (o el CTL
    falla silenciosamente si faltan los artefactos CTL, por ejemplo porque el workflow
    no los produjo), un run sin CTL sale decidido.
11. El control de vida compara con tolerancia numerica demasiado laxa (o compara
    redondeos), o compara el M14 agregado del lote y no por pasada.
12. El CTL ausente del todo (0 de 20 artefactos) se trata como "no aplica" y no como
    INVALIDO.
13. La prueba del autor (prueba_control_vida) puede ser un caso vivo y uno muerto con el
    muerto fabricado de forma que falle por otra razon (recalculo sin red, 2.1) y no por
    el control de vida.
