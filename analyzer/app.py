import connexion
from pykafka import KafkaClient 
import logging, logging.config
import yaml
import json
from apscheduler.schedulers.background import BackgroundScheduler
import os.path as op
import os
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

service_name = os.getenv("SERVICE_NAME")

with open('/config/analyzer_config.prod.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open("/config/log_config.prod.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    log_filename = f"/{service_name}/log/{service_name}.log"
    LOG_CONFIG['handlers']['file']['filename'] = log_filename
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')


DEFAULT_STATS = {
    "num_online_orders": 0,
    "num_store_sales": 0,
}

app_config['datastore']['filename'] = f"/data/{service_name}/{service_name}.json"
EVENT_FILE = app_config['datastore']['filename']

kafka_host = app_config['kafka']['hostname']
kafka_port = app_config['kafka']['port']
kafka_topic = app_config['kafka']['topic']


def get_kafka_event_list():
    hostname = f"{kafka_host}:{kafka_port}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(kafka_topic)]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    event_list_sum = []

    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        payload = data.get("payload")
#analyzer-1  | PAYLOAD: {'sid': 'bak059', 'sale_amount': 268.7, 'payment_method': 'Cash', 'sale_time': '2024-03-07T07:25:46.485Z', 'trace_id': 1742613946436227628}
#analyzer-1  | PAYLOAD: {'cid': 'C532', 'order_amount': 233.17, 'shipping_address': '662 hdu St, Vancouer, CA', 'order_time': '2024-08-27T08:25:51.082Z', 'trace_id': 1742613951114409329}
        event_list_sum.append({
            "event_id": payload.get("sid") or payload.get("cid"),
            "trace_id": payload.get("trace_id")
        })
    # online_event_list = []
    # store_event_list = []
    # event_list_sum = []
    # for msg in consumer:
    #     message = msg.value.decode("utf-8")
    #     data = json.loads(message)
    #     if data.get("type") == "online_order":
    #         online_event_list.append(data.get("payload"))
    #     if data.get("type") == "store_sale":
    #         store_event_list.append(data.get("payload"))
    # for i in online_event_list:
    #     event_list_sum.append({
    #         "event_id": i.get("event_id"),
    #         "trace_id": i.get("trace_id")
    #     })
    # for i in store_event_list:
    #     event_list_sum.append({
    #         "event_id": i.get("event_id"),
    #         "trace_id": i.get("trace_id")
    #     })    

    return event_list_sum

def get_each_type_msg(event_type):
    hostname = f"{kafka_host}:{kafka_port}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(kafka_topic)]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    filtered_messages = []
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        if data.get("type") == event_type:
            filtered_messages.append(data)

    return filtered_messages


def get_event_msg(index, event_type):

    filtered_messages = get_each_type_msg(event_type)

    if index < len(filtered_messages):  
        logger.info(f"Returning {event_type} at index {index}: {filtered_messages[index]}")
        return filtered_messages[index].get('payload', {}), 200
    else:
        logger.error(f"No message found at index {index}")
        return {"message": f"No message at index {index}!"}, 404


def get_online_orders(index):
    return get_event_msg(index, "online_orders")


def get_store_sales(index):
    return get_event_msg(index, "store_sales")


def count_event_msg(event_type):
    filtered_messages = get_each_type_msg(event_type)
    return len(filtered_messages)


def write_stats():
    online_orders_count = count_event_msg("online_orders")
    store_sales_count = count_event_msg("store_sales")

    DEFAULT_STATS["num_online_orders"] = online_orders_count
    DEFAULT_STATS["num_store_sales"] = store_sales_count

    if op.isfile(EVENT_FILE):
        with open(EVENT_FILE, 'r') as f:
            temp_stats = json.load(f)
    else:
        temp_stats = {}

    temp_stats.update(DEFAULT_STATS)

    with open(EVENT_FILE, "w") as f:
        json.dump(temp_stats, f, indent=4)
    
    logger.debug(f"stats updated: {temp_stats}")

def get_stats():
    logger.info("stats request received")
    write_stats()

    if op.isfile(EVENT_FILE):
        with open(EVENT_FILE, 'r') as f:
            stats = json.load(f)
        logger.debug(f"current stats: {stats}")
        return stats, 200
    else:
        logger.error("stats do not exist")
        return {"message": "stats do not exist"}, 404 

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("3855api.yaml", strict_validation=True, validate_responses=True)
app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    app.run(port=8200, host="0.0.0.0")