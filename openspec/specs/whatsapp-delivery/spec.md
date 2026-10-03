# WhatsApp Delivery Specification

## Purpose

Enviar el digest semanal y las alertas urgentes al grupo general de alumnos desde el número propio mediante Evolution API.

## Requirements

### Requirement: Envío grupal único por mensaje
El sistema SHALL enviar cada digest o alerta como un único mensaje de texto libre al grupo configurado; no SHALL enviar privados por alumno.

#### Scenario: Digest al grupo
- **WHEN** la corrida del lunes 8:00 produce la lista ordenada
- **THEN** se envía un solo mensaje al JID del grupo general

#### Scenario: Sin duplicación por alumno
- **WHEN** el grupo tiene N miembros
- **THEN** se produce exactamente 1 envío (sin fan-out por miembro)

### Requirement: Encabezado Comisión 4 y texto libre
El sistema SHALL encabezar cada mensaje con la comisión destinataria y SHALL usar texto libre con formato (negritas, listas, emojis verbatim de Moodle, 🆕 en urgentes).

#### Scenario: Grupo mixto
- **WHEN** el grupo general incluye otras comisiones
- **THEN** el encabezado aclara Comisión 4 para evitar confusión con avisos de otras comisiones

### Requirement: Sesión personal vía Evolution API
El sistema SHALL enviar a través de Evolution API con sesión vinculada por QR del número propio; ante sesión caída SHALL reportar y no SHALL reintentar a ciegas.

#### Scenario: Sesión válida
- **WHEN** la sesión está vinculada y hay mensaje a enviar
- **THEN** se hace POST interno con JID destino y texto, y se registra éxito/fracaso

#### Scenario: Sesión caída
- **WHEN** Evolution reporta sesión no vinculada o error de auth
- **THEN** no se reintenta el envío en bucle; se registra el fallo para re-vinculación manual desde el panel

### Requirement: Grupo de prueba antes del general
El sistema SHALL soportar JID de destino configurable para probar primero en un grupo solo-propio antes de apuntar al general.

#### Scenario: Prueba inicial
- **WHEN** el destino configurado es el grupo de prueba
- **THEN** ningún mensaje llega al grupo general hasta cambiar la configuración
