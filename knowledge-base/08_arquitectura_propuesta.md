# Arquitectura Propuesta

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|--------|--------------|---------|
| Pipeline por etapas | `scrape → dates → filters → grouping → formatting → sender` | Cada filtro es testeable aislado con fixtures |
| Single-shot por id | `watcher` + `estado.json` | Evita spam de re-alertas del vigía |
| Adapter de sesión | `session.py` (Moodle), `sender.py` (Evolution) | Encierra lo frágil (login, protocolo WA) tras interfaces |
| Fail-open por campus | `cycle.py` | Un campus caído no voltea la corrida del otro |
| Secrets por entorno | `config.py` + `.env` | Credenciales personales nunca en código |

## Estructura de directorios

```
bot-moodle/
├── src/bot_moodle/
│   ├── config.py, session.py      # env + login x2 campus
│   ├── sections.py, activities.py # recorrido + extracción
│   ├── breadcrumbs.py             # curso/sección/apartado verbatim
│   ├── dates.py, filters.py       # parser ES + ventana 14d
│   ├── comision.py                # alias + exclusion list
│   ├── grouping.py, formatting.py # agrupación + plantillas
│   ├── state.py, watcher.py       # estado.json + umbral 7d
│   ├── sender.py                  # POST Evolution, sin reintentos
│   ├── scrape.py, cycle.py        # pipeline + tipos de corrida
│   ├── scheduler.py, main.py      # 8:00/20:00, --dry-run, --send-test
├── tests/ (+ fixtures: 8 HTML + manifest.json)
├── docs/ (filtros.md, whatsapp.md)
├── knowledge-base/ (esta KB)
├── openspec/ (specs + archive del change)
├── docker-compose.evolution.yml
└── estado.json (runtime, no versionado)
```

## Seguridad

- Autenticación: sesiones Moodle propias; API key en Evolution (puerto interno, no expuesto).
- Autorización: sin usuarios internos; solo el operador toca VPS y panel.
- Validación de input: parseo defensivo (alias, meses ES, `setiembre/sep/set`); default NO-notificar (RN-GLB-01).
- Secrets management: solo env vars; `.env` fuera del repo; rotación = cambio de password rompe ambas sesiones (secreto compartido).

## Variables de entorno

| Variable | Descripción | Ejemplo | Sensible |
|----------|-------------|---------|----------|
| `MOODLE_C1_URL` | Base Campus 1 | `https://campusvirtual.frm.utn.edu.ar` | N |
| `MOODLE_C1_USER` / `MOODLE_C1_PASS` | Cuenta propia campus 1 | — | Y |
| `MOODLE_C2_URL` | Base Campus 2 | `https://campustest.frm.utn.edu.ar` | N |
| `MOODLE_C2_USER` / `MOODLE_C2_PASS` | Cuenta propia campus 2 (misma clave) | — | Y |
| `EVO_BASE_URL` | Evolution interno | `http://localhost:8080` | N |
| `EVO_API_KEY` | Key del servicio Evolution | generada con `openssl rand -hex 32` | Y |
| `GROUP_JID` | Grupo general destino | `<id>@g.us` | N |
| `TEST_GROUP_JID` | Grupo solo-propio de pruebas | `<id>@g.us` | N |
