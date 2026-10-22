"""F6-6 / identidad: compara los archivos locales del codigo OSF (copia de S158) contra los sha256 y tamanos
que OSF declara en experiments/_s158_audit/f6/osf_metadatos_codigo.txt, probando normalizacion CRLF->LF.
Pregunta 1: si la copia local fuera otro archivo, el hash LF no coincidiria. Pregunta 2: control positivo =
el hash crudo (con CRLF) NO coincide, asi que el instrumento distingue."""
import hashlib, pathlib, re, sys
base = pathlib.Path(r"C:/vrp-trabajo/s159-pruebas/experiments/_s158_d17_diseno/osf_codigo_mirova")
meta = pathlib.Path(r"C:/vrp-trabajo/s159-pruebas/experiments/_s158_audit/f6/osf_metadatos_codigo.txt").read_text(encoding="utf-8")
osf = {m.group(1): (int(m.group(2)), m.group(3)) for m in re.finditer(r"^(\S+) (\d+) creado .*? sha256 ([0-9a-f]{64})", meta, re.M)}
for name, p in [("MIROVA_VIIRS750_hotspot_detection.m", base/"MIROVA_VIIRS750_hotspot_detection.m"),
                ("MIROVA_VIIRS750_VRP.m", base/"MIROVA_VIIRS750_VRP.m"), ("README.txt", base/"README.txt"),
                ("CITATION.txt", base/"CITATION.txt"), ("run_example.m", base/"Example/run_example.m"),
                ("VIIRS750_example.mat", base/"Example/VIIRS750_example.mat")]:
    b = p.read_bytes(); lf = b.replace(b"\r\n", b"\n")
    hr = hashlib.sha256(b).hexdigest(); hl = hashlib.sha256(lf).hexdigest()
    sz, hs = osf.get(name, (None, None))
    print(f"{name}: local={len(b)}B crudo={hr[:12]} LF={len(lf)}B {hl[:12]} | OSF={sz}B {hs[:12] if hs else None} -> "
          f"{'IGUAL_LF' if hl==hs else ('IGUAL_CRUDO' if hr==hs else 'DISTINTO')}")
