# Spec Delta

## MODIFIED Requirements

### Requirement: Recorrido completo de secciones
El sistema SHALL recorrer TODAS las secciones de cada curso (índice drawer + tabs), no solo la vista de un tema puntual. El recorrido SHALL ser independiente del nombre de las tabs o secciones: dos secciones con el mismo título se recorren ambas.

#### Scenario: Curso multi-sección
- **WHEN** un curso tiene N secciones con actividades
- **THEN** todas las actividades con link de las N secciones son candidatas (las `isrestricted` sin link se excluyen)

#### Scenario: Tabs homónimas en el mismo curso
- **WHEN** un curso tiene varias secciones con el mismo título (ej. tres tabs "Práctica 💻" en el curso 14: FastAPI, SQLModel, Relaciones y Estado)
- **THEN** cada sección se recorre por su índice y las actividades de todas ellas llegan al pipeline

### Requirement: Solo entregas con fecha parseable
El sistema SHALL considerar únicamente actividades cuyo `div[data-region=activity-dates]` contenga una fecha de cierre reconocible; las que no la tengan SHALL descartarse, pero el descarte SHALL quedar registrado en un log de nivel warning con el identificador, el título, el tipo de módulo, el curso, la sección y el motivo del descarte, sin exponer secretos. El descarte SHALL ser explícito y diagnosticable, nunca silencioso. Cuando una corrida supere un umbral de descartes, el sistema SHALL emitir un resumen agregado con el conteo por motivo en lugar del detalle uno por uno, y SHALL emitir un resumen de cierre de corrida con las secciones recorridas, las actividades encontradas, las candidatas, los descartes por motivo y la duración.

#### Scenario: Actividad sin fecha
- **WHEN** una entrega no tiene `activity-dates` con cierre (ej. TP Unidad 4 BD2, FastApi)
- **THEN** no aparece en el mensaje ni genera error

#### Scenario: Descarte registrado
- **WHEN** una actividad candidata se descarta por no tener fecha de cierre parseable
- **THEN** el sistema emite un warning que identifica la actividad (id, título, tipo de módulo), el curso y la sección, junto con el motivo del descarte, de modo que su ausencia en el mensaje sea explicable, y el mensaje al grupo no cambia

#### Scenario: Volumen de descartes
- **WHEN** una corrida descarta más actividades que el umbral configurado
- **THEN** el sistema emite un resumen con el conteo de descartes por motivo en lugar de un warning por actividad, para que el log siga siendo legible

#### Scenario: Resumen de corrida
- **WHEN** termina el recorrido de secciones y detalles de una corrida
- **THEN** el sistema emite un único resumen con las secciones recorridas, las actividades encontradas, las candidatas, los descartes por motivo y la duración de la corrida

#### Scenario: Log sin secretos
- **WHEN** el sistema registra un descarte o un resumen de corrida
- **THEN** la entrada no contiene cookies, token de sesión, usuario ni contraseña

#### Scenario: Alias de etiquetas por campus
- **WHEN** la etiqueta es `Cierre`, `Cierra`, `Vence`, `Fecha de entrega` o `Fecha límite`
- **THEN** se interpreta como fecha fin; `Apertura`, `Abrió` o `Abre` se interpreta como inicio y se ignora para vencimiento

#### Scenario: Formato español sin datetime
- **WHEN** la fecha es texto tipo `martes, 25 de agosto de 2026, 00:00`
- **THEN** se normaliza a fecha real con mapa de meses ES; sin atributo machine como respaldo

#### Scenario: Fecha ilegible
- **WHEN** el texto de la fecha no corresponde a ningún formato reconocido
- **THEN** el default es NO notificar: la actividad se descarta y queda registrada en el warning de descarte

## ADDED Requirements

### Requirement: Identidad de la actividad por módulo de curso
El sistema SHALL identificar cada actividad por el identificador de su course module (`data-id` o `id="module-<cmid>"` del propio contenedor de la actividad, o `mod/*/view.php?id=<cmid>` de un link del contenedor), y SHALL NOT tomar el parámetro `id` de una URL `course/view.php`, que corresponde al curso y no a la actividad. Cuando no haya ninguna fuente válida de identidad, el sistema SHALL descartar la actividad y SHALL registrar el descarte con su motivo.

#### Scenario: Anchor con id de curso
- **WHEN** el único link con parámetro `id` de un contenedor de actividad es un ancla `course/view.php?id=14&section=40#module-1522`
- **THEN** la actividad no se registra con el identificador del curso `14`, sino con el identificador del módulo al que apunta el ancla

#### Scenario: Contenedor con data-id
- **WHEN** el contenedor de la actividad expone `data-id="1833"` / `id="module-1833"` (fuente autoritativa del DOM)
- **THEN** ese valor es el identificador de la actividad, con independencia de los links que contenga

#### Scenario: Actividad sin identidad determinable
- **WHEN** un contenedor de actividad no expone `data-id`, ni `id="module-N"`, ni un link a `mod/*/view.php?id=`, ni un ancla `#module-N`
- **THEN** la actividad se descarta y el descarte queda registrado con su motivo

#### Scenario: Persistencia de la clave de estado
- **WHEN** una actividad se registra como candidata con su cmid
- **THEN** la clave persistida en el estado es ese cmid y no el identificador del curso, de modo que el id de un curso no colisiona con el id de una actividad de otro curso