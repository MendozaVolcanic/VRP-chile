# -*- coding: utf-8 -*-
"""Clasifica las fallas de un JUnit XML de pytest: AssertionError contra otra excepcion contra error de coleccion.
Uso: python clasificar_junit.py <archivo.xml> [...]"""
import sys, collections, xml.etree.ElementTree as ET
for p in sys.argv[1:]:
    r = ET.parse(p).getroot()
    tipos, por_test = collections.Counter(), []
    n = 0
    for c in r.iter("testcase"):
        n += 1
        for f in c.findall("failure"):
            m = (f.get("message") or "").strip()
            t = "AssertionError" if m.startswith(("assert ", "AssertionError")) else m.split(":")[0]
            tipos[t] += 1; por_test.append((c.get("name"), t, m[:70]))
        for e in c.findall("error"):
            tipos["ERROR(coleccion/setup)"] += 1; por_test.append((c.get("name"), "ERROR", (e.get("message") or "")[:70]))
    print("%s: testcases %d, fallas por tipo %s" % (p.split("/")[-1].split("\\")[-1], n, dict(tipos)))
    for x in por_test:
        print("   %-70s %-16s %s" % x)
