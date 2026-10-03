# Actores y Roles

## Actores del sistema

| Actor | Descripción | Cómo interactúa |
|-------|-------------|-----------------|
| Operador | Estudiante de comisión 4, dueño del número y del VPS | Configura `.env`, vincula QR, mantiene alias/exclusion list, atiende sesión caída |
| Compañeros | Miembros del grupo general de WhatsApp (puede incluir otras comisiones) | Solo leen los mensajes; no operan el bot |
| Profesores | Cargan (o no) fechas en Moodle | Sin interacción directa; el bot lee `activity-dates` cuando existe |
| Admins Moodle | Gestionan campus, grupos y web services | Ninguna (no se les pide nada: sin tokens, sin cuentas fantasma) |

## RBAC — Matriz de permisos

Sistema sin usuarios internos ni login propio. Matriz mínima:

| Rol | Recurso | Permisos |
|-----|---------|----------|
| Operador | `.env` / VPS / Evolution panel | Lectura-escritura total |
| Operador | `estado.json`, exclusion list | Lectura-escritura |
| Compañeros | Mensajes del grupo | Solo lectura |
| Nadie | Credenciales Moodle ajenas | Sin acceso (cuenta propia únicamente) |

## Rutas públicas

No aplica (sin frontend ni API pública). Superficie expuesta: panel Evolution en puerto interno del VPS (proteger con API key, no exponer a internet).
