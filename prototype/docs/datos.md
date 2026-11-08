# Dataset — Discurso de Odio SV

## Descripción

Corpus de publicaciones salvadoreñas recolectadas manualmente de X y Facebook para clasificación de toxicidad multiclase.

## Variables principales

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `Texto_Original` | texto | Publicación original |
| `Clase_Toxicidad` | categórica | Etiqueta cruda del anotador |
| `label` | categórica | Etiqueta canónica (generada por pipeline) |
| `Plataforma` | categórica | X o Facebook |
| `Lenguaje_Dialectal` | categórica | Salvadoreño / General Español |
| `Presencia_Sarcasmo` | binaria | Sí/No |
| `Presencia_Ironia` | binaria | Sí/No |
| `Contexto_Politico` | binaria | Sí/No |
| `Cohen_Kappa` | numérica | Acuerdo inter-anotadores |
| `Usuario_ID_Anonimizado` | texto | ID anonimizado |

## Licencia y uso

Datos recolectados para fines académicos (UES — ESI 2026). No redistribuir fuera del equipo sin autorización. URLs originales incluidas solo para trazabilidad interna.

## Normalización de etiquetas

Las etiquetas crudas se mapean a 4 clases canónicas en `src/discurso_odio/data/taxonomy.py`:

- `No Tóxico` → `no_toxico`
- `Lenguaje Ofensivo`, `Insulto` → `ofensivo`
- `Discurso de odio`, `Acoso` → `odio`
- `Amenazas/Violencia` → `amenazas`
