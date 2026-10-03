# Design

## Context

Ver proposal.md. El código existe (86 tests verdes) pero jamás tocó infraestructura real. Este change es verificación + 3 micro-gaps + go-live. Referencias operativas: `docs/whatsapp.md` (runbook QR), `docs/filtros.md` (casos temporales), `docs/estado.md` (formato de estado).

## Goals / Non-Goals

**Goals:**
- Verificar en el VPS cada integración viva (Moodle x2, Evolution, envíos, scheduler) con comandos concretos y criterios observables.
- Cerrar los 3 micro-gaps sin cambiar lógica de negocio.
- Dejar el bot corriendo con primer digest real un lunes 8:00.

**Non-Goals:**
- Cambios de scraping, filtros, formato o watcher (si el vivo expone un bug, va a change nuevo).
- Cuenta business, Cloud API o multidifusión (se mantiene A2 sesión personal).

## Decisions

### 1. Verificación por comandos, no por inspección
Por qué: lo único no probado es el mundo real (red, QR, grupos). Cada tarea define comando + señal observable de éxito (log, mensaje recibido, estado `connected`).

### 2. Micro-gaps adentro del go-live, no en changes propios
Por qué: son 30 minutos en total (`.gitignore`, escritura atómica tmp+rename en `state.py`, `sys.exit` codes en `main.py`) y solo tienen sentido verificados en el VPS. Alternativa (3 changes): burocracia sin valor.

### 3. Orden: plano primero, red después
`.env` + dry-run de login antes que Docker/QR (si Moodle rechaza, no tiene sentido vincular WhatsApp). Grupo de prueba antes que general; 48h de sesión estable antes del primer digest real.

## Risks / Trade-offs

- [QR expira a mitad del go-live] → Mitigación: runbook 9.3 ejecutado antes del primer digest; ventana de 48h de estabilidad como gate.
- [Credenciales en el VPS] → Mitigación: `.env` creado a mano en el servidor (nunca viaja por git ni chat); `openssl rand -hex 32` para `EVO_API_KEY`.
- [Primer digest con datos inesperados] → Mitigación: e2e 10.2 al grupo de prueba con verificación visual antes de apuntar al general.
