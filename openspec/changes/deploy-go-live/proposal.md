# Proposal

## Why

Todo el código del bot existe y pasa 86 tests, pero nunca corrió contra el mundo real: login contra Moodle, Evolution con QR, envíos a WhatsApp y scheduler en el VPS están sin verificar. Sin este change, el primer digest del lunes es un salto de fe.

## What Changes

- Verificaciones vivas en el VPS (las 6 pendientes de los changes archivados): login real en ambos campus (2.1), Evolution en Docker + pairing QR (9.1), send-test al grupo de prueba (9.2), runbook de re-vinculación ejecutado (9.3), e2e con scrape real (10.2), checklist de pase al grupo general (10.3).
- Tres micro-gaps detectados en la auditoría C-01→C-09: crear `.gitignore` con `estado.json`, escritura atómica de `estado.json` en `state.py`, códigos de salida en `main.py` para cron/systemd.
- Completar alias de profesores por comisión y revisar la exclusion list antes del go-live (pregunta alta de la KB).
- Primer digest real un lunes 8:00 al grupo general como cierre.

## Capabilities

### New Capabilities
- (ninguna — change de verificación y ops; `skip_specs: true`)

### Modified Capabilities
- (ninguna — sin cambios de comportamiento especificado)

## Impact

- Sistemas: VPS propio (Docker + cron/systemd), Moodle x2 (sesiones reales), Evolution API (sesión QR del número propio), grupo de prueba y grupo general de WhatsApp.
- Código: toques mínimos (`state.py` escritura atómica, `main.py` exit codes, `.gitignore` nuevo); sin cambios de lógica de negocio.
- Riesgos: QR expira y hay que re-vincular; credenciales en el VPS solo vía `.env` (nunca en repo ni logs).
