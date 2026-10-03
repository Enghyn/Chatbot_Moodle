# WhatsApp vía Evolution API — runbook de pairing y re-vinculación

> Verificación en vivo pendiente: ejecutar estos pasos en el VPS y marcar 9.1/9.3.

## Levantar (9.1)

1. En el VPS, copiar `.env` con `EVO_API_KEY` (generar con `openssl rand -hex 32`).
2. `docker compose -f docker-compose.evolution.yml up -d`
3. Abrir el panel (puerto 8080 interno) y verificar que responde y muestra
   el estado de sesión (`connected` / `disconnected` / QR).

## Vincular número propio (pairing QR)

1. En el panel, crear instancia y mostrar el QR.
2. En el celular (número propio): WhatsApp → Dispositivos vinculados → Vincular.
3. Escanear el QR y esperar estado `connected`.
4. Desde el panel, listar grupos y copiar el JID del grupo de prueba
   (`TEST_GROUP_JID`) y luego el del grupo general (`GROUP_JID`).

## Prueba de envío (9.2)

`python -m bot_moodle.main --send-test` envía el último digest de prueba al
`TEST_GROUP_JID`. Verificar que el mensaje llega con formato intacto
(negritas, emojis, `🆕`).

## Re-vinculación (sesión caída)

1. El sender reporta `sesion/envio fallido` en el log y NO reintenta en bucle.
2. Abrir el panel → estado `disconnected` → `Logout`/eliminar sesión.
3. Generar nuevo QR y escanearlo con el número propio.
4. Re-correr en modo dry-run: `python -m bot_moodle.main --dry-run`.
