# Estado persistente (`estado.json`)

Registro por `assign id`: `{visto, notificado_urgente, notificado_digest, cierre_base}`.

## `cierre_base`

Fecha base de comparación para detectar cambios de fecha. Formato (año
ignorado en la comparación):

```json
"cierre_base": {"d": 9, "m": 10, "h": 23, "mi": 59}
```

- `d`: día del mes, `m`: mes, `h`: hora, `mi`: minuto.
- Se guarda en el primer avistaje (`mark_seen` con `due`) y se actualiza
  con `set_base` tras cada re-aviso enviado (o tras el digest que incluya
  la fecha nueva).
- La comparación ignora el año: solo día/mes/hora/minuto.

## Migración de estados viejos

Los registros creados antes de este campo no tienen `cierre_base`. En el
próximo avistaje posterior la adoptan silenciosamente del `due` observado,
sin disparar ningún aviso (ver `tests/test_date_change.py`).

Ver `src/bot_moodle/state.py`: `base_of`, `base_matches`,
`StateStore.get_base`, `StateStore.set_base`.
