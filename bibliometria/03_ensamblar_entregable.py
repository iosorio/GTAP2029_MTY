#!/usr/bin/env python3
"""
Ensambla resultados_bibliometria_gtap.json a partir de la salida de
02_conteo_openalex.py, en el esquema pedido por la mision.

El bloque google_scholar_pop queda en null mientras la Ruta B no se ejecute:
la mision prohibe rellenar campos con estimaciones.

Uso:  python3 03_ensamblar_entregable.py resultados_openalex.json FECHA
"""
import json
import sys

SS = {  # Cifras de Semantic Scholar del 24-ago-2026, para contraste
    "W1485558032": 946, "W2413227257": 622, "W2955545697": 466,
    "W2497463976": 362, "W2633769093": 289, "W4320021891": 119,
}


def main():
    src, fecha = sys.argv[1], sys.argv[2]
    oa = json.load(open(src, encoding="utf-8"))["openalex"]
    incidencias = json.load(open(src, encoding="utf-8"))["incidencias"]

    obras = []
    for o in oa["obras_canonicas"]:
        e = {
            "titulo": o["titulo"],
            "autor": o["autor"],
            "anio": o["anio"],
            "openalex_id": o["openalex_id"],
            "openalex_tipo": o["openalex_tipo"],
            "cited_by_count": o["cited_by_count"],
            "rol_en_la_union": o["rol"],
            "semantic_scholar_citas_2026_08_24": SS.get(o["openalex_id"]),
        }
        if o.get("nota"):
            e["nota"] = o["nota"]
        obras.append(e)

    incidencias = list(incidencias) + [
        "Ruta B (Publish or Perish / Google Scholar) NO ejecutada. Requiere que "
        "una persona opere la aplicacion de forma interactiva; automatizarla "
        "equivaldria a evadir el bloqueo de scholar.google.com, prohibido "
        "explicitamente por la mision. El bloque google_scholar_pop queda en null.",

        "OpenAlex tiene registros duplicados para tres obras (GTAP-E, Standard "
        "GTAP Model v7 y GTAP-AGR). Se incluyeron ambos registros de cada una en "
        "el filtro cites:. Esto no infla el conteo -- la union se deduplica del "
        "lado del servidor por trabajo citante -- pero si evita perder las citas "
        "dirigidas al registro secundario.",

        "El desglose por pais se calcula sobre la afiliacion institucional que "
        "OpenAlex logra resolver. Los trabajos sin afiliacion resuelta no "
        "aparecen en ningun pais, por lo que la suma por pais es menor que la "
        "union total y los cortes regionales son un piso, no un censo.",

        "por_anio, por_tipo y por_pais se calculan sobre la union ampliada "
        "(14 registros), no sobre la estricta.",

        "Verificado con 04_verificar.py: el conteo del filtro cites: y el campo "
        "cited_by_count de la misma obra difieren entre 1 y 4 unidades (menos de "
        "1%). Es el desfase conocido de OpenAlex entre el indice invertido en "
        "vivo y el campo cacheado, que se actualizan en ciclos distintos. La "
        "union usa el indice en vivo, que es el mas reciente de los dos. Un "
        "tercero que reproduzca el conteo puede obtener variaciones de ese orden, "
        "mas el crecimiento natural del indice desde la fecha de consulta.",
    ]

    salida = {
        "fecha_consulta": fecha,
        "metodo": (
            "OpenAlex API, filtro cites: con OR sobre los IDs de las obras "
            "canonicas de GTAP. meta.count devuelve trabajos distintos que citan "
            "al menos una de ellas, deduplicados del lado del servidor. IDs "
            "resueltos por busqueda de titulo y verificados uno por uno contra "
            "autor y anio. Reproducible con 02_conteo_openalex.py."
        ),
        "openalex": {
            "obras_canonicas": obras,
            "obras_no_resueltas_en_openalex": oa["obras_no_resueltas"],
            "union_trabajos_citantes": oa["union_trabajos_citantes"],
            "union_trabajos_citantes_solo_obras_de_la_mision": oa[
                "union_trabajos_citantes_solo_obras_de_la_mision"],
            "suma_cited_by_count_con_traslape": oa["suma_cited_by_count_con_traslape"],
            "trabajos_con_afiliacion_mexico": oa["trabajos_con_afiliacion_mexico"],
            "trabajos_con_afiliacion_america_latina": oa[
                "trabajos_con_afiliacion_america_latina"],
            "paises_latam_incluidos": oa["paises_latam_incluidos"],
            "ids_union_ampliada": oa["ids_union_ampliada"],
            "ids_union_estricta": oa["ids_union_estricta"],
            "por_anio": oa["por_anio"],
            "por_tipo": oa["por_tipo"],
            "por_pais": oa["por_pais"],
        },
        "google_scholar_pop": None,
        "incidencias": incidencias,
    }
    print(json.dumps(salida, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
