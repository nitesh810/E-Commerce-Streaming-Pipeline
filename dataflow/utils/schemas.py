"""BigQuery table schemas"""

ORDERS_SCHEMA = {
    'fields': [
        {'name': 'order_id', 'type': 'STRING'},
        {'name': 'customer_id', 'type': 'STRING'},
        {'name': 'amount', 'type': 'FLOAT'},
        {'name': 'status', 'type': 'STRING'},
        {'name': 'country', 'type': 'STRING'},
        {'name': 'processed_at', 'type': 'TIMESTAMP'}
    ]
}

METRICS_SCHEMA = {
    'fields': [
        {'name': 'window_start', 'type': 'TIMESTAMP'},
        {'name': 'window_end', 'type': 'TIMESTAMP'},
        {'name': 'order_count', 'type': 'INTEGER'},
        {'name': 'total_revenue', 'type': 'FLOAT'},
        {'name': 'avg_order_value', 'type': 'FLOAT'},
        {'name': 'calculated_at', 'type': 'TIMESTAMP'}
    ]
}
