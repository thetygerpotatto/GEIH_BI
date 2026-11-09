# Historias de usuario: GEIH_BI

Sistema de Business Intelligence para el análisis y predicción del mercado laboral en Colombia (GEIH 2022–2025).

## Roles

| Rol | Descripción |
|---|---|
| **Administrador** | Gestiona usuarios y roles, ejecuta el proceso ETL, supervisa la calidad de los datos y la bitácora del sistema. |
| **Analista** | Explora el dashboard completo: todos los filtros, estadística descriptiva, modelos predictivos y exportación de datos. |
| **Gerente** | Consulta el tablero descriptivo y el resumen ejecutivo de proyecciones para apoyar la toma de decisiones. No accede a la configuración de modelos ni a la administración. |

## Convenciones

- **Prioridad:** Alta / Media / Baja.
- **Estimación:** puntos de historia (1, 2, 3, 5, 8).
- **Iteración 1** (semanas 9–12, entrega 09-11-2026): prototipo con la mitad de las historias.
- **Iteración 2** (semanas 13–16, entrega 09-12-2026): resto de historias y aplicación completa.
- **Estado:** Pendiente / En progreso / Hecha.
- Todas las cifras de población se expanden con el factor `FEX_C18` y las tasas siguen la metodología DANE.

---

## Acceso y navegación

### Historia de usuario: 1. Iniciar sesión
Como **usuario del sistema** deseo iniciar sesión con mi usuario y contraseña, para acceder solo a las funcionalidades de mi rol.

**Criterios de aceptación**
- Con credenciales válidas se ingresa al menú principal del rol.
- Con credenciales inválidas se muestra un mensaje genérico ("Usuario o contraseña incorrectos") sin revelar cuál dato falló.
- Las contraseñas se almacenan cifradas (bcrypt), nunca en texto plano.
- Ninguna página del dashboard es accesible sin sesión activa.

Prioridad: Alta · Estimación: 3 · Iteración: 1 · Estado: Hecha

### Historia de usuario: 2. Menú según rol
Como **usuario autenticado** deseo ver un menú con las opciones de mi rol, para encontrar rápidamente lo que puedo hacer.

**Criterios de aceptación**
- El menú del Administrador, del Analista y del Gerente muestra únicamente las opciones de la matriz de acceso (ver final del documento).
- Si un usuario intenta abrir una página que no corresponde a su rol, se le niega el acceso y se registra el intento.

Prioridad: Alta · Estimación: 3 · Iteración: 1 · Estado: En progreso (el menú muestra solo las páginas del rol y las demás no se pueden abrir; falta registrar los intentos de acceso a páginas no permitidas)

### Historia de usuario: 3. Cerrar sesión
Como **usuario autenticado** deseo cerrar sesión, para que nadie más use mi cuenta en el equipo.

**Criterios de aceptación**
- Al cerrar sesión se invalida la sesión y se regresa a la pantalla de inicio de sesión.
- La sesión expira automáticamente tras 30 minutos de inactividad.

Prioridad: Media · Estimación: 1 · Iteración: 1 · Estado: Hecha

---

## Administración

### Historia de usuario: 4. Crear usuarios
Como **administrador** deseo crear usuarios y asignarles un rol, para controlar quién usa la aplicación.

**Criterios de aceptación**
- El formulario exige usuario único, nombre, contraseña (mínimo 8 caracteres) y rol.
- No se permite crear un usuario con un nombre ya existente.
- El nuevo usuario puede iniciar sesión inmediatamente con el rol asignado.

Prioridad: Alta · Estimación: 3 · Iteración: 1 · Estado: Hecha (también por CLI `python -m geih_bi.cli create-user`)

### Historia de usuario: 5. Editar y desactivar usuarios
Como **administrador** deseo editar el rol de un usuario o desactivarlo, para mantener actualizados los permisos del equipo.

**Criterios de aceptación**
- Un usuario desactivado no puede iniciar sesión.
- El administrador no puede desactivarse a sí mismo ni dejar el sistema sin administradores.

Prioridad: Media · Estimación: 2 · Iteración: 2 · Estado: En progreso (el controlador ya desactiva usuarios con sus reglas y el login rechaza a los inactivos; falta la vista y la edición del rol)

