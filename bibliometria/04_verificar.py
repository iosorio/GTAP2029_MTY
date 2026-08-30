#!/usr/bin/env python3
"""
Verificacion independiente del conteo.

Tres pruebas:
  1. cites:<un id> debe coincidir con el cited_by_count de esa obra.
  2. La union de dos obras debe ser <= la suma y >= el maximo individual.
  3. La union total debe ser < la suma de todos los cited_by_count
     (si fuera igual, no habria traslape y algo estaria mal).
"""
import os
import json
import time
import urllib.parse
import urllib.request

# Contacto para el "polite pool" de OpenAlex y Crossref. Las APIs son abiertas
# y no piden llave; el correo solo da prioridad de cola. Se toma del entorno
# para no publicarlo:  export OPENALEX_MAILTO="tu-correo@institucion.edu"
M = os.environ.get("OPENALEX_MAILTO", "gtap-bibliometria@example.org")


def get(u):
    r = urllib.request.Request(u, headers={"User-Agent": "gtap-bib (%s)" % M})
    return json.load(urllib.request.urlopen(r, timeout=60))


def n_cites(ids):
    p = urllib.parse.urlencode({"filter": "cites:%s" % "|".join(ids),
                                "per_page": 1, "mailto": M})
    return get("https://api.openalex.org/works?%s" % p)["meta"]["count"]


def cb(wid):
    return get("https://api.openalex.org/works/%s?mailto=%s&select=cited_by_count"
               % (wid, M))["cited_by_count"]


d = json.load(open("resultados_bibliometria_gtap.json", encoding="utf-8"))["openalex"]
ids = d["ids_union_ampliada"]

print("PRUEBA 1 - cites:<id> vs cited_by_count declarado")
ok = True
for o in d["obras_canonicas"][:4]:
    w = o["openalex_id"]
    a, b = n_cites([w]), cb(w)
    marca = "OK " if a == b else "DIF"
    if a != b:
        ok = False
    print("  %s %-12s cites=%-5s cited_by_count=%-5s" % (marca, w, a, b))
    time.sleep(0.3)

print("\nPRUEBA 2 - union de dos obras acotada por suma y maximo")
a, b = ids[0], ids[2]
na, nb = n_cites([a]), n_cites([b])
time.sleep(0.3)
nab = n_cites([a, b])
print("  |A|=%d  |B|=%d  |A U B|=%d" % (na, nb, nab))
print("  max<=union<=suma : %s" % ("OK" if max(na, nb) <= nab <= na + nb else "FALLA"))
print("  traslape A^B = %d trabajos" % (na + nb - nab))

print("\nPRUEBA 3 - union total vs suma con traslape")
total = n_cites(ids)
suma = d["suma_cited_by_count_con_traslape"]
print("  union=%d  suma=%d  traslape absorbido=%d" % (total, suma, suma - total))
print("  union<suma : %s" % ("OK" if total < suma else "FALLA"))
print("  union estable entre corridas : %s"
      % ("OK" if total == d["union_trabajos_citantes"] else "CAMBIO"))
