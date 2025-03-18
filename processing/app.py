import connexion
from datetime import datetime, timezone
import yaml
import logging, logging.config
from apscheduler.schedulers.background import BackgroundScheduler
import os.path as op
import json
import requests
import os
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

service_name = os.getenv("SERVICE_NAME")

with open('/config/process_config.prod.yml', 'r') as file:
    app_config = yaml.safe_load(file)

with open("/config/log_config.prod.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    log_filename = f"/{service_name}/log/{service_name}.log"
    LOG_CONFIG['handlers']['file']['filename'] = log_filename
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

DEFAULT_STATS = {
    "num_online_orders": 0,
    "max_online_order": 0.0,
    "num_store_sales": 0,
    "max_store_sale": 0.0,
    "last_updated": None
}

app_config['datastore']['filename'] = f"/data/{service_name}/{service_name}.json"
EVENT_FILE = app_config['datastore']['filename']


def get_stats():
    logger.info("Request received")

    if op.isfile(EVENT_FILE):

        with open(EVENT_FILE, 'r') as f:
            stats = json.load(f)

        logger.debug(f"Current stats: {stats}")
        logger.info("Request completed")
        return stats, 200
    else:
        logger.error("No stats")
        return "Stats do not exist", 404 

def query_request(url, start_timestamp, end_timestamp):
    
    url_with_params = f"{url}?start_timestamp={start_timestamp}&end_timestamp={end_timestamp}"
    response = requests.get(
        url_with_params)

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Error getting stats at {url}. Status code: {response.status_code}")
        return None

def populate_stats():
    logger.info("Periodic processing has started.")

    if op.isfile(EVENT_FILE):
        with open(EVENT_FILE, 'r') as f:
            temp_stats = json.load(f)
    else:
        temp_stats = DEFAULT_STATS
    
    current_datetime = datetime.now(timezone.utc)
    formatted_datetime = current_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f') 

    if temp_stats['last_updated']:
        start_timestamp = temp_stats['last_updated']

    else:
        start_timestamp = "2000-01-01T00:00:00"
    
    online_order_stat = query_request(app_config['eventstores']['online_orders']['url'], start_timestamp, formatted_datetime)
    store_sales_stat = query_request(app_config['eventstores']['store_sales']['url'], start_timestamp, formatted_datetime)


    if online_order_stat:
        logger.info(f"Received {len(online_order_stat)} online orders events.")
        new_online_orders = len(online_order_stat)
        max_online_order = max(order['order_amount'] for order in online_order_stat)
    else:
        new_online_orders = 0
        max_online_order = 0.0

    if store_sales_stat:
        logger.info(f"Received {len(store_sales_stat)} store sales events.")
        new_store_sales = len(store_sales_stat)
        max_store_sale = max(sale['sale_amount'] for sale in store_sales_stat)
    else:
        new_store_sales = 0
        max_store_sale = 0.0

    temp_stats["num_online_orders"] += new_online_orders
    temp_stats["max_online_order"] = max(temp_stats["max_online_order"], max_online_order)
    temp_stats["num_store_sales"] += new_store_sales
    temp_stats["max_store_sale"] = max(temp_stats["max_store_sale"], max_store_sale)

    temp_stats["last_updated"] = formatted_datetime

    with open(EVENT_FILE, "w") as f:
        json.dump(temp_stats, f, indent=4)

    logger.debug(f"Stats updated: {temp_stats}")

    logger.info("Periodic processing has ended")

def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['interval'])
    sched.start()

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
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")
