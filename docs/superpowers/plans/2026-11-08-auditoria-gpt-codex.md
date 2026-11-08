# Plan: que GPT Codex revise, entienda y audite VRP Chile

Hora del servidor: 2026-11-08 18:24 GMT. Base medida: `origin/main` = `a7a6ae360`. `developers.openai.com/codex` redirige hoy a
`learn.chatgpt.com/docs`: las URL son las que se leyeron hoy. Lo no confirmado dice SIN DATO y se reúne en el §9.

## 0. En una pantalla

**Por qué.** Todas las revisiones las han hecho modelos de un mismo proveedor, que pueden compartir una mala lectura del
MATLAB de MIROVA o de la física de una banda y confirmarse entre sí. Otra familia sirve como laboratorio externo: lo valioso
es que no herede nuestras suposiciones.

**Recomendación.** Usar **Codex Cloud** sobre una **copia aparte y sin historia**, no sobre el repo de producción.
Primero una **prueba ciega barata** con defectos que ya conocemos. Sólo si la pasa, auditar en seis frentes,
partiendo por la vía MODIS que lleva seis días en producción. Todo hallazgo pasa por un verificador limpio de
otra familia, y nada se mergea sin tu frase.

| Decisión que te toca | Recomendación | Por qué |
|---|---|---|
| Plan de ChatGPT | Plus, 20 USD al mes, para la prueba ciega | Basta para medir; sube a Pro sólo si te topas con el límite |
| Dónde corre | Codex Cloud con dos repos privados nuevos | Nunca toca producción y deja afuera tus claves del computador |
| Criterio de aceptar a Codex (§6) | Sellarlo antes de mirar resultados | Si se fija después, se acomoda a lo que salió |

## 1. Qué Codex usar y cómo accede

