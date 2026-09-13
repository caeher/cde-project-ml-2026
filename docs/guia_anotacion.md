# Guía de Anotación — Toxicidad y Discurso de Odio (contexto salvadoreño)

**Versión 2.0** · 30 de julio de 2026
Proyecto: Análisis del Discurso de Odio en Redes Sociales en El Salvador · UES

> **Motivo de esta versión.** La v1 no era unívoca: produjo una divergencia de protocolo
> entre anotadores (348 filas etiquetadas con el nivel de subclase en la columna de clase)
> y convenciones implícitas nunca escritas. Esta versión fija criterios operativos,
> establece una regla de precedencia y resuelve por escrito los casos límite observados
> en el corpus real.

---

## 1. Las cuatro clases

La anotación asigna **exactamente una** de estas cuatro clases a cada texto:

| ID | Clase | Núcleo del criterio |
|---|---|---|
| 0 | `No Tóxico` | No hay insulto, ataque ni agresión |
| 1 | `Lenguaje Ofensivo` | Insulto o vulgaridad **sin** grupo protegido de por medio |
| 2 | `Discurso de Odio` | Ataque a una persona **por pertenecer** a un grupo protegido |
| 3 | `Amenazas/Violencia` | Amenaza, incitación, deseo o celebración de daño físico |

## 2. Regla de precedencia (obligatoria)

Muchos textos cumplen más de una definición. Cuando eso ocurra, **se asigna siempre la
clase de mayor severidad**:

```
Amenazas/Violencia  >  Discurso de Odio  >  Lenguaje Ofensivo  >  No Tóxico
```

Ejemplo: *«hay que matar a esos negros de mierda»* contiene vulgaridad (clase 1) y ataque
racial (clase 2), pero incita a la violencia → **Amenazas/Violencia**.

Ejemplo: *«inmigrantes de mierda»* contiene vulgaridad (clase 1) y ataque por origen
nacional (clase 2) → **Discurso de Odio**.

## 3. Definiciones operativas

### 3.0 · No Tóxico

Ausencia de insulto, desprecio y agresión. **Incluye explícitamente:**

- Contenido neutro, informativo, comercial o afectivo.
- **Crítica dura a ideas, políticas, instituciones o gestión pública sin insultar.**
  *«Excelente ya era tiempo de poner orden en el sistema de transporte público»* →
  No Tóxico. *«Esta medida es un fracaso y va a empeorar la economía»* → No Tóxico.
- Reporte o descripción de hechos violentos sin adherirse a ellos.
  *«Detuvieron a tres personas por el asesinato»* → No Tóxico.
- Desacuerdo, queja o enojo expresado sin insulto.

> **No confundir tema con toxicidad.** Que un texto hable de pandillas, migración o
> política no lo hace tóxico. Lo tóxico es el ataque, no el asunto.

### 3.1 · Lenguaje Ofensivo

Insulto, vulgaridad, desprecio, burla o descalificación dirigidos a:

- una **persona individual** (*«sos un pendejo»*, *«su opinión nos vale verga»*),
- una **institución, gobierno o funcionario** (*«este gobierno de ladrones»*),
- un **colectivo no protegido**: partido político, afición deportiva, profesión,
  seguidores de una figura pública,
- o **sin destinatario** (obscenidad genérica, *«qué mierda de día»*).

**Incluye:** groserías, insultos directos, tono agresivo, sarcasmo hiriente hacia un
individuo, descalificación política con insulto.

**La afiliación política NO es categoría protegida.** *«Los del partido X son unos
imbéciles»* → Lenguaje Ofensivo, **no** Discurso de Odio. Esta regla es explícita y no
admite excepción: sigue el criterio de HatEval y de la literatura estándar.

### 3.2 · Discurso de Odio

Ataque, deshumanización, estigmatización, exclusión o negación de derechos dirigidos a
una persona o colectivo **en razón de su pertenencia a un grupo protegido**.

**Ejes protegidos reconocidos en este proyecto:**

| Eje | Ejemplos de subclase |
|---|---|
| Origen o nacionalidad | Xenofobia, estigmatización nacional |
| Etnia o raza | Racismo, bestialización, antigitanismo |
| Religión | Islamofobia, antisemitismo, religiofobia |
| Género | Misoginia, sexismo |
| Orientación sexual | Homofobia |
| Identidad de género | Transfobia |
| Discapacidad | Capacitismo |
| Estado de salud | Serofobia |
| Edad | Edadismo, gerontofobia |
| Corporalidad | Gordofobia |
| Condición socioeconómica | Clasismo, aporofobia |

**Marcadores típicos:** generalización hostil sobre el grupo, atribución de defectos
inherentes, comparación con animales o plagas, llamado a excluirlos o expulsarlos,
negación de su humanidad o de hechos históricos que los victimizaron.

**Ejemplos del corpus:**

- *«Que indios de mierda»* → Discurso de Odio (racismo)
- *«Los haitianos nos están quitando el trabajo»* → Discurso de Odio (xenofobia económica)
- *«solo un 3% de los discapacitados de mierda»* → Discurso de Odio (capacitismo)
- *«deportar a toda una familia de inmigrantes de mierda»* → Discurso de Odio (xenofobia)

