#!/usr/bin/env python3
"""
Reconciliacion con la cifra del boletin de GTAP de 2017.

El boletin de 2017 reporta "24,400+ citations attributed to GTAP research
globally" (Google Scholar). Para comparar con el conteo propio hay que igualar
DOS cosas que la comparacion ingenua deja desiguales:

  1. LA FECHA. El 8,825 propio es el acervo de 2026. El 24,400 es el acervo de
     2017. Comparar acervos de distinta fecha sobreestima la brecha. Este
     script recorta el conteo propio a citas emitidas hasta 2017.

  2. EL UNIVERSO SEMILLA. El 24,400 se atribuye a "GTAP research globally",
     no a 14 obras metodologicas. Por eso la comparacion se hace contra la
     semilla ampliada de 05_universo_ampliado.py (las cuatro series propias
     del proyecto mas los libros y volumenes de base de datos).

Lo que queda despues de igualar ambas cosas es el factor de COBERTURA
Google Scholar / OpenAlex, que es la cantidad que la Ruta B debe verificar.

Uso:  python3 07_reconciliacion_2017.py > resultados_reconciliacion.json
"""
import os
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Contacto para el "polite pool" de OpenAlex y Crossref. Las APIs son abiertas
# y no piden llave; el correo solo da prioridad de cola. Se toma del entorno
# para no publicarlo:  export OPENALEX_MAILTO="tu-correo@institucion.edu"
MAILTO = os.environ.get("OPENALEX_MAILTO", "gtap-bibliometria@example.org")
BASE = "https://api.openalex.org/works"
CORTE = 2017
PAUSA = 0.12

# Las 14 obras de la Ruta A, para calcular tambien el conteo estrecho a 2017.
RUTA_A = {
    "W1485558032", "W2497463976", "W2413227257", "W2955545697", "W2633769093",
    "W4242531241", "W4320021891", "W7117369847", "W2141229371", "W3123830708",
    "W1574368972", "W3121700781", "W1525723848", "W2403987006",
}


def get(url, reintentos=5):
    espera = 2.0
    for intento in range(reintentos):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "gtap-bibliometria (%s)" % MAILTO})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and intento < reintentos - 1:
                time.sleep(espera)
                espera *= 2
                continue
            raise
    raise RuntimeError("agotados los reintentos")


def cuenta(filtro):
    url = "%s?%s" % (BASE, urllib.parse.urlencode(
        dict(filter=filtro, per_page=1, mailto=MAILTO)))
    return get(url)["meta"]["count"]


def main():
    universo = json.load(open("resultados_universo_ampliado.json"))
    semilla_ids = []
    for serie in universo["semilla"]["por_serie"].values():
        pass  # los IDs se rearman abajo desde la consulta a las series

    # Rearmar los IDs de la semilla desde las mismas fuentes que 05.
    sys.stderr.write("== rearmando semilla ==\n")
    for sid in [s["source_id"] for s in universo["semilla"]["por_serie"].values()]:
        cursor = "*"
        while cursor:
            url = "%s?%s" % (BASE, urllib.parse.urlencode(
                dict(filter="primary_location.source.id:%s" % sid,
                     select="id", per_page=200, cursor=cursor, mailto=MAILTO)))
            d = get(url)
            semilla_ids.extend(r["id"].rsplit("/", 1)[-1] for r in d["results"])
            cursor = d["meta"].get("next_cursor")
            if not d["results"]:
                break
            time.sleep(PAUSA)
    for c in universo["semilla"]["canonicas_fuera_de_serie"]:
        semilla_ids.append(c["id"])
    semilla_ids = sorted(set(semilla_ids))
    sys.stderr.write("  %d obras en la semilla\n" % len(semilla_ids))

    sys.stderr.write("== citas por obra, acervo %d vs acervo actual ==\n" % CORTE)
    suma_2017 = suma_hoy = 0
    suma_a_2017 = suma_a_hoy = 0
    for i, wid in enumerate(semilla_ids, 1):
        n_hoy = cuenta("cites:%s" % wid)
        time.sleep(PAUSA)
        n_17 = cuenta("cites:%s,publication_year:-%d" % (wid, CORTE)) if n_hoy else 0
        time.sleep(PAUSA)
        suma_hoy += n_hoy
        suma_2017 += n_17
        if wid in RUTA_A:
            suma_a_hoy += n_hoy
            suma_a_2017 += n_17
        if i % 40 == 0:
            sys.stderr.write("  %d/%d  acum: hoy %d, %d %d\n"
                             % (i, len(semilla_ids), suma_hoy, CORTE, suma_2017))

    union_hoy = universo["citantes"]["trabajos_citantes_distintos"]
    sa = universo["citantes"]["serie_anual"]
    union_2017 = sum(v for k, v in sa.items() if int(k) <= CORTE)

    boletin = 24400
    salida = dict(
        fecha_consulta=time.strftime("%Y-%m-%d"),
        fuente="OpenAlex",
        corte=CORTE,
        referencia_externa=dict(
            cifra=boletin,
            texto="24,400+ citations attributed to GTAP research globally",
            fuente="Boletin de GTAP, 2017 (Google Scholar)",
        ),
        semilla_ampliada=dict(
            obras=len(semilla_ids),
            citas_acervo_actual=suma_hoy,
            citas_acervo_2017=suma_2017,
            trabajos_citantes_actual=union_hoy,
            trabajos_citantes_2017=union_2017,
        ),
        ruta_a_14_obras=dict(
            citas_acervo_actual=suma_a_hoy,
            citas_acervo_2017=suma_a_2017,
        ),
        descomposicion_de_la_brecha=dict(
            factor_universo_semilla=(round(suma_2017 / suma_a_2017, 2)
                                     if suma_a_2017 else None),
            factor_cobertura_implicito=(round(boletin / suma_2017, 2)
                                        if suma_2017 else None),
            brecha_total_vs_ruta_a=(round(boletin / suma_a_2017, 2)
                                    if suma_a_2017 else None),
            nota=("factor_cobertura_implicito es lo que Google Scholar tendria "
                  "que estar contando de mas, por obra y a igual fecha, para "
                  "que el 24,400 sea consistente con el conteo de OpenAlex. "
                  "La Ruta B (Publish or Perish) lo verifica midiendo la razon "
                  "Scholar/OpenAlex obra por obra."),
        ),
    )
    json.dump(salida, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.stderr.write(
        "\nSemilla %d obras | citas hoy %d | citas a %d: %d\n"
        "Ruta A a %d: %d citas\n"
        "factor semilla %.2fx | cobertura implicita %.2fx | brecha total %.2fx\n"
        % (len(semilla_ids), suma_hoy, CORTE, suma_2017, CORTE, suma_a_2017,
           suma_2017 / suma_a_2017 if suma_a_2017 else 0,
           boletin / suma_2017 if suma_2017 else 0,
           boletin / suma_a_2017 if suma_a_2017 else 0))


if __name__ == "__main__":
    main()
