# Propuesta de ML e IA para Telemetria (backend)

Fecha: 2026-04-21  
Repositorio: `back/` (Django + DRF + Celery + Redis)

## 1) Contexto del proyecto (lo que ya existe)

El backend ya tiene un pipeline muy adecuado para ML/IA:

- **Ingesta**: `TelemetrySyncView` trae y guarda telemetría desde PanAccess.
- **Procesamiento**: `merge_ott_records` construye tablas optimizadas para análisis (p.ej. `MergedTelemetricOTTDelancer`).
- **Orquestación**: Celery ejecuta periódicamente una cadena **Sync → Merge**.
- **Analítica avanzada**: `TelemetriaDelancer/panaccess/analytics.py` incluye:
  - Segmentación (K-means con NumPy)
  - Forecasting simple (tendencia + media móvil)
  - Correlaciones (Pandas)
  - Anomalías (SQL con desviación estándar)
  - Matrices de performance (Pandas)
- **API**: endpoints de telemetría y análisis en `TelemetriaDelancer/urls.py`.

**Conclusión**: No hace falta “inventar” el pipeline. Hay que “productizar” analítica/ML:
persistir resultados, versionar modelos, automatizar training/scoring y exponer endpoints estables.

## 2) Objetivos ML/IA (casos de uso recomendados)

Se proponen 4 frentes. Se pueden implementar por fases:

### A) Detección de anomalías (MVP rápido)

- **Qué entrega**: alertas por día/canal/franja con z-score o modelo.
- **Datos**: `MergedTelemetricOTTDelancer` (campos: `dataDate`, `timeDate`, `dataName`, `dataDuration`, `subscriberCode`, `deviceId`).
- **Valor**: detectar caídas/picos, problemas de red, eventos masivos, etc.

### B) Forecasting de demanda (MVP medio)

- **Qué entrega**: predicción de “views” o “watch_time” por canal para próximos N días.
- **Valor**: capacity planning, campañas, programación.

### C) Segmentación de usuarios + churn (MVP medio)

- **Qué entrega**: segmentos (ocasional/regular/activo/súper activo) y riesgo de churn.
- **Valor**: personalización, retención, priorización de soporte.

### D) Asistente IA (LLM) para consultas (fase avanzada)

- **Qué entrega**: endpoint “pregunta-respuesta” que llama “herramientas” internas (funciones/analíticas existentes).
- **Condición**: gobernanza (no PII), control de costos, rate limiting, logging.

## 3) Arquitectura propuesta (alto nivel)

### 3.1 Flujo batch (recomendado como base)

1. **Sync** (PanAccess → BD local)  
2. **Merge** (tablas especializadas: OTT/DVB/…)  
3. **Feature generation** (agregados diarios/semanales; tablas o vistas)  
4. **Training** (periódico: diario o cada X horas)  
5. **Scoring** (frecuente: cada 2–10 minutos, o tras merge)  
6. **Serving** (API: lee resultados persistidos o cache)

### 3.2 Persistencia recomendada (resultado ML)

Crear almacenamiento para:

- **Artefactos de modelo**: (p.ej. archivo `.joblib` o JSON) con metadata (versión, fecha, dataset).
- **Predicciones/segmentos**:
  - tabla `ml_predictions_*` (por tipo) o
  - Redis cache si el dato es efímero, con fallback a BD si se requiere historial.

### 3.3 Endpoints recomendados (API estable)

Bajo prefijo `delancer/telemetry/` (consistente con lo actual):

- `/ml/anomalies/` (por rango y/o por canal)
- `/ml/forecast/` (parámetros: canal, horizonte, rango entrenamiento)
- `/ml/segments/` (parámetros: fecha, n_segments)
- `/ml/churn/` (si aplica)
- (Opcional) `/assistant/` (LLM)

### 3.4 Celery (jobs)

Reutilizar el pipeline actual (`sync_and_merge_telemetry_chain`) y extenderlo con:

- `compute_features_task`
- `train_models_task` (o uno por modelo)
- `score_models_task`
- `publish_insights_task` (cache + DB + logs)

## 4) Implementación por fases (MVP → Producción)

### Fase 0 — Preparación (1–2 días)

- Definir qué métricas son “verdad”:
  - target = `views` o `watch_time` por canal/día
  - para churn: “activo” en ventana (p.ej. últimos 7 días)
- Definir ventanas temporales (últimos 30/60/90 días).
- Definir “granularidad” (día, hora, franja).

### Fase 1 — Productizar Anomalías (MVP)

- Reusar `get_anomaly_detection()` (SQL) y exponer endpoint ML dedicado.
- Persistir eventos en tabla `ml_anomalies` (o cache si no hace falta histórico).
- Agendar tarea Celery para recalcular cada X minutos/horas.

Entregables:
- Endpoint `/ml/anomalies/`
- Job Celery “anomalies refresh”
- Dashboard-friendly JSON

### Fase 2 — Forecasting simple (MVP)

- Reusar `get_time_series_analysis()` como baseline.
- Persistir pronósticos por canal/horizonte.
- Agregar validación: si hay pocos datos, devolver “insuficiente”.

Entregables:
- Endpoint `/ml/forecast/`
- Job Celery “forecast refresh”

### Fase 3 — Segmentación + perfiles

- Reusar `get_user_segmentation_analysis()` y convertirlo en proceso batch.
- Guardar segmento por `subscriberCode` + fecha de corte.

Entregables:
- Endpoint `/ml/segments/`
- Job Celery “segmentation refresh”

### Fase 4 — Modelos mejores (scikit-learn)

- Introducir `scikit-learn`:
  - anomaly: IsolationForest o OneClassSVM (si aplica)
  - forecasting: regresión + features (día de semana, estacionalidad)
  - churn: clasificación (si hay etiqueta) o heurística calibrada
- Versionar modelos y controlar drift.

Entregables:
- Artefactos versionados (modelo + metadata)
- Métricas offline (backtesting)

### Fase 5 — Asistente LLM (opcional)

- Endpoint que “elige” qué análisis correr según intención.
- Guardrails: PII, rate limiting, auditoría.

## 5) Riesgos y mitigaciones

- **Volumen de datos**: evitar cargar toda la tabla a Pandas; usar agregaciones por día/canal/usuario.
- **SQLite vs MariaDB**: algunas funciones SQL/ventanas pueden variar; asegurar compatibilidad o condicionar por vendor.
- **PII (subscriberCode, ip)**: anonimizar/hashear en outputs; nunca enviar PII a LLM.
- **Costos** (LLM): caching, límites de tokens, cuotas, logs.

## 6) Definiciones técnicas (para el backlog)

### Feature sets mínimos (ejemplos)

- Por **canal/día**:
  - views, watch_time_total, unique_users, unique_devices, avg_duration
  - day_of_week, is_weekend
- Por **usuario/ventana**:
  - total_watch_time_7d, views_7d, unique_channels_7d
  - actividad_días_en_7d

### Contratos API (respuesta)

- Siempre incluir:
  - `generated_at`
  - `filters`
  - `success`
  - `data` (lista o dict)

---

## Anexo: Archivos clave actuales (referencia)

- `TelemetriaDelancer/tasks.py` (Cadena Celery Sync → Merge)
- `TelemetriaDelancer/celery.py` (Beat schedule)
- `TelemetriaDelancer/panaccess/analytics.py` (analíticas + “ML baseline”)
- `TelemetriaDelancer/panaccess/analytics_date_range.py` (analítica por rango)
- `TelemetriaDelancer/models.py` (tablas mergeadas e índices)
- `TelemetriaDelancer/views.py` + `TelemetriaDelancer/urls.py` (API DRF)

