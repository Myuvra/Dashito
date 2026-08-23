# Archivos BCRA conservados sólo en local

Estos dos archivos fuente se usan y conservan localmente, pero no se suben al repositorio:

- `data/fuentes/tasas/bcra/tas1_ser.txt` — aproximadamente 160,32 MiB en disco.
- `data/fuentes/tasas/bcra/tas2_ser.txt` — aproximadamente 130,11 MiB en disco.

## Por qué no están en GitHub

GitHub rechaza archivos individuales mayores de 100 MB. El intento de subirlos produjo el error `GH001: Large files detected`, por lo que ambos quedaron excluidos mediante `.gitignore`.

Los archivos no fueron borrados del equipo: permanecen en las rutas indicadas para los cálculos y reconstrucciones locales del dashboard. Para reproducir el proyecto con estas fuentes completas, hay que volver a colocar ambos archivos en esas mismas rutas.

## Despliegue en Netlify

Estos archivos tampoco son necesarios para publicar el sitio en Netlify. El `index.html` contiene las series ya procesadas y no carga los `.txt` locales durante la navegación. Las referencias visibles a `tas1_ser.txt` y `tas2_ser.txt` son enlaces a las fuentes remotas del BCRA y notas de auditoría.
