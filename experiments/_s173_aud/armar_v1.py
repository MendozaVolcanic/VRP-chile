import re, pathlib, hashlib, os, csv
os.chdir(r"D:\vrp-trabajo\temporales\s173_aud")
exec(open("armar.py", encoding="utf-8").read().split("TAREA = {")[0])
carpeta = "D:/vrp-trabajo/temporales/s173_aud/v1/"
os.makedirs(carpeta, exist_ok=True)
filas = list(csv.DictReader(open("f1/hallazgos.csv", encoding="utf-8")))
lista = "\n".join(f"- {r['id']} (gravedad {r['gravedad']}): {r['titulo']}. Dónde: {r['archivo_linea']}" for r in filas)
b = bloque.replace("«CARPETA»", carpeta).replace("«RANGO»", "V1-01 en adelante").replace("«DEFINICIONES_DE_LA_VARA»", DEF)
a = auton.replace("«CARPETA»", carpeta).replace("«LIMITES_DE_RECURSOS»", LIM)
v = verif.replace("«CARPETA»", carpeta).replace("«RANGO»", "V1-01 en adelante")
tarea = f"""Verificas los hallazgos de un auditor del eje «censo de consumidores del flag enable_modis_codigo_mirova» sobre los PR A y B del encendido de MODIS. No abras su carpeta D:/vrp-trabajo/temporales/s173_aud/f1/ ni experiments/_s173_aud/f1/ en el repo. Además de estos hallazgos, el auditor afirmó en su resumen tres cosas que también verificas: (X1) en las puntas de A y B ningún workflow que corre un perfil con la vía deja de instalar pyproj; (X2) el `git revert` del merge de B sale limpio sobre main con o sin la rama claude/s172-sombra-34 (PR #932) mergeada antes, y las pruebas pasan sobre el árbol revertido; (X3) no existe ningún record real de la vía de MODIS en data/ (sólo sintéticos).
Hallazgos (título, lugar, gravedad del auditor):
{lista}
Para cada uno, veredicto con tu gravedad y si BLOQUEA el merge del PR A, el del PR B, o ninguno (con la razón). Ten presente que el arreglo natural de 161 y 162 que se discute es mover a A los cambios de B que leen records de la vía; dime si eso es correcto o si rompe algo (patrón 6). En el encabezado declara el modelo y el esfuerzo con que corriste realmente. Informe en {carpeta}INFORME.md."""
txt = f"Eres verificador del proyecto VRP Chile ({REPO}). Lee primero su CLAUDE.md. Por qué: Nicolás va a decidir mergear el PR A y encender en producción la vía «código MIROVA» de MODIS (PR B); el auditor que encontró esto corrió a esfuerzo bajo, así que tu verificación es la que sostiene la decisión.\n\n{b}\n\n{v}\n\nTarea\n{tarea}\n\n{a}\n"
assert not re.search(r"«[A-Z_]+»", txt)
pathlib.Path("prompts/verificador_v1.txt").write_text(txt, encoding="utf-8", newline="\n")
print("v1", hashlib.sha256(txt.encode()).hexdigest()[:8], len(txt))
