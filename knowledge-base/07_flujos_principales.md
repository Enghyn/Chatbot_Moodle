# Flujos Principales

## Flujo 1: Digest del lunes 8:00
**Disparador**: cron/APScheduler. **Actor**: sistema (sin intervención).

**Pasos**:
1. `[scheduler]` dispara corrida tipo digest.
2. `[session]` loguea en Campus 1 y 2 (si uno falla: log + sigue con el otro).
3. `[scrape]` recorre secciones de Inglés, BD2 y Prog3; extrae actividades con link.
4. `[dates]` parsea `activity-dates` (alias ES); sin fecha se descarta.
5. `[filters]` aplica ventana 14 días + comisiones + exclusion list.
6. `[watcher]` marca vistos en `estado.json` (el digest no dispara 🆕).
7. `[formatting]` agrupa (orden fijo Prog→BD2→Inglés) y omite vacíos; si nada: aviso corto.
8. `[sender]` POST a Evolution → grupo; registra éxito/fracaso.

**Casos de error**:
- Login rechazado → reporta campus, sigue con el otro (RN-TMP-03).
- Sesión WA caída → log, sin reintentos; re-vinculación manual (RN-ENV-02).

## Flujo 2: Vigía 8:00/20:00 con hallazgo urgente
**Disparador**: cron. **Actor**: sistema.

**Pasos**: 1–5 iguales al digest; 6. `[watcher]` detecta id nuevo con margen ≤ 7 días → marca `notificado_urgente`; 6b. si el id es conocido pero su día/mes/hora de cierre cambió vs `estado.json` → marca `fecha de entrega modificada` y actualiza la base; 7. mensaje tipo actualización con 🆕 en nuevas y marca de modificada donde corresponda; 8. envío único.

**Casos de error**:
- Sin novedades → silencio total (cero mensajes).
- Nueva con margen > 7 → se registra vista y espera al lunes.

## Flujo 3: Sesión WhatsApp caída
**Disparador**: error de auth en Evolution.

**Pasos**:
1. `[sender]` loguea fallo y NO reintenta.
2. Operador abre panel → `disconnected` → logout → nuevo QR → escanea.
3. Re-corre dry-run (`--dry-run`) para validar.

## Flujo 4: Go-live al grupo general
**Disparador**: decisión del operador tras 48h de sesión estable.

**Pasos**:
1. Verificar checklist (JID final, sesión 48h, exclusion list revisada).
2. Cambiar destino de `TEST_GROUP_JID` a `GROUP_JID`.
3. Primer digest un lunes 8:00; observar recepción y formato.