### Historia de usuario: 6. Procesar los archivos de la GEIH
Como **administrador** deseo ejecutar la extracción y transformación de los archivos mensuales del DANE, para preparar los datos de 2022 a 2025 sin hacerlo a mano.

**Criterios de aceptación**
- Se procesan los 48 archivos mensuales aunque tengan separadores, nombres y columnas distintos.
- Se integran los módulos Características generales, Fuerza de trabajo, Ocupados y No ocupados por persona.
- El resultado tiene al menos 1.000.000 de registros.

Prioridad: Alta · Estimación: 8 · Iteración: 1 · Estado: Hecha (CLI `python -m geih_bi.etl process`; 48 meses, 3.427.494 registros)

### Historia de usuario: 7. Cargar los datos a MongoDB
Como **administrador** deseo cargar los datos procesados en la base de datos, para que el dashboard los consulte.

**Criterios de aceptación**
- Se crean el hecho `personas_mes`, el cubo `cubo_mensual` y las dimensiones `dim_*`.
- Recargar un mes reemplaza sus datos y no genera duplicados.
- Cada carga queda registrada en `etl_ejecuciones`.

Prioridad: Alta · Estimación: 5 · Iteración: 1 · Estado: Hecha (CLI `python -m geih_bi.etl load`)

### Historia de usuario: 8. Informe de calidad de datos
Como **administrador** deseo ver un informe de calidad por mes, para saber si los datos cargados son confiables.

**Criterios de aceptación**
- Por cada mes se muestran: filas de entrada por módulo, duplicados eliminados, registros huérfanos, registros sin factor de expansión, valores anulados, filas de salida y TD calculada.
- Se resaltan los meses que no superan las reglas de validación (FT = OCI + DSI, ocupados dentro de la PET, TD plausible).

Prioridad: Media · Estimación: 3 · Iteración: 1 · Estado: En progreso (la vista "Calidad de datos" ya existe; falta mostrar las filas de entrada de Fuerza de trabajo, Ocupados y No ocupados, hoy solo muestra Características)

### Historia de usuario: 9. Bitácora del sistema
Como **administrador** deseo consultar la bitácora de ejecuciones ETL y de inicios de sesión, para auditar el uso del sistema.

**Criterios de aceptación**
- Se listan fecha, usuario y resultado de cada inicio de sesión (exitoso o fallido).
- Se listan fecha, periodos y documentos de cada ejecución ETL.

Prioridad: Baja · Estimación: 2 · Iteración: 2 · Estado: En progreso (los inicios de sesión y las cargas ETL ya se registran en `bitacora_accesos` y `etl_ejecuciones`; falta la vista)

---

## Estadística descriptiva: métricas

### Historia de usuario: 10. Tasas principales del mercado laboral
Como **gerente** deseo ver la tasa de desempleo (TD), la tasa de ocupación (TO) y la tasa global de participación (TGP) del periodo seleccionado, para conocer el estado actual del mercado laboral.

**Criterios de aceptación**
- Se muestran como tarjetas con su valor en porcentaje y la variación frente al mismo mes del año anterior.
- Los valores nacionales coinciden con los boletines del DANE (±0,1 p.p.).

Prioridad: Alta · Estimación: 3 · Iteración: 1 · Estado: Hecha (TD nacional calculada: ene-2024 12,7 %, dic-2024 9,1 %, ene-2025 11,6 %)

### Historia de usuario: 11. Población por condición laboral
Como **gerente** deseo ver cuántas personas están ocupadas, desocupadas y fuera de la fuerza de trabajo, para dimensionar el tamaño de cada grupo.

**Criterios de aceptación**
- Se muestran las cifras expandidas (en miles de personas).
- Si se seleccionan varios meses, se muestra el promedio mensual.

Prioridad: Alta · Estimación: 2 · Iteración: 1 · Estado: Hecha

### Historia de usuario: 12. Ingreso laboral
Como **analista** deseo ver el ingreso laboral promedio y mediano de los ocupados, para analizar las condiciones salariales.