| Superficie | Qué hace, según la documentación | ¿Para esto? | Fuente |
|---|---|---|---|
| **Codex Cloud** | Tarea en una máquina virtual aislada; requiere entrar con ChatGPT | **Sí** | [environments](https://learn.chatgpt.com/docs/environments/cloud-environments), [auth](https://learn.chatgpt.com/docs/auth) |
| CLI e IDE | Corre en tu computador con sandbox del sistema operativo | No como primera opción (§7) | [security](https://learn.chatgpt.com/docs/agent-approvals-security) |
| Revisión de PR (`@codex review`, `/review`) | Revisa cambios de un PR o rama, no el repo entero | No audita; sirve después para PR | [code-review](https://learn.chatgpt.com/docs/code-review) |
| Codex Security | Escaneo de seguridad de repos | No: nuestro riesgo es científico | [security](https://learn.chatgpt.com/docs/security) |

Lo que condiciona el diseño:

- **Máquina.** Plus: 2 vCPU, 8 GiB de RAM y 8 GiB de disco. Pro y Business: 4 vCPU, 16 GiB y 32 GiB. El estado se
  guarda hasta 7 días ([environments](https://learn.chatgpt.com/docs/environments/cloud-environments)).
- **Internet.** El preparado del entorno tiene red para instalar. En la tarea, "By default, Codex blocks internet
  access during the agent phase" ([internet](https://learn.chatgpt.com/docs/cloud/internet-access), página de la
  versión heredada). La página vigente no dice el valor por defecto: **se deja en Off a mano y se comprueba**.
- **Secretos.** La versión heredada los borra antes de que parta el agente; la vigente pasa las variables de entorno a
  los programas. No importa cuál rija: **no se carga ninguno**.
- **Instrucciones.** Lee `AGENTS.md` y `AGENTS.override.md`, con tope por defecto de 32 KiB. Nuestro `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\CLAUDE.md` no
  aparece entre los nombres que busca ([agents-md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)), y además
  pesa 32.188 bytes: por sí solo llenaría el tope.
- **GitHub.** Codex puede abrir PR ([cloud](https://learn.chatgpt.com/docs/cloud)) y subir arreglos si tiene permiso
  ([github](https://learn.chatgpt.com/docs/third-party/github)). Los permisos exactos de su aplicación no aparecen.
- **Modelos.** Astra es el más capaz; GPT-6.1 Sol es casi igual y más barato, con 500.000 tokens de contexto
  ([models](https://learn.chatgpt.com/docs/models)). Propongo Sol en esfuerzo High, y Astra sólo para el frente F1.

## 2. Por qué nuestro repo le costará y qué preparar

Medido hoy: `.git` local 9,5 GB; GitHub declara 12,2 GiB; `loop/activo` tiene 10.184 archivos y 1.228 MB;
`origin/main` tiene 8.745 archivos y 1.190 MB (780 MB de `data/`, 364 MB de `experiments/`). `loop/activo` va 312 commits
adelante de `main`: la base auditable es `main`, como manda la `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md` §0.

**El problema físico del repo es la historia, no el código.** Un clon completo probablemente no cabe en los 8 GiB de Plus (paquetes locales: 8,98 GiB). Si Codex
clona superficial o no, no está documentado. Una copia sin historia elimina la duda.

| Corte | Contenido | Tamaño | Sirve para |
|---|---|---|---|
| **Ciego** | `d516b9d8c` (la base que auditó S160): `pipeline/`, `scripts/`, `frontend/`, `.github/`, `volcanoes.yaml`, más el `.m` de MIROVA. **Sin** `docs/`, `tests/`, `experiments/` ni `CLAUDE.md` | 3,9 MB más el `.m` | Prueba ciega (§6) |
| **C** | Código, `docs/`, `tests/`, `experiments/` entero, y de `data/` sólo lo operacional y la referencia | 594 MB, 8.293 archivos; el mayor pesa 24,7 MB | Auditoría |
| A (`C:\Users\nmend\vrp-temporales\s176_codex\corte_a`) | Código, `docs/`, `tests/` y `.m`, sin datos | 20 MB, 1.235 archivos | Sólo para la medición de pruebas |

Elegí `git archive` antes que `git clone --depth 1` con sparse-checkout: no deja historia y fija un hash. El clon superficial es plan B y no lo ejecuté. Dos trampas medidas:

- **Finales de línea.** Este computador tiene `core.autocrlf=true`, así que `git archive` entrega el `.m` en CRLF: el
  sha256 cambia (`af9e9115…` contra `e3df84c5…` del blob). Hay que extraer con
  `git -c core.autocrlf=false archive` y declarar que el hash de OSF corresponde a la versión CRLF.
- **Actions se encendería sola.** La copia lleva 57 workflows, 16 con cron. En un repo nuevo correrían sin secretos.
  **Desactivar Actions antes del primer push** y comprobarlo con `gh api repos/<dueño>/<repo>/actions/permissions`.

**¿Corren las pruebas sin red ni credenciales?** En su mayoría sí. `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.github\workflows\tests.yml` declara que no usa
secretos y que mockea la red; instala `libhdf4-dev` y `requirements.txt` para que `import pyhdf` no falle. Comprobé una
muestra, no la suite: 30 de 284 archivos elegidos con semilla fija, con conexiones bloqueadas en Python y sin variables
`EARTHDATA_*`, en este Windows con Python 3.12 (salidas en `C:\Users\nmend\vrp-temporales\s176_codex\muestra_a.json`,
`C:\Users\nmend\vrp-temporales\s176_codex\muestra_b.json` y `C:\Users\nmend\vrp-temporales\s176_codex\muestra_c.json`).

| Grupo | Resultado | Lectura |
|---|---|---|
| Muestra de 30 sobre el corte A | 26 pasan; 4 fallan | Las 4 por carpetas ausentes o una importación desde `experiments/` |
| Esas 4 con carpetas agregadas | 3 pasan; `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\tests\test_guard_libro_de_pruebas_s146.py` sigue fallando | Compara un archivo generado byte a byte; causa SIN DATO |
| 4 que nombran git, sin `.git` | 2 pasan; 1 falla; 1 excede 100 s | Coinciden con las que llaman a `git show`; causa no aislada |
| `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\tests\test_mirova_modis_codigo_s164.py` y `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\tests\test_mirova_v750_codigo_s162.py` | 76 y 38 pasan, sin L1B | Lo central de la vía se prueba con datos sintéticos |

Por censo de texto de los 284 archivos (un piso): 105 mencionan `experiments/`, 45 `data/`, 26 `node` y 10 llaman a
git. Eso justifica el corte C. Queda sin probar en Linux con el arnés real de CI.

**Lo que no podrá verificar.** Sin L1B no reprocesa una pasada real: mide código, datos publicados y escenas sintéticas. Tampoco
tendrá Coppola 2016a (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion\sp426.5.pdf` está en `.gitignore`), lo que limita los frentes a código contra `.m`. Si quieres
que lea el paper, decide primero si la licencia te permite subirlo a un repo privado.

**Preparación del entorno Codex** (red sólo en esta fase, sin probar en su imagen):

```bash
sudo apt-get update -qq && sudo apt-get install -y -qq libhdf4-dev octave nodejs
pip install -r requirements.txt pytest
```

## 3. Cómo hacer que entienda

El borrador completo está en `C:\Users\nmend\vrp-temporales\s176_codex\AGENTS_BORRADOR.md` (7,9 KB, dentro del tope). Va en la
raíz de cada copia, no en producción, reemplazando `<HASH_BASE>`. Va del fenómeno (píxel caliente, detección contra vecinos,
potencia radiante) al mapa de código, los tres sensores con su detector de hoy, el orden de la verdad, los límites y el formato
de hallazgo. Le advierte lo que un auditor sin memoria no adivinaría: los documentos también se auditan, y una marca ⚠️ rebaja el
texto de abajo. Sus rutas son relativas a propósito, porque viven dentro de la copia.

## 4. Qué auditar, de lo que más cambia una alerta a lo que menos

Según nuestro registro, rinde el eje nuevo y no la profundidad (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\PROTOCOLO_AUDITORIA_PROFUNDA.md`, "Cómo se audita, medido"). El eje
nuevo aquí es **otro proveedor leyendo lo que depende de una lectura única**. La última auditoría en esta rama es S160; `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\AUDIT_S175.md`
no está (PR #955, borrador): **SIN DATO**, y antes de lanzar F1 hay que cruzarlo con ella. S160 §8 declara que no corrió los frentes por uso ni de campo.

| # | Frente | Qué pasa en el volcán si falla | Material | Por qué otro proveedor | Línea base que debe reencontrar |
|---|---|---|---|---|---|
| **F1** | Vía MODIS en producción desde 2026-11-02 | MODIS calla una anomalía real o la inventa, con detector nuevo | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\mirova_v750_codigo.py`, `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\process_modis.py:637`, el `.m`, y Octave | El `.m` publicado es de VIIRS 750; aplicarlo a MODIS es SOSPECHA declarada en la cabecera del port. Lectura de MATLAB y su `omitnan` | Una mutación sembrada en el port, sellada por hash |
| **F2** | Lo que ve el operador | El pipeline detecta y el tablero lo esconde, o al revés | `mirovaEqVrp` en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\frontend\index.html`, `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\frontend\diario.html`, `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\frontend\mosaico.html`, contra `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_equivalent\` con node | S160 no corrió el frente por uso, y el eje operador no se usa desde S131; tres copias a mano | K-1 |
| **F3** | Detector K en VIIRS 375 y 750 | Dos de los tres sensores detectan con esto hoy | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\detection_context.py`, `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\process_viirs.py`, `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\process_viirs_mod.py`, flags efectivos de `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\profile.py` | S158 midió 10 de 13 puntos distintos al código de MIROVA; falta una lectura independiente | K-2, K-3, K-4 |
| **F4** | Ausencias silenciosas | Una plataforma calla y el sistema sigue en verde | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\fetch.py`, `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\scripts\run_pipeline.py`, `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.github\workflows\nrt.yml`, simulando ausencias | Eje de vencimientos, con el token por vencer el 2026-12-07 | K-5, K-6, K-7 |
| **F5** | Los instrumentos que sellan decisiones | Se adopta un detector por una vara mal hecha | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\scripts\clase_mirova.py`, `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\scripts\banco_paridad.py`, `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s162_v750a\` | El próximo sello pendiente es V750-A, y S160 ya halló una regla débil | Hallazgo 161 de S160 |
| **F6** | Cierres | Un frente cerrado sin respaldo apaga trabajo futuro | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s145_censo_cierres\censo.py` | Cierres sin respaldo: mayor rendimiento histórico | Sólo si sobra cupo |

Fuera de este plan: el scraper Mirova-v1, que produce la hoja de respuestas y no se auditó en S160. Merece su propio plan.

## 5. Flujo para aceptar lo que encuentre

```text
Plan y criterios commiteados antes  ->  Codex audita, sin red ni secretos, en la copia
  ->  Entrega informe, hallazgos.csv y scripts como PR en la copia (nunca en producción)
  ->  Verificador limpio de otra familia: recibe sólo título y archivo:línea, y reproduce
  ->  CONFIRMADO con guarda en rojo  ->  PR a producción preparado por la sesión  ->  tu frase
```

- **Cuenta como hallazgo** sólo con archivo:línea, comando de reproducción y salida cruda. Formato: el de S160 (título,
  archivo:línea, qué pasa, cómo se ve, cómo reproducir, confianza, gravedad) más el `hallazgos.csv` de la guía §5.
- **El verificador no ve el razonamiento de Codex** (guía §5). Si no reproduce, el hallazgo no entra.
- **Sin guarda no se cierra**: cada confirmado termina en una prueba vista en rojo, porque cerrar con prosa hizo que nueve
  hallazgos reaparecieran (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\PROTOCOLO_AUDITORIA_PROFUNDA.md`, regla B).
- **Tocar `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\process_*.py`, `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\store.py` o `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\profiles\mirova_equivalent.yaml`** exige además tag defensivo y tu confirmación (A45).

## 6. Prueba ciega para calibrar a Codex

**Por qué ciega.** El repo documenta sus propios defectos: encontrarlos leyendo `docs/` mide lectura, no criterio. Por eso se usa `d516b9d8c`, el commit de S160, sin documentos ni pruebas y con el `.m` agregado. En ese commit
comprobé las líneas de K-1, K-5, K-6, K-7 y K-8; K-2 a K-4 las citó S160 sobre ese mismo commit. Una búsqueda parcial no halló
comentarios que los delaten, pero no leí todo el código: la sesión debe repetirla antes de sellar.

| ID | Defecto ya confirmado | Dónde está en `d516b9d8c` | Fuente |
|---|---|---|---|
| K-1 | Cúmulo de cumbre VIIRS 750 recortado a 0,0 MW, que el tablero no publica | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\process_viirs_mod.py:1056` | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\AUDIT_S160.md` §2, 203 |
| K-2 | Contraste contra 8 vecinos y no 3 × 3 con central: pisos 12,5 % más laxos | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\detection_context.py:60-61` y `:530-531` | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s160_audit\f2\INFORME.md`, F2-202 |
| K-3 | El segundo pase toma la sigma de un pool que MIROVA no usa | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\detection_context.py:923` | ídem, F2-205 |
| K-4 | El anillo de fondo se centra en el volcán; en PCC el cráter cae dentro | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\process_viirs_mod.py:539` | ídem, F2-206 |
| K-5 | Plataforma que deja de servirse se informa como cobertura completa | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\scripts\run_pipeline.py:417` | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\AUDIT_S160.md` §2, 241 |
| K-6 | Protegida sin record no levanta bandera en el auto-audit | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\scripts\auto_audit_weekly.py:796` y `:827` | ídem, V3-01 |
| K-7 | `nrt.yml` sin guarda de token vacío | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.github\workflows\nrt.yml` (ausencia) | ídem, 247 |
| K-8 | Geolocalización MODIS: interpolación desde 5 km con el píxel corrido 1 a 3 km (medido en 7 gránulos) | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\pipeline\process_modis.py:385` | `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\tests\test_mxd03_etiquetas_s151.py` l. 4 y 5 |

Además: **control negativo**, la VRE que "integra 62,5 h por día" (211), que un verificador refutó: si Codex la reporta como
defecto sin matices, es una señal de falso positivo. Y **tres mutaciones físicas sembradas** en la copia ciega (banda
cambiada, comparador invertido, media sin central), con su lista sellada por hash fuera de lo que Codex ve.

**Criterio propuesto, que es convención y sellas tú antes de mirar:** continuar si encuentra al menos 5 de 8 conocidos con el
archivo correcto, y **ningún archivo o línea inventados**. Reportar la tasa de confirmación de lo nuevo que traiga. Si
falla, no se descarta a Codex: se revisa si fue la instrucción o el modelo, una vez, y se decide.

## 7. Costo y riesgos

**Costo** ([pricing](https://learn.chatgpt.com/docs/pricing)). Plus 20 USD al mes; Pro desde 100; Business 20 a 25 por usuario al mes con
mínimo de dos. Plus estima 15 a 160 mensajes locales de GPT-6.1 Sol y 5 a 45 de Astra cada 5 horas, puede haber tope semanal y las
tareas en la nube pueden gastar más. Cuántos mensajes cuesta una auditoría es SIN DATO: **la prueba ciega lo mide**. Si tienes ya
cuenta de OpenAI es SIN DATO; hoy `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md` no la nombra y, si se crea, va ahí antes de usarla.

**Qué se expone y qué no.** El repo ya es público, así que el código no es secreto.

| Elemento | Estado comprobado | Regla |
|---|---|---|
| `EARTHDATA_TOKEN` | Sólo el nombre aparece en workflows (102 usos); valor en GitHub Secrets | **Jamás** se entrega |
| `EARTHDATA_USERNAME` y `_PASSWORD` | Nombres en workflows (95 usos cada uno); valor vencido | Jamás |
| `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.env` | Existe (232 bytes) y según el registro trae credenciales reales; está en `.gitignore`; no entra a `git archive` | Por esto Codex **no corre en tu checkout** |
| PAT de GitHub en `C:\Users\nmend\.claude\settings.json` | Según `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md`, en texto plano y sin rotar | Pendiente tuyo, y otra razón para no usar el CLI ahí |
| Repo rastreado | Sin tokens `ghp_`, `github_pat_`, `gho_`, `ghs_` en `origin/main`, ni en `experiments/` ni en los `data/` del corte; los 3 archivos con `EARTHDATA_*=` traen ejemplos | Repetir el barrido sobre la copia antes del primer push |

**Por qué no el CLI en tu computador.** Su documentación no define hasta dónde lee en modo sólo lectura. Hay reglas para denegar rutas
([permissions](https://learn.chatgpt.com/docs/permissions)), pero proteger tus claves con ellas sería confiar en algo no probado acá.

**Entrenamiento.** Revisa en Ajustes, Controles de datos, «Improve the model for everyone», y en Codex el ajuste de entornos.
Lo vi en resultados de búsqueda de [help.openai.com](https://help.openai.com/en/articles/7730893-data-controls-in-chatgpt): la página me
dio 403, compruébalo en pantalla.

**Otros riesgos.** Una instrucción escondida en un archivo: la red apagada corta la salida. Una copia desactualizada: cada informe declara su hash.

## 8. Pasos, en orden

| # | Quién | Qué |
|---|---|---|
| 1 | Nicolás | Decide el §0 y contrata Plus, si no lo tiene. Revisa el ajuste de entrenamiento |
| 2 | Sesión | Commitea este plan y el criterio del §6; sella por hash la lista de conocidos y mutaciones |
| 3 | Nicolás | Autoriza crear dos repos privados: `vrp-codex-ciego` y `vrp-codex-auditoria` |
| 4 | Sesión | Crea los repos, **apaga Actions antes del primer push**, sube el corte ciego con barrido de secretos previo |
| 5 | Nicolás | Conecta Codex a GitHub y selecciona **sólo** `vrp-codex-ciego`; confirma en pantalla que producción no aparece |
| 6 | Nicolás | Crea el entorno en la web: internet Off, sin secretos, script del §2 |
| 7 | Sesión | Te entrega el texto exacto del encargo, con el preámbulo de `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\PLAN_AUDITORIA_S160.md` §6.1 |
| 8 | Nicolás | Lanza la prueba ciega y avisa cuando termine |
| 9 | Sesión | Puntúa contra lo sellado, pasa lo nuevo por verificador limpio, informa consumo y recomienda seguir o parar |
| 10 | Nicolás | Decide si continúa, y si sube de plan |
| 11 | Sesión | Sube el corte C con `AGENTS.md` y prepara el encargo F1, después de cruzarlo con #955 |
| 12 | Nicolás | Lanza F1, luego F2 y siguientes, de a uno |
| 13 | Sesión | Verifica cada frente, escribe guardas y prepara PR a producción. **Nada se mergea sin tu frase** |

## 9. SIN DATO

- Codex: tiempo máximo por tarea, límite de tamaño de repo, profundidad del clon, cómo elegir commit, permisos de su aplicación en GitHub y si se limita a un repo (lo ves en la pantalla de instalación).
- Alcance de lectura del CLI en Windows; si la imagen trae Node, Octave, `sudo` y `apt` (el paso 6 lo revela); cuánto consume una auditoría real.
- `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\AUDIT_S175.md`, que no está en esta rama. La suite completa en el corte C y en Linux; la causa de la falla de `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\tests\test_guard_libro_de_pruebas_s146.py`.
- Si tienes cuenta de OpenAI; licencia para subir PDF de papers.
