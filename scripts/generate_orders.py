"""Generate test orders"""
import json, random, time, argparse
from google.cloud import pubsub_v1

STATUSES = ['pending', 'confirmed', 'delivered']
COUNTRIES = ['India', 'USA', 'UK']

def generate_order(num):
    return {
        'order_id': f'ORD{num:06d}', # d = decimal integer with whole number with no decimal part, written in base 10
        # order_id = "ORD" + str(num).zfill(6) | if num = 6, ORD000006

        'customer_id': f'CUST{random.randint(1000, 9999)}',
        'amount': round(random.uniform(100, 5000), 2), 
        # Generates random amount between 100 and 5000 and rounds it to 2 decimal places, round(123.456789, 2) → 123.46

        'status': random.choice(STATUSES),
        'country': random.choice(COUNTRIES)
    }

def send_orders(project, topic, rate, minutes):
    publisher = pubsub_v1.PublisherClient() # Creates a Pub/Sub publisher client that can send messages to topics.
    topic_path = publisher.topic_path(project, topic) # It builds Pub/Sub topic name: projects/{project}/topics/{topic}
    interval = 60.0 / rate # interval = seconds between two messages | rate = no of orders per minute
    total = rate * minutes # this calculation to know how many total messages to send.
    # rate = 100 orders/min
    # minutes = 5
    # total = 100 × 5 = 500 orders

    print(f"Sending {rate} orders/min for {minutes} min (Total: {total})")
    
    for i in range(total):
        order = generate_order(i + 1)
        publisher.publish(topic_path, json.dumps(order).encode()).result() # Sends the message to the Pub/Sub topic
        # json.dumps(order) = Converts a Python dictionary → JSON string
        # .encode() = Converts the JSON string → bytes
        # .result() = Blocks the program , Waits until Pub/Sub confirms the publish ,Raises an error if publish fails.
        # Without .result() = Messages send asynchronously

        if (i+1) % 100 == 0:
            print(f"Sent {i+1}/{total}")
        time.sleep(interval)
    
    print("✅ Done!")

if __name__ == '__main__': # Run code only executed directly.
    # Prevents this block from running if the file is imported into another script
    # All other code in the file CAN still run when imported.

    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True) # Creates an argument parser to read inputs from the command line.
    parser.add_argument('--topic', default='order-events')
    parser.add_argument('--rate', type=int, default=100)
    parser.add_argument('--minutes', type=int, default=5)
    send_orders(**vars(parser.parse_args()))