**Criterios de aceptación**
- Solo se consideran ocupados con ingreso mayor a cero.
- Ambas cifras están ponderadas por el factor de expansión.

Prioridad: Media · Estimación: 3 · Iteración: 2 · Estado: Pendiente (el cubo ya trae las sumas de ingreso; la mediana tendrá que calcularse sobre `personas_mes`)

### Historia de usuario: 13. Tasa de informalidad
Como **gerente** deseo ver el porcentaje de ocupados que no cotizan a pensión, para identificar la magnitud de la informalidad laboral.

**Criterios de aceptación**
- Se calcula sobre los ocupados con dato de cotización; los pensionados se cuentan como formales.
- Se indica en pantalla que es una aproximación (proxy) a la definición oficial del DANE.

Prioridad: Media · Estimación: 2 · Iteración: 2 · Estado: Pendiente (el ETL ya calcula `informal` y el cubo trae sus sumas)

### Historia de usuario: 14. Horas trabajadas y duración del desempleo
Como **analista** deseo ver las horas semanales promedio trabajadas por los ocupados y las semanas promedio que llevan buscando empleo los desocupados, para analizar la intensidad del trabajo y la dificultad para conseguir empleo.

**Criterios de aceptación**
- Se excluyen valores fuera de rango (más de 130 horas semanales o negativos).
- Ambas métricas responden a los filtros activos.

Prioridad: Media · Estimación: 2 · Iteración: 2 · Estado: Pendiente (el ETL ya anula horas negativas o mayores a 130 y el cubo trae las sumas)

### Historia de usuario: 15. Brecha de género
Como **gerente** deseo ver la diferencia de la tasa de desempleo entre mujeres y hombres, para evaluar la equidad en el mercado laboral.

**Criterios de aceptación**
- Se muestra la TD de cada sexo y la brecha en puntos porcentuales.
- La brecha responde a los demás filtros (departamento, edad, periodo).

Prioridad: Media · Estimación: 2 · Iteración: 2 · Estado: Pendiente

---

## Filtros

### Historia de usuario: 16. Filtrar por periodo
Como **gerente** deseo filtrar por año y mes, para analizar un periodo específico.

**Criterios de aceptación**
- Filtros: año (2022–2025) y mes (1–12), con selección múltiple.
- Todas las métricas y gráficas de la página se actualizan al cambiar el filtro.

Prioridad: Alta · Estimación: 2 · Iteración: 1 · Estado: Hecha

### Historia de usuario: 17. Filtrar por ubicación
Como **gerente** deseo filtrar por departamento y por zona (cabecera o rural), para comparar territorios.

**Criterios de aceptación**
- Filtros: departamento (33 opciones con su nombre) y zona (cabecera / centros poblados y rural disperso).
- Si un filtro deja muestra insuficiente (menos de 30 encuestados), se muestra una advertencia.

Prioridad: Alta · Estimación: 2 · Iteración: 1 · Estado: Hecha

### Historia de usuario: 18. Filtrar por características demográficas
Como **analista** deseo filtrar por sexo, rango de edad y nivel educativo, para analizar grupos poblacionales.

**Criterios de aceptación**
- Filtros: sexo, rango de edad (15–28, 29–44, 45–59, 60+) y grupo educativo.
- Los filtros se combinan entre sí (operación Y).

Prioridad: Alta · Estimación: 3 · Iteración: 1 · Estado: Hecha

### Historia de usuario: 19. Filtrar por características del empleo
Como **analista** deseo filtrar por rama de actividad económica, posición ocupacional y tamaño de empresa, para analizar a los ocupados por sector.

**Criterios de aceptación**
- Filtros: rama (secciones CIIU Rev. 4), posición ocupacional y tamaño de empresa.
- Al usar estos filtros, las métricas que solo aplican a ocupados se recalculan y las demás indican "no aplica".

Prioridad: Media · Estimación: 3 · Iteración: 2 · Estado: Pendiente

### Historia de usuario: 20. Limpiar filtros
Como **usuario del dashboard** deseo restablecer todos los filtros con un botón, para volver rápidamente a la vista nacional.

**Criterios de aceptación**
- Un clic devuelve los 10 filtros a su valor por defecto (todos los valores, último año disponible).

