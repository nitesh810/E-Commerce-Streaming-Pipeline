"""Alert Handler - Processes anomaly alerts"""
import base64, json, logging

def process_alert(event, context):
    msg = base64.b64decode(event['data']).decode('utf-8')
    alert = json.loads(msg) if msg.startswith('{') else eval(msg)
    
    if alert.get('severity') == 'HIGH':
        logging.error(f"🚨 {alert.get('message')}")
    else:
        logging.warning(f"⚠️  {alert.get('message')}")
    
    return {'status': 'success'}
