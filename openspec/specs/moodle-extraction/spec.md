# Moodle Extraction Specification

## Purpose

Define la extracción y filtrado de entregas con fecha desde Moodle como contrato de comportamiento para el futuro bot de avisos por WhatsApp.

## Requirements

### Requirement: Autenticación por campus con cuenta estudiante
El sistema SHALL autenticarse en cada campus con credenciales propias de estudiante (comisión 4), una sesión por campus, login nativo sin captcha.

#### Scenario: Login en ambos campus
- **WHEN** inicia el ciclo semanal con credenciales configuradas por campus
- **THEN** obtiene una sesión válida en Campus 1 (Inglés + BD2) y otra en Campus 2 (Programación)

#### Scenario: Credenciales inválidas
- **WHEN** un campus rechaza user+pass
- **THEN** el ciclo reporta el campus fallido y continúa con el otro sin notificar datos parciales como completos

### Requirement: Recorrido completo de secciones
El sistema SHALL recorrer TODAS las secciones de cada curso (índice drawer + tabs), no solo la vista de un tema puntual.

#### Scenario: Curso multi-sección
- **WHEN** un curso tiene N secciones con actividades
- **THEN** todas las actividades con link de las N secciones son candidatas (las `isrestricted` sin link se excluyen)

### Requirement: Solo entregas con fecha parseable
El sistema SHALL considerar únicamente actividades cuyo `div[data-region=activity-dates]` contenga fecha de cierre reconocible; las sin fecha SHALL descartarse en silencio.

#### Scenario: Actividad sin fecha
- **WHEN** una entrega no tiene `activity-dates` con cierre (ej. TP Unidad 4 BD2, FastApi)
- **THEN** no aparece en el mensaje ni genera error

#### Scenario: Alias de etiquetas por campus
- **WHEN** la etiqueta es `Cierre`, `Cierra`, `Vence`, `Fecha de entrega` o `Fecha límite`
- **THEN** se interpreta como fecha fin; `Apertura`, `Abrió` o `Abre` se interpreta como inicio y se ignora para vencimiento

#### Scenario: Formato español sin datetime
- **WHEN** la fecha es texto tipo `martes, 25 de agosto de 2026, 00:00`
- **THEN** se normaliza a fecha real con mapa de meses ES; sin atributo machine como respaldo

### Requirement: Filtro temporal de dos semanas y orden por urgencia
El sistema SHALL incluir solo vencimientos no vencidos dentro de 14 días desde el día de ejecución, ordenados de más urgente a menos urgente.

#### Scenario: Ventana de inclusión
- **WHEN** una entrega vence en 3 días y otra en 20 días
- **THEN** solo la de 3 días es candidata; la de 20 se guarda sin notificar

#### Scenario: Vencida se elimina
- **WHEN** una entrega venció antes del día de ejecución (ej. UML Cierre 25 ago evaluado el 29 sept)
- **THEN** no aparece en el mensaje de esa semana

#### Scenario: Orden
- **WHEN** hay 3 candidatas con distintos vencimientos
- **THEN** el mensaje las ordena ascendente por fecha fin

### Requirement: Filtro de comisión por nombre
El sistema SHALL aplicar filtro de comisión solo en BD2 y Programación; Inglés SHALL incluirse sin filtro.

#### Scenario: Compartida con comisión 4
- **WHEN** el título menciona a la 4 junto a otras (`COM4,COM3,COM1`, `Com3 y Com4`, `2prog3 y 2prog4`)
- **THEN** se incluye

#### Scenario: Solo otra comisión
- **WHEN** el título menciona solo otra (`2prog3` solo, `Prof Yácomo`, Com1)
- **THEN** se excluye

#### Scenario: Sin marca por defecto inclusivo
- **WHEN** el título no menciona comisión
- **THEN** se incluye como general, salvo que su ID/título figure en la lista de exclusión explícita (ej. UML id=1457 de Com1)

### Requirement: Agrupación y omisión de vacíos
El sistema SHALL agrupar candidatas por Curso > Sección-verbatim > Apartado-verbatim y SHALL omitir apartados sin entregas y secciones sin apartados con entregas.

#### Scenario: Apartado vacío
- **WHEN** un apartado no tiene candidatas en ventana
- **THEN** no se muestra su encabezado

#### Scenario: Nombres verbatim
- **WHEN** la sección es `UNIDAD 1: FASTAPI` duplicada o `Actividades 🚀` vs `Práctica 💻`
- **THEN** se muestra tal cual, sin normalizar ni reordenar por número

#### Scenario: Semana sin vencimientos
- **WHEN** ningún curso tiene candidatas en ventana
- **THEN** el sistema produce un resultado vacío tipificado (silencio o aviso "sin vencimientos", a decidir en capa de envío)
