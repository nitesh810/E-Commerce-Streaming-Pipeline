# E-Commerce Streaming Pipeline

Real-time order processing with Apache Beam on GCP Dataflow.

## Project Names
- **Project**: ecommerce-streaming-pipeline
- **Dataset**: ecommerce_orders
- **Tables**: orders, hourly_metrics
- **Topics**: order-events, order-alerts

## Metrics
✅ **Capacity**: Designed to scale to **thousands of orders per minute**  
✅ **Latency**: **Near real-time processing** using 5-minute windows  
✅ **Validation**: Tested with **large-scale simulated events**  
✅ **Cost**: **~$70/month** for sustained **~500 orders/min** workload  
✅ **Availability**: Designed with **fault-tolerant streaming patterns**

### **Detailed Component Breakdown**

#### 1. **Ingestion Layer: Cloud Pub/Sub**

**Topic: `order-events`**
- **Purpose**: Receives incoming order events from various sources
- **Message Format**: JSON-encoded order data
- **Delivery**: At-least-once guarantee (handled by deduplication in pipeline)
- **Scalability**: Auto-scales to handle traffic spikes

**How Messages Flow:**
```
Order Event → Pub/Sub Topic → Stored in buffer → Delivered to Dataflow
```

**Message Structure:**
```json
{
  "order_id": "ORD000001",
  "customer_id": "CUST1234",
  "amount": 299.99,
  "status": "confirmed",
  "country": "India"
}
```

#### 2. **Processing Layer: Cloud Dataflow (Apache Beam)**

**Pipeline Configuration:**
- **Runner**: DataflowRunner (managed service on GCP)
- **Streaming Mode**: True (processes data continuously)
- **Workers**: 
  - Minimum: 2 workers
  - Maximum: 10 workers (autoscaling enabled)
- **Machine Type**: n1-standard-2 (default)
- **Region**: us-central1

**Autoscaling Behavior:**
```
Low traffic (< 100 orders/min)  → 2 workers  → ~$25/month
Medium (500 orders/min)         → 4-5 workers → ~$70/month  
High (2000+ orders/min)         → 8-10 workers → ~$150/month
```

**Pipeline Steps Explained:**

#### **Step 0: Run test order script**
```python
mkdir -p scripts
nano scripts/generate_test_data.py

...Paste the code, Save (Ctrl + O)

python scripts/generate_test_data.py --project project-id
```
- mkdir -p scripts: Creates a folder named scripts if it does not already exist.
- -p tells mkdir to create parent directories if they don’t exist.
- The file is saved inside the scripts folder under the directory where we ran the nano command.
- /home/<your-cloud-shell-username>/scripts/generate_test_data.py

##### **Step 1: Read from Pub/Sub**
```python
orders = pipeline | 'Read' >> ReadFromPubSub(topic='projects/.../topics/order-events')
```
- Subscribes to `order-events` topic
- Receives messages as they arrive
- Each message becomes an element in the pipeline

##### **Step 2: Parse & Validate**
```python
parsed_orders = orders | 'Parse' >> beam.ParDo(ParseOrders())
```
**What ParseOrders does:**
1. Decodes bytes to JSON
2. Validates required fields exist: `order_id`, `customer_id`, `amount`
3. Converts `amount` to float
4. Adds `processed_at` timestamp
5. Filters out invalid orders

##### **Step 3: Write Raw Orders to BigQuery**
```python
orders | 'Save Orders' >> WriteToBigQuery(
    table='ecommerce_orders.orders',
    schema=ORDERS_SCHEMA,
    write_disposition='WRITE_APPEND'
)
```
- Writes ALL parsed orders to `orders` table
- Preserves raw data for historical analysis
- Uses streaming inserts (low latency)

**Table Schema:**
| Column       | Type      | Description                                |
|--------------|-----------|--------------------------------------------|
| order_id     | STRING    | Unique order identifier                    |
| customer_id  | STRING    | Customer identifier                        |
| amount       | FLOAT     | Order amount                               |
| status       | STRING    | Order status (pending/confirmed/delivered) |
| country      | STRING    | Customer country                           |
| processed_at | TIMESTAMP | When order entered pipeline                |

##### **Step 4: Apply 5-Minute Tumbling Windows**
```python
windowed = orders | 'Window' >> beam.WindowInto(window.FixedWindows(5*60))
```

