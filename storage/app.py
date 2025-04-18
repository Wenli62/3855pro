import connexion
from connexion import NoContent
from datetime import datetime, date as dt
import functools
from db import make_session
from models import onlineOrderReport, storeSalesReport
import yaml
import logging, logging.config
from sqlalchemy import select, func
from pykafka import KafkaClient
from pykafka.common import OffsetType
import json
from threading import Thread
import os
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

service_name = os.getenv("SERVICE_NAME")

with open('/config/storage_config.prod.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open("/config/log_config.prod.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    log_filename = f"/{service_name}/log/{service_name}.log"
    LOG_CONFIG['handlers']['file']['filename'] = log_filename
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

kafka_host = app_config['kafka']['hostname']
kafka_port = app_config['kafka']['port']
kafka_topic = app_config['kafka']['topic']

def get_mysql_event_list():
    # logger.info("GETTING_EVENT_LIST")
    session = make_session()
    online_stmt = select(onlineOrderReport.cid, onlineOrderReport.trace_id)
    store_stmt = select(storeSalesReport.sid, storeSalesReport.trace_id)
    online_results = [
        {"cid": cid, "trace_id": trace_id, "type": "online_orders"} for cid, trace_id in session.execute(online_stmt).all()
    ]

    store_results = [
        {"sid": sid, "trace_id": trace_id, "type": "store_sales"} for sid, trace_id in session.execute(store_stmt).all()
    ]
    session.close()
    
    online_event_list = [{"event_id": row["cid"], "trace_id": row["trace_id"], "type": row["type"]} for row in online_results]
    store_event_list = [{"event_id": row["sid"], "trace_id": row["trace_id"], "type": row["type"]} for row in store_results]

    event_list_all = online_event_list + store_event_list
    return event_list_all 

def get_count():
    session = make_session()
    online_state = select(func.count()).select_from(onlineOrderReport)
    store_state = select(func.count()).select_from(storeSalesReport)

    online_count = session.execute(online_state).scalar()
    store_count = session.execute(store_state).scalar()

    session.close()

    logger.info("Found %d online orders and %d store sales ", online_count, store_count)
    return {"online_order_count": online_count, "store_sale_count": store_count}


def process_messages():
    """ Process event messages """
    
    hostname = f"{kafka_host}:{kafka_port}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(kafka_topic)]

    # Create a consume on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).

    consumer = topic.get_simple_consumer(consumer_group=b'event_group', 
                                         reset_offset_on_start=False,
                                         auto_offset_reset=OffsetType.LATEST)
    
    # This is blocking - it will wait for a new message
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        #Message: {
        #          'type': 'online_orders', 
        #          'datetime': '2025-04-16T06:13:01', 
        #          'payload': {'cid': 'C12345', 'order_amount': 100.5, 
        #                      'shipping_address': '123 ABC St, Vancouer, CA', 
        #                      'order_time': '2025-01-08T09:12:33.001Z', 
        #                      'trace_id': 1744783981537898263}
        #          }
        payload = msg["payload"]
        
        if msg["type"] == "store_sales": # Change this to your event type
            post_to_db("store_sales", payload)
        elif msg["type"] == "online_orders": # Change this to your event type
            post_to_db("online_orders", payload)
        # Commit the new message as being read
        consumer.commit_offsets()

def setup_kafka_thread():
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()


def use_db_session(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = make_session()
        try:
            event_type = args[0]
            trace_id = args[1]['trace_id']
            
            event = func(session, *args, **kwargs)
            session.add(event)
            session.commit()
        finally:
            session.close()
            logger.debug(f"Stored event {event_type} with a trace id of {trace_id}")
    return wrapper

@use_db_session
def post_to_db(session, event_type, body):
    if event_type == "online_orders":
        body["order_time"] = datetime.strptime(body["order_time"], "%Y-%m-%dT%H:%M:%S.%fZ")
        event = onlineOrderReport(**body)
    elif event_type == "store_sales":
        body["sale_time"] = datetime.strptime(body["sale_time"], "%Y-%m-%dT%H:%M:%S.%fZ")
        event = storeSalesReport(**body)
    return event

def get_online_orders(start_timestamp, end_timestamp):
    session = make_session()
    # Convert from '2025-01-08T09:12:33.001Z' to '2025-01-08 09:12:33.001000'
    start = datetime.fromisoformat(start_timestamp.rstrip("Z"))
    end = datetime.fromisoformat(end_timestamp.rstrip("Z"))

    statement = select(onlineOrderReport)\
                    .where(onlineOrderReport.date_created >= start)\
                    .where(onlineOrderReport.date_created < end)
    results = [
        result.to_dict()
        for result in session.execute(statement).scalars().all()
    ]
    session.close()
    logger.info("Found %d online orders (start: %s, end: %s)", len(results), start, end)
    return results

def get_store_sales(start_timestamp, end_timestamp):
    session = make_session()
    # Convert from '2025-01-08T09:12:33.001Z' to '2025-01-08 09:12:33.001000'
    start = datetime.fromisoformat(start_timestamp.rstrip("Z"))
    end = datetime.fromisoformat(end_timestamp.rstrip("Z"))

    statement = select(storeSalesReport)\
                    .where(storeSalesReport.date_created >= start)\
                    .where(storeSalesReport.date_created < end)
    results = [
        result.to_dict()
        for result in session.execute(statement).scalars().all()
    ]
    session.close()
    logger.info("Found %d store sales (start: %s, end: %s)", len(results), start, end)
    return results

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("3855api.yaml", base_path="/storage", strict_validation=True, validate_responses=True)
if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if __name__ == "__main__":
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")
