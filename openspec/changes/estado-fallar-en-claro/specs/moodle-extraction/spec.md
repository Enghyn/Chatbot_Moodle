# Spec Delta

## MODIFIED Requirements

### Requirement: Solo entregas con fecha parseable
El sistema SHALL considerar únicamente actividades cuyo `div[data-region=activity-dates]` contenga una fecha de cierre reconocible; las que no la tengan SHALL descartarse, pero el descarte SHALL quedar registrado en un log de nivel warning con el identificador, el título, el tipo de módulo, el curso, la sección y el motivo del descarte, sin exponer secretos. El descarte SHALL ser explícito y diagnosticable, nunca silencioso. El techo de detalle SHALL aplicarse **por curso**: cada curso emite hasta 50 warnings de detalle y los descartes que exceden ese techo sólo se cuentan. Cada corrida SHALL cerrar con un único resumen con las secciones recorridas, las actividades encontradas, las candidatas, los descartes por motivo, los descartes por curso, la duración y el estado con el que se cargó el estado persistido (`estado=ausente|vacio|corrupto|ok`).

#### Scenario: Actividad sin fecha
- **WHEN** una entrega no tiene `activity-dates` con cierre (ej. TP Unidad 4 BD2, FastApi)
- **THEN** no aparece en el mensaje ni genera error

#### Scenario: Descarte registrado
- **WHEN** una actividad candidata se descarta por no tener fecha de cierre parseable
- **THEN** el sistema emite un warning que identifica la actividad (id, título, tipo de módulo), el curso y la sección, junto con el motivo del descarte, de modo que su ausencia en el mensaje sea explicable, y el mensaje al grupo no cambia

#### Scenario: Volumen de descartes
- **WHEN** una corrida descarta 60 actividades en el curso `723`, 55 en el curso `743` y 11 en el curso `14`, y el curso `14` es el último recorrido
- **THEN** cada curso emite su propio detalle hasta el umbral (50 + 50 + 11 = 111 líneas de detalle, no 50), el curso `14` emite sus 11 líneas aunque los dos anteriores hayan agotado su cuota, y el cierre informa `descartes_detalle_omitido=15` — la suma de los excedentes por curso `(60−50) + (55−50) + 0`

#### Scenario: Resumen de corrida
- **WHEN** termina el recorrido de secciones y detalles de una corrida
- **THEN** el sistema emite un único resumen en nivel info, interpolado en una sola línea, con `secciones=`, `actividades=`, `candidatas=`, `descartes_por_motivo={'sin_fecha': 148, 'sin_id': 113}`, `descartes_por_curso={'14': 11, '723': 130, '743': 120}`, `duracion_s=98.6`, —sólo si hubo truncamiento— `descartes_detalle_omitido=N` y, siempre como último campo de la línea, `estado=`; las claves de curso salen ordenadas de forma determinista, y `duracion_s=` se parsea como número real (`float(m.split("duracion_s=")[1].split()[0])`)

#### Scenario: Estado del estado persistido en el cierre
- **WHEN** la corrida arrancó con el estado persistido ausente, vacío, corrupto o sano
- **THEN** la línea de cierre termina en exactamente uno de `estado=ausente`, `estado=vacio`, `estado=corrupto` o `estado=ok`, de modo que la pérdida del estado se lea en el log en segundos, y el mensaje al grupo no cambia

#### Scenario: Descarte sin curso identificable
- **WHEN** un descarte llega sin `course_id` (vacío o ausente) porque el target no lo trae
- **THEN** se contabiliza bajo la clave `'?'` en `descartes_por_curso`, sin inventar un id de curso ni descartar la línea de detalle

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