Prioridad: Baja · Estimación: 1 · Iteración: 1 · Estado: Hecha (restablece los 7 filtros actuales; los 3 de la HU 19 se agregarán al implementarla)

---

## Estadística descriptiva: gráficas

### Historia de usuario: 21. Evolución mensual de las tasas
Como **gerente** deseo ver una gráfica de líneas de la TD, TO y TGP mes a mes entre 2022 y 2025, para identificar tendencias y estacionalidad.

**Criterios de aceptación**
- Eje X con los 48 meses; al pasar el cursor se ve el valor exacto.
- La gráfica responde a los filtros activos.

Prioridad: Alta · Estimación: 3 · Iteración: 1 · Estado: Hecha

### Historia de usuario: 22. Desempleo por departamento
Como **gerente** deseo ver la tasa de desempleo por departamento en un mapa o gráfica de barras ordenada, para identificar las regiones más afectadas.

**Criterios de aceptación**
- Los departamentos se ordenan de mayor a menor TD.
- Se puede seleccionar un departamento desde la gráfica para aplicarlo como filtro.

Prioridad: Alta · Estimación: 5 · Iteración: 1 · Estado: Hecha

### Historia de usuario: 23. Desempleo por sexo y edad
Como **analista** deseo ver una gráfica de la TD por rango de edad separada por sexo, para identificar los grupos más vulnerables, como los jóvenes.

**Criterios de aceptación**
- Barras agrupadas por rango de edad, con una serie por sexo.

Prioridad: Media · Estimación: 3 · Iteración: 1 · Estado: Hecha (visible solo para el rol Analista)

### Historia de usuario: 24. Ocupados por rama de actividad
Como **gerente** deseo ver la distribución de los ocupados por rama de actividad económica, para conocer qué sectores generan más empleo.

**Criterios de aceptación**
- Treemap o barras con el número de ocupados y su participación porcentual por sección CIIU.

Prioridad: Media · Estimación: 3 · Iteración: 2 · Estado: Pendiente

### Historia de usuario: 25. Ingreso según nivel educativo
Como **analista** deseo ver la distribución del ingreso laboral por nivel educativo en un diagrama de cajas, para analizar el retorno de la educación.

**Criterios de aceptación**
- Una caja por grupo educativo; se omiten los valores atípicos extremos de la visualización (no del cálculo).

Prioridad: Media · Estimación: 3 · Iteración: 2 · Estado: Pendiente

---

## Estadística probabilística (predicción)

### Historia de usuario: 26. Pronóstico de la tasa de desempleo
Como **analista** deseo ver el pronóstico de la TD nacional para los próximos 6 meses con su intervalo de confianza, para anticipar escenarios futuros.

**Criterios de aceptación**
- Gráfica con la serie histórica, el pronóstico y la banda de confianza del 95 %.
- Se muestran la TD proyectada para el próximo mes y para el sexto mes.
- El modelo solo se entrena con datos anteriores al periodo pronosticado.

Prioridad: Alta · Estimación: 8 · Iteración: 2 · Estado: Pendiente

### Historia de usuario: 27. Evaluación de los modelos predictivos
Como **analista** deseo comparar el desempeño de varios modelos (línea base estacional, SARIMA y Gradient Boosting) con MAE, RMSE y MAPE, para elegir el pronóstico más confiable.

**Criterios de aceptación**
- Validación temporal (walk-forward) sobre los últimos 12 meses.
- Tabla con MAE, RMSE y MAPE por modelo y gráfica de valores reales frente a predichos.
- Se resalta el mejor modelo y si supera a la línea base.

Prioridad: Alta · Estimación: 8 · Iteración: 2 · Estado: Pendiente

### Historia de usuario: 28. Probabilidad de desempleo según perfil
Como **analista** deseo ingresar un perfil (sexo, edad, nivel educativo, departamento, zona) y obtener la probabilidad de estar desempleado, para identificar perfiles de riesgo.

**Criterios de aceptación**
- Modelo de clasificación entrenado sobre la fuerza de trabajo, con su AUC visible.
- Gráfica de importancia de variables del modelo.

Prioridad: Media · Estimación: 8 · Iteración: 2 · Estado: Pendiente

