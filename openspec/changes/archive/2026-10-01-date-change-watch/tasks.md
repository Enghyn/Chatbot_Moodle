# Tasks

## 1. Estado con fecha base

- [x] 1.1 Agregar `cierre_base` (día/mes/hora) al registro por id en `state.py` con migración de estados viejos (adoptan la base del primer avistaje sin alertar) y verificar con tests que un estado sin el campo migra sin disparar avisos
- [x] 1.2 Documentar el nuevo campo en `docs/` o README interno del módulo y verificar que la doc describe migración y formato

## 2. Rama de cambio en el watcher

- [x] 2.1 Implementar en `watcher.py` la comparación contra la base ignorando el año, con tests de reloj fijo que verifican: cambia día → re-avisa; cambia hora → re-avisa; cambia solo año → silencio; sin cambios → silencio
- [x] 2.2 Implementar regla de margen del re-aviso (≤ 7 días inmediato, mayor al digest con base actualizada) y single-shot por cambio (segundo valor distinto vuelve a avisar), con tests que verifican los tres casos más la no-repetición

## 3. Marca y verificación integrada

- [x] 3.1 Agregar la marca `fecha de entrega modificada` en `formatting.py` solo en re-avisos (conviviendo con 🆕 de nuevas) y verificar byte-a-byte con test golden que digest/actualización/modificada se distinguen
- [x] 3.2 Corrida integrada en dry-run con un cambio simulado y verificar que el mensaje sale una vez con la marca y la base queda actualizada
