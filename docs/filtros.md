# Regla temporal del bot

Solo se notifican vencimientos **no vencidos dentro de 14 días** desde el día
de ejecución, ordenados de más urgente a menos urgente (fecha fin ascendente).

## Casos verificados (reloj fijo: 29 sept 2026, 8:00)

1. **Incluye 3 días**: vence el 2 oct 2026 → candidata (entra en ventana).
2. **Excluye 20 días**: vence el 19 oct 2026 → se guarda sin notificar.
3. **Excluye vencida**: UML (Cierre 25 de agosto de 2026) evaluado el 29 sept →
   no aparece en el mensaje de esa semana.

## Borde

- Vence exactamente a los 14 días → entra.
- Vence a los 14 días + 1 segundo → espera.

Ver `tests/test_temporal.py` y `tests/test_docs_filtros.py`: los ejemplos de
este doc coinciden con los tests.
