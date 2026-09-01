# Candidatura Monterrey 2029 — Conferencia Anual GTAP

Sitio de respaldo de la candidatura del **Tecnológico de Monterrey** y la **Universidad
Autónoma de Nuevo León** para albergar la 32ª Conferencia Anual sobre Análisis Económico
Global —la conferencia de GTAP— en junio de 2029.

**→ [https://iosorio.github.io/GTAP2029_MTY/](https://iosorio.github.io/GTAP2029_MTY/)**

## Por qué existe

La conversación con los directivos universitarios se apoya en una ficha de dos páginas.
Una ficha corta obliga a dejar fuera casi todo: el historial de sedes, las instituciones
del consorcio, el método detrás de cada cifra. Este repositorio guarda ese material para
que esté disponible sin engordar el documento que la gente realmente lee.

## Contenido

| | |
|---|---|
| `index.html` | La ficha de dos páginas, en pantalla. Mismo texto que el PDF, palabra por palabra |
| `candidatura.html` | La versión extendida: lo anterior más el historial completo de sedes, las 28 instituciones del consorcio por nombre, las plenarias por año, geografía y centros, y las fuentes |
| `bibliometria.html` | Método y resultados del conteo bibliométrico |
| `acerca.html` | Quiénes, en qué estado está el proceso y cómo se verificó cada cifra |
| `Ficha_GTAP2029_Monterrey.pdf` | La ficha de dos páginas que circula entre directivos |
| `Ficha_GTAP2029_Monterrey.md` | Su fuente en Markdown |
| `scripts/` | El código que reproduce el conteo y el que genera el PDF |
| `datos/` | La salida cruda de la consulta a OpenAlex |

Las cuatro páginas son HTML autocontenido: sin CDN, sin JavaScript, sin dependencias externas.

## Qué se edita aquí y qué no

**`index.html`, `candidatura.html`, `Ficha_GTAP2029_Monterrey.md` y
`Ficha_GTAP2029_Monterrey.pdf` son archivos generados. No se editan a mano:** se
sobrescriben en la siguiente corrida. Salen todos de un solo archivo maestro,
`fuente/ficha.md`, que vive en el repositorio de trabajo (`GTAP29`, del que éste
es submódulo), y se regeneran desde ahí con `python3 construir.py`. Ese mismo
script reescribe la barra de navegación de `bibliometria.html` y `acerca.html`,
para que las cuatro páginas ofrezcan siempre el mismo menú en el mismo orden.

Lo que sí se edita a mano aquí es el cuerpo de `bibliometria.html` y `acerca.html`,
y este README.

## La cifra principal

**5,878 trabajos académicos distintos citan la producción del Global Trade Analysis Project**,
procedentes de 129 países. De ellos, **24 tienen afiliación institucional mexicana** — el 0.41%.

No es una suma de citas. Es el conteo de trabajos distintos que citan al menos una de las 323
obras del corpus del proyecto —sus tres series de documentos y su revista, más los libros y
volúmenes de base de datos—, deduplicado por identificador. Las citas suman 8,825; reportar esa
suma inflaría la cifra en un 50%, porque muchos trabajos citan varias obras a la vez.

**El 0.4% mexicano es estable bajo tres definiciones distintas del universo**, con coberturas que
difieren por un factor de tres: 0.35% sobre las 14 obras canónicas, 0.41% sobre las 323 del
corpus, 0.40% sobre los 12,499 trabajos que mencionan «GTAP» en texto completo. Esa estabilidad,
y no el tamaño del conteo, es lo que sostiene el argumento.

La cifra es además un **piso**: OpenAlex no indexa tres de los volúmenes de la base de datos
—que en Google Scholar suman 1,672 citas— ni los conference papers, y no cubre toda la
literatura gris. El método, sus límites y la reconciliación con el «24,400+ citations» que GTAP
difundió en 2017 están en `bibliometria.html`. Esa reconciliación **no cierra**: el universo
semilla explica 1.73x y la cobertura de Google Scholar, medida obra por obra, 1.81x; quedan
2.77x sin explicar, y así se reporta.

## Reproducir el conteo

Los scripts, sus resultados y sus bitácoras están en [`bibliometria/`](bibliometria/),
junto con el [protocolo de captura en Google Scholar](bibliometria/08_protocolo_scholar.md)
y el [detalle del método](bibliometria/README.md). Desde `bibliometria/`:

```bash
python3 02_conteo_openalex.py      > resultados_openalex.json          # 14 obras canónicas
python3 05_universo_ampliado.py    > resultados_universo_ampliado.json # 323 obras del corpus
python3 06_cobertura_fuentes.py    > resultados_cobertura.json         # OpenAlex/Crossref/S2
python3 07_reconciliacion_2017.py  > resultados_reconciliacion.json    # la brecha de 2017
python3 09_procesar_pop.py                                             # Google Scholar
```

Los cuatro primeros vuelcan JSON a stdout, de ahí la redirección; `09` escribe sus
archivos por su cuenta. Los `resultados_*.json` publicados aquí son la salida de esa
misma corrida, para que se pueda comparar sin volver a consultar las APIs.

Sin dependencias externas: sólo biblioteca estándar de Python 3, sin llave de API. `05` y `07`
tardan varios minutos porque recorren las 323 obras de la semilla una por una.

`scripts/` en este directorio conserva los sondeos previos con Semantic Scholar (`cite.py`,
`cite2.py`) y el generador del PDF.

## Regenerar la ficha y las dos páginas que salen de ella

Desde el repositorio de trabajo `GTAP29`, no desde aquí:

```bash
python3 construir.py
```

Regenera las seis salidas, deja el PDF en dos páginas y comprueba de forma
automática que `index.html` y el PDF digan el mismo texto palabra por palabra.
Requiere Python 3 y Google Chrome.

`scripts/md2pdf.py` es la copia publicada del conversor que usa ese script. Sirve
para pasar cualquier `.md` a PDF por su cuenta:

```bash
python3 scripts/md2pdf.py Ficha_GTAP2029_Monterrey.md 8.0
```

El segundo argumento es el tamaño del cuerpo en puntos, y es la perilla para controlar
cuántas páginas ocupa. El script imprime el número de páginas al terminar.

## Estado

**En exploración.** No hay compromiso institucional de ninguna de las dos universidades ni
una candidatura presentada. Purdue publica la convocatoria de expresiones de interés en enero
de 2027, con fecha límite el 28 de febrero y anuncio del coanfitrión a fines de abril.

## Contacto

Israel Osorio Rodarte — <iosoriorodarte@worldbank.org>
Marcos Esaú Domínguez Viera — <marcos.dominguezviera@wur.nl>

Si algo aquí está mal —una cifra, una atribución, el estado de un proceso— escríbenos.
