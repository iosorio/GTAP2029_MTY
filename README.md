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
| `index.html` | La candidatura completa: qué es GTAP, la conferencia, el perfil del asistente, el esquema Tec–UANL, el calendario y las fuentes |
| `bibliometria.html` | Método y resultados del conteo bibliométrico |
| `acerca.html` | Quiénes, en qué estado está el proceso y cómo se verificó cada cifra |
| `Ficha_GTAP2029_Monterrey.pdf` | La ficha de dos páginas que circula entre directivos |
| `Ficha_GTAP2029_Monterrey.md` | Su fuente en Markdown |
| `scripts/` | El código que reproduce el conteo y el que genera el PDF |
| `datos/` | La salida cruda de la consulta a OpenAlex |

Las tres páginas son HTML autocontenido: sin CDN, sin JavaScript, sin dependencias externas.

## La cifra principal

**3,947 trabajos académicos distintos citan la metodología de GTAP**, procedentes de 111 países.
De ellos, **14 tienen afiliación institucional mexicana** — el 0.4%.

No es una suma de citas. Es el conteo de trabajos distintos que citan al menos una de las
obras canónicas del proyecto, deduplicado del lado del servidor por OpenAlex. Sumar las citas
obra por obra habría dado 4,864 e inflado la cifra un 23%, porque muchos trabajos citan varias
obras a la vez.

Es además un **piso**: OpenAlex no indexa tres de los volúmenes de la base de datos, y no cubre
la literatura gris —informes de ministerios, evaluaciones regulatorias— que es donde GTAP más
se usa. El método y sus límites están documentados en `bibliometria.html`.

## Reproducir el conteo

```bash
python3 scripts/cite.py     # obras canónicas y corpus en Semantic Scholar
python3 scripts/cite2.py    # citas acumuladas del corpus
```

Sin dependencias externas: solo biblioteca estándar de Python 3, sin llave de API.

La cifra principal viene de OpenAlex y sale de una sola consulta:

```
https://api.openalex.org/works?filter=cites:<id>|<id>|...&per_page=1
```

El campo `meta.count` de la respuesta es el número.

## Regenerar el PDF

```bash
python3 scripts/md2pdf.py Ficha_GTAP2029_Monterrey.md 9.8
```

El segundo argumento es el tamaño del cuerpo en puntos, y es la perilla para controlar
cuántas páginas ocupa. El script imprime el número de páginas al terminar. Requiere
Python 3 y Google Chrome.

## Estado

**En exploración.** No hay compromiso institucional de ninguna de las dos universidades ni
una candidatura presentada. Purdue publica la convocatoria de expresiones de interés en enero
de 2027, con fecha límite el 28 de febrero y anuncio del coanfitrión a fines de abril.

## Contacto

Israel Osorio Rodarte — <iosoriorodarte@worldbank.org>
Marcos Esaú Domínguez Viera — <marcos.dominguezviera@wur.nl>

Si algo aquí está mal —una cifra, una atribución, el estado de un proceso— escríbenos.
