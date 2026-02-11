"""Calculate metrics per window"""
import apache_beam as beam
from datetime import datetime

class CalculateMetrics(beam.DoFn):
    def process(self, element, window=beam.DoFn.WindowParam):
        key, orders = element
        count = len(orders)
        revenue = sum(o.get('amount', 0) for o in orders)
        avg = revenue / count if count > 0 else 0
        
        yield {
            'window_start': window.start.to_utc_datetime().isoformat(),
            'window_end': window.end.to_utc_datetime().isoformat(),
            'order_count': count,
            'total_revenue': round(revenue, 2),
            'avg_order_value': round(avg, 2),
            'calculated_at': datetime.now(timezone.utc)
        }
