# Moodle Urgent Watch Specification

## Purpose

Detectar entre digest semanales las entregas nuevas que vencerían antes de ser notificadas, y alertarlas de inmediato sin spamear.

## Requirements

### Requirement: Detección de entregas nuevas
El sistema SHALL registrar cada `assign id` visto con fecha de primer avistaje y fecha base de cierre (día/mes/hora) para distinguir nuevas de ya conocidas y detectar cambios. El avistaje SHALL persistirse con independencia de que la entrega se haya enviado o no: `visto` significa "ya lo vi", no "ya te avisé". Una carga del estado distinta de sana SHALL NOT convertir la corrida en un silencio: las entregas se consideran nuevas y se notifican como tales.

#### Scenario: Primer avistaje
- **WHEN** una corrida encuentra un id nunca visto con fecha de cierre parseable
- **THEN** lo marca como nuevo con timestamp de descubrimiento y guarda su cierre como base de comparación

#### Scenario: Ya conocida
- **WHEN** una corrida encuentra un id ya registrado con igual día/mes/hora de cierre que la base
- **THEN** no lo trata como nuevo aunque siga en ventana (lo cubre el digest)

#### Scenario: Avistaje independiente del envío
- **WHEN** una corrida termina con el aviso enviado o con el envío fallido
- **THEN** el avistaje de las entregas que no se enviaron queda persistido en ambos casos

#### Scenario: Estado perdido no silencia la corrida
- **WHEN** el estado persistido no existe al iniciar la corrida
- **THEN** las entregas se consideran nuevas y se notifican como tales, y la carga queda registrada como no sana (nunca un silencio silencioso)

### Requirement: Re-aviso por cambio de fecha
El sistema SHALL re-notificar en la corrida 8:00/20:00 que detecte el cambio toda entrega conocida cuyo día/mes/hora de cierre difiera de la base, con la marca `fecha de entrega modificada`, y actualizar la base **solo tras el envío exitoso**. Si el envío falla, la base SHALL quedar en el valor anterior para que la corrida siguiente vuelva a detectar el cambio.

#### Scenario: Cambio de día con margen urgente
- **WHEN** una entrega conocida pasa de vencer en 10 días a vencer en 3 días
- **THEN** se re-avisa en esa corrida con la marca y la base pasa al nuevo cierre

#### Scenario: Cambio con margen amplio
- **WHEN** una entrega conocida cambia su cierre pero el nuevo margen supera 7 días
- **THEN** no se alerta; la fecha actualizada aparece en el próximo digest y la base se actualiza igual

#### Scenario: Cambio solo de año
- **WHEN** solo cambia el año del cierre (igual día/mes/hora)
- **THEN** no se re-avisa (el año se ignora en la comparación)

#### Scenario: Segundo cambio distinto
- **WHEN** una entrega ya re-avisada vuelve a cambiar su cierre a otro valor
- **THEN** se re-avisa de nuevo (cada cambio distinto avisa una vez)

#### Scenario: Re-aviso con envío fallido
- **WHEN** la corrida detecta un cambio de fecha y el envío del aviso falla
- **THEN** la base no se actualiza y la corrida siguiente vuelve a detectar el mismo cambio y lo reintenta

### Requirement: Umbral urgente de 7 días
El sistema SHALL alertar de inmediato solo las nuevas cuyo margen `vencimiento - hoy <= 7 días`; las de mayor margen SHALL esperar al próximo digest. Las candidatas que la corrida no alerta (margen mayor a 7 días, o conocidas sin base de cierre por migración) SHALL marcarse como vistas en esa misma corrida, de modo que al entrar en la ventana de 7 días no generen una alerta por primera vez.

#### Scenario: Nueva urgente (margen corto)
- **WHEN** se descubre un martes una entrega que vence al día siguiente (margen 1)
- **THEN** se alerta en esa misma corrida

#### Scenario: Nueva al límite
- **WHEN** se descubre un martes una entrega que vence en 7 días
- **THEN** se alerta en esa misma corrida (llegaría al lunes con 1 día, insuficiente)

#### Scenario: Nueva con tiempo
- **WHEN** se descubre un martes una entrega que vence en 10 días
- **THEN** no se alerta; aparece en el digest del lunes con 4 días de margen

#### Scenario: Entrada posterior en la ventana
- **WHEN** una entrega se avistó con 10 días de margen y dos días después queda en 8 y luego en 6 días
- **THEN** sigue sin generar alerta urgente: ya fue marcada como vista al avistarse y solo la lista el digest

#### Scenario: Migración sin base de cierre
- **WHEN** una entrega conocida no tiene base de cierre registrada
- **THEN** adopta la base observada y se marca vista sin generar alerta

### Requirement: Alerta en la misma lista con resaltado
El sistema SHALL enviar la alerta urgente al mismo destino con la misma lista ordenada por fecha, encabezado `Actualización - N nueva(s)` y marca 🆕 solo en las nuevas.

#### Scenario: Una nueva
- **WHEN** hay 1 entrega nueva urgente entre 5 candidatas
- **THEN** el mensaje lleva encabezado de actualización con contador 1 y una sola marca 🆕