### Historia de usuario: 29. Resumen ejecutivo de proyecciones
Como **gerente** deseo ver un resumen con el escenario base, optimista y pesimista de la TD, para apoyar decisiones sin entrar en el detalle técnico de los modelos.

**Criterios de aceptación**
- Los escenarios corresponden al pronóstico y a los límites del intervalo de confianza del mejor modelo.
- Texto breve que indique si se espera aumento o disminución del desempleo.

Prioridad: Media · Estimación: 3 · Iteración: 2 · Estado: Pendiente

---

## Exportación

### Historia de usuario: 30. Exportar resultados
Como **analista** deseo exportar las métricas y los datos agregados con los filtros activos a CSV, para usarlos en otros informes.

**Criterios de aceptación**
- El archivo incluye los filtros aplicados y la fecha de generación.
- Solo se exportan datos agregados (nunca registros individuales de encuestados).

Prioridad: Baja · Estimación: 2 · Iteración: 2 · Estado: Pendiente

---

## Matriz de acceso por rol

| HU | Funcionalidad | Administrador | Analista | Gerente |
|---|---|:-:|:-:|:-:|
| 1–3 | Inicio/cierre de sesión y menú | ✔ | ✔ | ✔ |
| 4–5 | Gestión de usuarios | ✔ | | |
| 6–9 | ETL, calidad de datos y bitácora | ✔ | | |
| 10–11, 13, 15 | Tasas, población, informalidad, brecha de género | | ✔ | ✔ |
| 12, 14 | Ingreso, horas y duración del desempleo | | ✔ | |
| 16–17, 20 | Filtros de periodo y ubicación, limpiar filtros | | ✔ | ✔ |
| 18–19 | Filtros demográficos y de empleo | | ✔ | ✔ |
| 21–22, 24 | Gráficas de evolución, departamentos y ramas | | ✔ | ✔ |
| 23, 25 | Gráficas de sexo/edad e ingreso/educación | | ✔ | |
| 26–28 | Pronóstico, evaluación de modelos y clasificador | | ✔ | |
| 29 | Resumen ejecutivo de proyecciones | | ✔ | ✔ |
| 30 | Exportación | | ✔ | |

## Cobertura del requerimiento 14 del enunciado

| Requisito | Cubierto por |
|---|---|
| 10 filtros | Año, mes (HU 16); departamento, zona (HU 17); sexo, rango de edad, nivel educativo (HU 18); rama, posición ocupacional, tamaño de empresa (HU 19) |
| 10 métricas descriptivas | TD, TO, TGP (HU 10); ocupados, desocupados, inactivos (HU 11); ingreso promedio y mediano (HU 12); informalidad (HU 13); horas promedio y semanas buscando empleo (HU 14); brecha de género (HU 15) |
| 5 gráficas descriptivas | HU 21, 22, 23, 24, 25 |
| 5 métricas probabilísticas | TD proyectada (HU 26); MAE, RMSE, MAPE (HU 27); AUC (HU 28) |
| 3 gráficas probabilísticas | Pronóstico con intervalo (HU 26); real vs. predicho (HU 27); importancia de variables (HU 28) |

## Plan por iteración

| Iteración | Semanas | Historias | Cantidad |
|---|---|---|:-:|
| 1 | 9–12 (entrega 09-11-2026) | 1, 2, 3, 4, 6, 7, 8, 10, 11, 16, 17, 18, 20, 21, 22, 23 | 16 |
| 2 | 13–16 (entrega 09-12-2026) | 5, 9, 12, 13, 14, 15, 19, 24, 25, 26, 27, 28, 29, 30 | 14 |

## Avance (revisado el 09-11-2026)

| Iteración | Hechas | En progreso | Pendientes |
|---|---|---|---|
| 1 | 14 de 16: 1, 3, 4, 6, 7, 10, 11, 16, 17, 18, 20, 21, 22, 23 | 2, 8 | — |
| 2 | 0 de 14 | 5, 9 | 12, 13, 14, 15, 19, 24, 25, 26, 27, 28, 29, 30 |
| **Total** | **14 de 30** | **4** | **12** |
