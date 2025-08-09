from prometheus_client import Counter, Histogram


events_published_counter = Counter(
    "events_published_total",
    "Nombre d'evenements publies",
    ["topic", "type"],
)

events_consumed_counter = Counter(
    "events_consumed_total",
    "Nombre d'evenements consommes",
    ["topic", "type", "consumer"],
)

event_latency_seconds = Histogram(
    "event_latency_seconds",
    "Latence emission -> consommation",
    ["topic", "type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
)

# Saga chorégraphiée (compteurs dédiés)
saga_choreo_started_total = Counter(
    "saga_choreo_started_total",
    "Nombre de sagas choreographiees demarreess",
    ["source"],
)

saga_choreo_success_total = Counter(
    "saga_choreo_success_total",
    "Nombre de sagas choreographiees terminees avec succes",
    ["source"],
)

saga_choreo_failed_total = Counter(
    "saga_choreo_failed_total",
    "Nombre de sagas choreographiees en echec",
    ["source"],
)


