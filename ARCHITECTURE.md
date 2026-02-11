# Architecture
```
Orders → Pub/Sub → Dataflow → BigQuery
                      ↓
                  Anomalies → Cloud Function
```

## **High-Level Data Flow**
```
┌─────────────┐
│   Orders    │  (Simulated e-commerce events)
│  Generated  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│              CLOUD PUB/SUB                          │
│  Topic: order-events                                │
│  • Message buffering                                │
│  • At-least-once delivery guarantee                 │
│  • Automatic scaling                                │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│         DATAFLOW PIPELINE (Apache Beam)             │
│                                                     │
│  [Read] → [Parse] → [Window] → [Aggregate]          │
│              ↓          ↓           ↓               │
│         [BigQuery]  [5-min]   [Metrics]             │
│                    tumbling                         │
│                     windows                         │
│                        ↓                            │
│                  [Anomaly Detection]                │
└─────────────┬───────────────────────┬───────────────┘
              │                       │
              ▼                       ▼
┌─────────────────────┐   ┌─────────────────────────┐
│     BIGQUERY        │   │   CLOUD PUB/SUB         │
│  Dataset:           │   │  Topic: order-alerts    │
│  ecommerce_orders   │   │                         │
│                     │   │  Triggers:              │
│  Tables:            │   │  Cloud Function         │
│  • orders           │   │  for alerting           │
│  • hourly_metrics   │   │                         │
└─────────────────────┘   └─────────────────────────┘
```

## Flow
1. Orders come in via Pub/Sub
2. Dataflow processes in real-time
3. Saves to BigQuery
4. Detects anomalies
5. Sends alerts

## Components
- **Pub/Sub**: Message queue
- **Dataflow**: Stream processing
- **BigQuery**: Data warehouse
- **Cloud Functions**: Alerts

## Scalability
- Workers: 2-10 (autoscaling)
- Capacity: 10,000+ orders/min
- Latency: <1 second
