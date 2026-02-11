"""Detect unusual patterns"""
import apache_beam as beam
from datetime import datetime

class DetectAnomalies(beam.DoFn):
    def process(self, metrics):
        count = metrics.get('order_count', 0)
        if count > 1000:  # Too many
            yield {
                'alert_time': datetime.now(timezone.utc),
                'type': 'SPIKE',
                'message': f'{count} orders in 5min',
                'severity': 'HIGH'
            }
        elif count < 5 and count > 0:  # Too few
            yield {
                'alert_time': datetime.now(timezone.utc),
                'type': 'DROP',
                'message': f'Only {count} orders',
                'severity': 'MEDIUM'
            }