**About Tumbling Window?**
- Divides data stream into **fixed, non-overlapping time intervals**
- Each order belongs to exactly ONE window
- Window duration: 5 minutes (300 seconds)

**Example:**
```
Orders arriving between 10:00-10:05 → Window 1
Orders arriving between 10:05-10:10 → Window 2
Orders arriving between 10:10-10:15 → Window 3
```

**About 5 minutes?**
- Short enough for "real-time" insights
- Long enough to aggregate meaningful data
- Balances between latency and data volume

##### **Step 5: Group Orders by Window**
```python
grouped = windowed | 'Group' >> beam.Map(lambda x: ('all', x)) | 'GroupByKey' >> beam.GroupByKey()
```
- Groups all orders in same window together
- Key: `'all'` (one group per window)
- Result: `('all', [order1, order2, ..., orderN])` per window

##### **Step 6: Calculate Aggregated Metrics**
```python
metrics = grouped | 'Calculate' >> beam.ParDo(CalculateMetrics())
```

**Calculated Metrics:**
1. **order_count**: How many orders in this 5-minute window
2. **total_revenue**: Sum of all order amounts
3. **avg_order_value**: Average order size

**Example Output:**
```json
{
  "window_start": "2024-02-09T10:00:00Z",
  "window_end": "2024-02-09T10:05:00Z",
  "order_count": 523,
  "total_revenue": 45678.90,
  "avg_order_value": 87.35,
  "calculated_at": "2024-02-09T10:05:03Z"
}
```

##### **Step 7: Save Metrics to BigQuery**

**Table Schema:**
| Column          | Type      | Description       |
|-----------------|-----------|-------------------|
| window_start    | TIMESTAMP | Window start time |
| window_end      | TIMESTAMP | Window end time   |
| order_count     | INTEGER   | Orders in window  |
| total_revenue   | FLOAT     | Sum of amounts    |
| avg_order_value | FLOAT     | Average amount    |
| calculated_at   | TIMESTAMP | When calculated   |

##### **Step 8: Anomaly Detection**
```python
anomalies = metrics | 'Detect' >> beam.ParDo(DetectAnomalies())
```

**When Alerts Trigger:**
- **SPIKE**: More than 1000 orders in 5 minutes (unusual traffic)
- **DROP**: Less than 5 orders in 5 minutes (possible system issue)

##### **Step 9: Publish Alerts to Pub/Sub**
```python
anomalies | 'Alert' >> WriteToPubSub(topic='projects/.../topics/order-alerts')
```

**Alert Topic: `order-alerts`**
- Receives anomaly messages
- Triggers Cloud Function for notification
- Decouples detection from notification logic

#### 3. **Storage Layer: BigQuery**

**Dataset: `ecommerce_orders`**

**Table 1: `orders`**
- Stores ALL individual orders
- Partitioned by `processed_at` (date) for cost optimization
- Clustered by `country` for faster queries
- Used for detailed analysis and auditing

**Table 2: `hourly_metrics`**
- Stores aggregated 5-minute summaries
- Much smaller than raw orders (12 rows/hour vs thousands)
- Used for dashboards and trend analysis
- Partitioned by `window_start` (date)

**Example Query:**
```sql
-- Get last hour's metrics
SELECT 
  window_start,
  order_count,
  total_revenue,
  avg_order_value
FROM `ecommerce_orders.hourly_metrics`
WHERE window_start >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY window_start DESC;

-- Get today's total orders
SELECT COUNT(*) as total_orders
FROM `ecommerce_orders.orders`
WHERE DATE(processed_at) = CURRENT_DATE();

#### 4. **Alerting Layer: Cloud Function**

**Function: `process-order-alerts`**
- **Trigger**: Pub/Sub message on `order-alerts` topic
- **Purpose**: Handle anomaly notifications

**How Alert Flow Works:**
```
1. DetectAnomalies finds spike (e.g., 1500 orders in 5 min)
2. Alert message published to order-alerts topic
3. Cloud Function automatically triggered
4. Function logs alert to Cloud Logging
```

## 🤝 Contributing

This is a portfolio project, but suggestions welcome:
1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

---

## 📄 License

MIT License - feel free to use for learning and portfolio purposes.

---