#### Scenario: Sin novedades
- **WHEN** una corrida del vigía no encuentra nuevas urgentes
- **THEN** no envía ningún mensaje (silencio total)

### Requirement: Ritmo 8:00 y 20:00 con digest integrado
El sistema SHALL correr el vigía a las 8:00 y 20:00 todos los días; la corrida del lunes 8:00 SHALL incluir además el digest semanal de 14 días. La marca de notificación SHALL persistirse solo tras un envío exitoso, y el avistaje SHALL persistirse siempre, aunque el envío falle. Si el envío del digest falla, el sistema SHALL registrar el digest como pendiente y la corrida siguiente SHALL reintentarlo completo, en un único envío por corrida.

#### Scenario: Corrida nocturna con hallazgo
- **WHEN** la corrida de las 20:00 descubre una urgente subida al mediodía
- **THEN** la alerta sale esa noche (punto ciego máximo ~12h)

#### Scenario: Alerta única
- **WHEN** una urgente ya fue alertada en una corrida previa
- **THEN** las corridas siguientes no la re-alertan (el digest la sigue listando sin marca)

#### Scenario: Envío fallido se reintenta
- **WHEN** el envío de una actualización falla (ok=False) y la corrida siguiente vuelve a ver la misma entrega urgente
- **THEN** la entrega no quedó marcada como notificada y se vuelve a enviar

#### Scenario: Digest fallido no genera ráfaga de nuevas
- **WHEN** el envío del digest del lunes falla
- **THEN** las candidatas quedan avistadas igual (la corrida siguiente no las marca 🆕), no se marca el digest como notificado ni se sincroniza la base, y el digest queda registrado como pendiente

#### Scenario: Reintento del digest pendiente
- **WHEN** la corrida siguiente (8:00 o 20:00, del día que sea) encuentra el digest pendiente
- **THEN** envía el digest completo de la ventana de 14 días con el encabezado de digest y sin marcas 🆕, en un único envío, incluyendo las entregas que aparecieron después del fallo sin duplicarlas

#### Scenario: El reintento del digest también falla
- **WHEN** el envío del reintento del digest falla
- **THEN** el digest queda pendiente otra vez y la corrida siguiente vuelve a intentarlo, siempre con un solo envío por corrida (sin bucle de reintentos dentro de una corrida)

#### Scenario: El reintento del digest sale bien
- **WHEN** el reintento del digest se envía con éxito (o corre en dry-run, equivalente a un envío exitoso)
- **THEN** se marca el digest como notificado, se sincroniza la base y se limpia el pendiente, y el vigía retoma su ritmo normal de 8:00 y 20:00

### Requirement: Carga del estado diagnosticable
El sistema SHALL clasificar el resultado de cargar el estado persistido como `ausente` (el archivo no existe), `vacio` (existe pero no tiene contenido o no tiene registros), `corrupto` (no decodifica, o decodifica a algo que no es un objeto de registros) u `ok`. Ante cualquier clasificación distinta de `ok` SHALL emitir un `warning` de una línea con la ruta y el motivo, y SHALL continuar la corrida con estado vacío.

#### Scenario: Estado ausente
- **WHEN** el archivo de estado no existe al iniciar la corrida
- **THEN** la carga se clasifica `ausente`, se emite un warning con la ruta, y la corrida envía igual

#### Scenario: Estado vacío
- **WHEN** el archivo de estado existe pero está en blanco o no tiene registros
- **THEN** la carga se clasifica `vacio`, se emite un warning, y la corrida envía igual

#### Scenario: Estado corrupto
- **WHEN** el archivo de estado no decodifica, o decodifica a algo que no es un objeto de registros
- **THEN** la carga se clasifica `corrupto`, se emite un warning con la ruta y el motivo, la corrida no revienta y envía igual

#### Scenario: Estado sano
- **WHEN** el archivo de estado decodifica a un objeto de registros
- **THEN** la carga se clasifica `ok` y no se emite ningún warning

#### Scenario: Warning sin secretos
- **WHEN** se registra una carga distinta de `ok`
- **THEN** la línea incluye solo la ruta y el motivo, y nunca cookies, tokens, usuario ni contraseña

### Requirement: Escritura del estado con temporal único
El sistema SHALL publicar cada escritura del estado de forma atómica a través de un archivo temporal cuyo nombre sea único por escritura (no un nombre fijo compartido), y SHALL eliminar su propio temporal si la escritura no llega a publicarse. Dos escritores concurrentes SHALL NOT compartir archivo temporal, y el archivo real SHALL conservar siempre su último contenido publicado válido.

#### Scenario: Dos escritores concurrentes
- **WHEN** dos procesos guardan el estado al mismo tiempo sobre la misma ruta
- **THEN** cada uno escribe su propio temporal y ninguno publica ni pisa el temporal del otro

#### Scenario: Temporal ajeno presente
- **WHEN** hay un temporal de otra escritura en el directorio
- **THEN** la escritura actual usa su propio temporal y el archivo real queda con JSON válido

#### Scenario: Escritura interrumpida
- **WHEN** el proceso cae entre la escritura del temporal y la publicación
- **THEN** el archivo real conserva su último contenido válido y el temporal propio se descarta
