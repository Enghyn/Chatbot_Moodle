# Tasks

## 1. Plano y micro-gaps (ejecutable local + VPS)

- [x] 1.1 Crear `.gitignore` con `estado.json`, `.env` y `__pycache__/` y verificar que `git status` (o inspección) no muestra secretos ni estado
- [x] 1.2 Implementar escritura atómica de `estado.json` en `state.py` (tmp + rename) con tests que verifican que un corte a mitad de escritura nunca deja JSON corrupto
- [x] 1.3 Agregar códigos de salida en `main.py` (`0` éxito, `1` fallo de campus/envío, `2` error de configuración) con tests que verifican cada código y documentarlos para cron/systemd
- [x] 1.4 En el VPS: copiar `.env.example` a `.env`, completar las 8 variables (clave generada para `EVO_API_KEY`) y verificar que `python -m bot_moodle.main --once --dry-run` loguea sesión válida en ambos campus (cierra 2.1)

## 2. WhatsApp en vivo (VPS)

- [x] 2.1 Levantar Evolution (`docker compose -f docker-compose.evolution.yml up -d`), vincular QR con el número propio y verificar estado `connected` en el panel (cierra 9.1)
- [x] 2.2 Ejecutar `python -m bot_moodle.main --send-test` y verificar que el mensaje llega al grupo de prueba con formato intacto (negritas, emojis, 🆕) (cierra 9.2)
- [ ] 2.3 Ejecutar el runbook de re-vinculación de `docs/whatsapp.md` (logout → QR nuevo → dry-run) y verificar que cada paso funciona tal cual está escrito (cierra 9.3)

## 3. E2E y go-live

- [x] 3.1 Completar alias de profesores por comisión y revisar la exclusion list, y verificar contra los grupos reales que no falta ninguna marca ajena
- [x] 3.2 Corrida e2e con scrape real al grupo de prueba y verificar visualmente orden fijo, omisión de vacíos/sin fecha/vencidas/ajenas y marcas 🆕/modificada (cierra 10.2)
- [x] 3.3 Checklist de pase (JID final, sesión 48h estable, exclusion list revisada) y primer digest real un lunes 8:00 al grupo general (cierra 10.3)
