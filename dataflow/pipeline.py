"""
Main Pipeline - Real-time Order Processing
===========================================
Reads orders → Cleans data → Calculates metrics → Detects problems
"""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms import window
from apache_beam.io.gcp import pubsub, bigquery
from transforms.parse_orders import ParseOrders
from transforms.calculate_metrics import CalculateMetrics
from transforms.detect_anomalies import DetectAnomalies
from utils.schemas import ORDERS_SCHEMA, METRICS_SCHEMA

def run():
    # YOUR SETTINGS - Change these
    PROJECT_ID = 'your-project-id'
    BUCKET = 'your-bucket'
    
    options = PipelineOptions([
        f'--project={PROJECT_ID}',
        '--region=us-central1',
        f'--temp_location=gs://{BUCKET}/temp',
        f'--staging_location=gs://{BUCKET}/staging',
        '--runner=DataflowRunner',
        '--streaming',
        '--num_workers=2',
        '--max_num_workers=10'
    ])
    
    with beam.Pipeline(options=options) as pipeline:
        # Step 1: Read and clean orders
        orders = (
            pipeline
            | 'Read' >> pubsub.ReadFromPubSub(
                topic=f'projects/{PROJECT_ID}/topics/order-events')
            | 'Parse' >> beam.ParDo(ParseOrders())
        )
        
        # Step 2: Save raw orders
        orders | 'Save Orders' >> bigquery.WriteToBigQuery(
            f'{PROJECT_ID}:ecommerce_orders.orders',
            schema=ORDERS_SCHEMA,
            write_disposition='WRITE_APPEND'
        )
        
        # Step 3: Calculate metrics (5-min windows)
        metrics = (
            orders
            | 'Window' >> beam.WindowInto(window.FixedWindows(5*60))
            | 'Group' >> beam.Map(lambda x: ('all', x))
            | 'GroupByKey' >> beam.GroupByKey()
            | 'Calculate' >> beam.ParDo(CalculateMetrics())
        )
        
        # Step 4: Save metrics
        metrics | 'Save Metrics' >> bigquery.WriteToBigQuery(
            f'{PROJECT_ID}:ecommerce_orders.hourly_metrics',
            schema=METRICS_SCHEMA,
            write_disposition='WRITE_APPEND'
        )
        
        # Step 5: Detect & alert
        (metrics
         | 'Detect' >> beam.ParDo(DetectAnomalies())
         | 'Alert' >> pubsub.WriteToPubSub(
             topic=f'projects/{PROJECT_ID}/topics/order-alerts'))

if __name__ == '__main__':
    run()
