"""Parse & validate orders"""
import json, apache_beam as beam
from datetime import datetime

class ParseOrders(beam.DoFn):
# DoFn = a function that processes one record at a time. 
# If 100 orders come, process() inside DoFn runs 100 times.

    def process(self, msg):
        # process() is the standard method name defined by Beam’s DoFn class.
        # For every element in the pipeline, call the process() method.

        try:
            order = json.loads(msg.decode('utf-8')) 
            # msg.decode('utf-8'): convert bytes → string, json.loads(): convert string → Python dictionary

            if 'order_id' in order and 'amount' in order:
                order['processed_at'] = datetime.now(timezone.utc)
                order['amount'] = float(order.get('amount', 0))
                yield order # yield sends a value out of the function, one at a time.
                # If you use: return order, It sends one value and the function stops.
        except:
            pass  # Skip bad orders
