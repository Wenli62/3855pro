import connexion
from connexion import NoContent
import httpx
import time
import yaml
import logging, logging.config
from pykafka import KafkaClient 
import datetime
import json
import os

service_name = os.getenv("SERVICE_NAME")

with open('/config/receiver_config.prod.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open("/config/log_config.prod.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    log_filename = f"/{service_name}/log/{service_name}.log"
    LOG_CONFIG['handlers']['file']['filename'] = log_filename
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

log_filename = f"/log/receiver.log"


kafka_host = app_config['kafka']['hostname']
kafka_port = app_config['kafka']['port']
kafka_topic = app_config['kafka']['topic']

def post_to_endpoint(event_type, body):
    if body:
        body['trace_id'] = time.time_ns()
        logger.info(f"Received event {event_type} with {body['trace_id']}")

        client = KafkaClient(hosts=f"{kafka_host}:{kafka_port}")
        topic = client.topics[str.encode(kafka_topic)]
        producer = topic.get_sync_producer()
        msg = { "type": event_type,
                "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "payload": body
                }
       
        msg_str = json.dumps(msg)
        print(msg_str)
        producer.produce(msg_str.encode('utf-8'))
        logger.info(f"Event {event_type} published to Kafka topic {kafka_topic}")
        # no need to return response code here
        #return 201
        

def online_orders(body):
    response_status_code = post_to_endpoint('online_orders', body)
    logger.info(f"Response for event online_orders (id:{body['cid']}) has status {response_status_code}")
    # change response_status_code to 201
    return NoContent, 201

def store_sales(body):
    response_status_code = post_to_endpoint('store_sales', body)
    logger.info(f"Response for event store_sales (id:{body['sid']}) has status {response_status_code}")
    return NoContent, 201

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("WXU62-3855_api-1.0.0-resolved.yaml", strict_validation=True, validate_responses=True)




if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")