#!/usr/bin/env python3
"""
Paso 1 - Resolver candidatos de OpenAlex para cada obra canonica de GTAP.

No decide nada: descarga los candidatos con autor y anio para que una
persona verifique cada coincidencia antes de fijar el ID.

Uso:  python3 01_resolver_ids.py > candidatos.txt
"""
import json
import time
import urllib.parse
import urllib.request

MAILTO = "osorio.israel@gmail.com"
BASE = "https://api.openalex.org/works"

# (etiqueta_corta, titulo_de_busqueda, autor_esperado, anio_esperado)
OBRAS = [
    ("hertel1997",  "Global Trade Analysis: Modeling and Applications",                                   "Hertel",         1997),
    ("gtap9",       "An Overview of the GTAP 9 Data Base",                                                "Aguiar",         2016),
    ("gtap10",      "The GTAP Data Base: Version 10",                                                     "Aguiar",         2019),
    ("structure",   "Structure of GTAP",                                                                  "Hertel/Tsigas",  2000),
    ("standard7",   "The Standard GTAP Model, Version 7",                                                 "Corong",         2017),
    ("gtap11",      "The GTAP Data Base: Version 11",                                                     "Aguiar",         2022),
    ("gtap8",       "Global Trade Assistance and Production: The GTAP 8 Data Base",                       "Narayanan",      2012),
    ("gtap7",       "Global Trade Assistance and Production: The GTAP 7 Data Base",                       "Narayanan/Walmsley", 2008),
    ("gtap6",       "Global Trade Assistance and Production: The GTAP 6 Data Base",                       "Dimaranan",      2006),
    ("gtape",       "GTAP-E: An Energy-Environmental Version of the GTAP Model",                          "Burniaux/Truong", 2002),
    ("dynamic",     "Dynamic Modeling and Applications for Global Economic Analysis",                     "Ianchovichina/Walmsley", 2012),
    ("gtapagr",     "GTAP-AGR: A Framework for Assessing the Implications of Multilateral Changes in Agricultural Policies", "Keeney/Hertel", 2005),
    ("gtap12",      "The GTAP Data Base: Version 12",                                                     "Aguiar",         2025),
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": f"gtap-bibliometria ({MAILTO})"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def buscar(titulo, per_page=5):
    q = urllib.parse.urlencode({
        "search": titulo,
        "per_page": per_page,
        "mailto": MAILTO,
        "select": "id,display_name,publication_year,type,cited_by_count,authorships,doi",
    })
    return get(f"{BASE}?{q}")


def autores(w, n=4):
    nombres = [a["author"]["display_name"] for a in w.get("authorships", [])[:n]]
    extra = " et al." if len(w.get("authorships", [])) > n else ""
    return ", ".join(nombres) + extra


def main():
    for etiqueta, titulo, autor_esp, anio_esp in OBRAS:
        print("=" * 100)
        print(f"[{etiqueta}]  BUSCADO: {titulo}")
        print(f"              ESPERADO: {autor_esp}, {anio_esp}")
        print("-" * 100)
        try:
            data = buscar(titulo)
        except Exception as e:
            print(f"   ERROR: {e}")
            continue
        if not data.get("results"):
            print("   SIN RESULTADOS")
        for i, w in enumerate(data["results"], 1):
            wid = w["id"].rsplit("/", 1)[-1]
            print(f"   {i}. {wid}  {w.get('publication_year')}  cited_by={w.get('cited_by_count')}  type={w.get('type')}")
            print(f"      titulo: {w.get('display_name')}")
            print(f"      autores: {autores(w)}")
            print(f"      doi: {w.get('doi')}")
        print()
        time.sleep(0.4)


if __name__ == "__main__":
    main()