> **Criterio del eje frente al objeto.** La clase la determina *a quién* se ataca, no
> *por qué eje*. Racismo, xenofobia y clasismo son todos `Discurso de Odio`; el eje se
> registra en la columna `Subclase_Toxicidad`, **nunca** en `Clase_Toxicidad`.
> Este es el error que originó la v2 de esta guía.

### 3.3 · Amenazas / Violencia

Amenaza explícita, incitación, deseo o celebración de daño físico contra personas.

**Subtipos:**

- **Amenaza directa** — *«te voy a matar»*
- **Amenaza implícita** — *«ya sabés lo que te puede pasar»*
- **Incitación a la violencia** — *«hay que darles plomo»*
- **Deseo de daño o sufrimiento** — *«ojalá se muera»*, *«que se le mueran los familiares»*
- **Apología o celebración de la violencia** — *«bien hecho que lo mataron, uno menos»*

#### Convención del proyecto: discurso punitivo contra pandillas

El corpus contiene abundante discurso hostil hacia mareros, pandilleros y personas
detenidas. La convención adoptada por el proyecto, y que esta guía formaliza, es:

- **`Amenazas/Violencia`** cuando el texto **celebra, desea o incita** daño, sufrimiento,
  muerte o encierro como castigo, o deshumaniza al colectivo con lenguaje eliminacionista
  (*«escoria»*, *«hay que exterminarlos»*, *«uno menos»*, *«al CECOT y que se pudran»*).
- **`No Tóxico`** cuando es discusión de política de seguridad sin adhesión al daño
  (*«el régimen de excepción redujo los homicidios»*).

«Marero» o «pandillero» **no** constituye grupo protegido: se refiere a una conducta
delictiva, no a una característica identitaria. Por eso este discurso se clasifica en
`Amenazas/Violencia` y no en `Discurso de Odio`.

#### Petición de sanción legal

Pedir cárcel, juicio o deportación **por vías legales**, sin desear daño ni deshumanizar,
**no** es `Amenazas/Violencia`:

- *«Que lo investiguen y lo juzguen»* → No Tóxico
- *«Que lo deporten, no tiene papeles»* → No Tóxico
- *«Que deporten a esos indios asquerosos»* → Discurso de Odio (el ataque es al grupo)
- *«Al CECOT y que se pudran ahí»* → Amenazas/Violencia (deseo de sufrimiento)

---

## 4. Casos límite resueltos

| Situación | Clase | Razón |
|---|---|---|
| Sarcasmo o ironía hiriente hacia un individuo | Lenguaje Ofensivo | El sarcasmo no atenúa el insulto |
| Sarcasmo que ataca a un grupo protegido | Discurso de Odio | La precedencia manda |
| Cita o denuncia de discurso de odio ajeno | No Tóxico | El emisor no lo suscribe |
| Uso reapropiado dentro del propio grupo | No Tóxico | *«qué onda negro»* entre amigos |
| Vulgaridad afectiva salvadoreña | No Tóxico | *«qué verga, cerote, qué alegre verte»* |
| Groserías sin destinatario | Lenguaje Ofensivo | *«a la gran puta, qué calor»* |
| Chiste basado en estereotipo de grupo protegido | Discurso de Odio | El humor no neutraliza el estigma |
| Insulto a persona **por** su nacionalidad | Discurso de Odio | El eje protegido eleva la clase |
| Insulto a persona **que además** es extranjera, sin aludir al origen | Lenguaje Ofensivo | No se ataca el eje |
| Amenaza a una institución (no a personas) | Lenguaje Ofensivo | *«hay que quemar la Asamblea»* sin personas |
| Violencia contra animales | Lenguaje Ofensivo | La taxonomía cubre violencia contra personas |
| Texto ambiguo sin contexto suficiente | La menos severa | En la duda, no se sobreetiqueta |
| Emoji como único vehículo del ataque | Según el ataque | 🐒 + bandera = Discurso de Odio |

## 5. Marcadores lingüísticos salvadoreños

El voseo, los diminutivos y buena parte del léxico vulgar local **no** implican toxicidad
por sí solos. Términos como *cerote*, *maje*, *vergón*, *puta* o *verga* funcionan con
frecuencia como marcadores afectivos o de énfasis entre pares.

**Lo que decide es la intención y el destinatario, no la palabra.**

- *«Qué verga, maje, qué alegre verte»* → No Tóxico
- *«Sos un cerote de mierda»* → Lenguaje Ofensivo

Consultar `data/raw/lexicon_salvadoreno.csv` ante dudas de significado local.

## 6. Procedimiento

1. Leer el texto **completo** antes de decidir.
2. Preguntar en orden: ¿hay amenaza o celebración de daño? ¿hay ataque a un grupo
   protegido? ¿hay insulto o vulgaridad? Si las tres respuestas son no → `No Tóxico`.
3. Aplicar la precedencia de la sección 2.
4. Registrar la subclase en su columna, nunca en la de clase.
5. En caso de duda genuina, elegir la clase **menos severa** y anotarlo en observaciones.

## 7. Control de calidad

- Doble anotación independiente y **a ciegas** de cada ítem.
- Cohen's Kappa global y **por clase**. Umbral mínimo del proyecto: **κ ≥ 0.60**.
- Los desacuerdos se resuelven por **adjudicación razonada de una tercera pasada**, nunca
  promediando ni por mayoría automática.
- Toda adjudicación queda registrada con su justificación en
  `data/interim/adjudicacion_desacuerdos.csv`.
