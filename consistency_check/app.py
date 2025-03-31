import connexion
from datetime import datetime, timezone
import time
import yaml
import logging, logging.config
import json
import os
import requests
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

service_name = os.getenv("SERVICE_NAME")

with open('/config/check_config.prod.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open("/config/log_config.prod.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    log_filename = f"/{service_name}/log/{service_name}.log"
    LOG_CONFIG['handlers']['file']['filename'] = log_filename
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

app_config['datastore']['filename'] = f"/data/{service_name}/{service_name}.json"
EVENT_FILE = app_config['datastore']['filename']

def query_endpoints():
    logger.info("Start Query Endpoints")
    eventstores = app_config['eventstores']
    endpoints = {
        'counts_in_proc': 'counts_in_processing',
        'counts_in_anal': 'counts_in_analyzer',
        'lst_in_anal': 'list_in_analyzer',
        'count_in_db': 'count_events_in_db',
        'lst_in_db': 'list_events_in_db'
    }
    results = {}
    for key, value in endpoints.items():
        try:
            response = requests.get(eventstores[value]['url'])
            if response.status_code == 200:
                results[key] = response.json()
            else:
                logger.debug(f"Failed to fetch data from {value}. Status Code: {response.status_code}")
        except Exception as e:
            logger.debug(f"Error fetching data from {value}: {str(e)}")   
    return results

def run_consistency_checks():
    logger.info("Start Consistency Check")
    base = query_endpoints()

    start_time = time.time()

    trace_ids_in_anal = {item["trace_id"] for item in base['lst_in_anal']}
    trace_ids_in_db = {item["trace_id"] for item in base['lst_in_db']}

    not_in_db = [item for item in base['lst_in_anal'] if item["trace_id"] not in trace_ids_in_db]
    not_in_queue = [item for item in base['lst_in_db'] if item["trace_id"] not in trace_ids_in_anal]

    end_time = time.time()
    run_time = int((end_time - start_time) * 1000)

    logger.info(f"Consistency checks completed  | processing_time_ms={run_time}  |  missing_in_db = {len(not_in_db)}  | missing_in_queue = {len(not_in_queue)}")
    
    results = {
        "last_updated": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f'), 
        "counts": {
            "db": {
                "online_orders": base['count_in_db']['online_order_count'],
                "store_sales": base['count_in_db']['store_sale_count']
            },
            "queue": {
                "online_orders": base['counts_in_anal']['num_online_orders'],
                "store_sales": base['counts_in_anal']['num_store_sales']
            },
            "processing": {
                "online_orders": base['counts_in_proc']["num_online_orders"],
                "store_sales": base['counts_in_proc']["num_store_sales"]
            }
        },
        "missing_in_db": not_in_db,
        "missing_in_queue": not_in_queue
    }

    write_to_json(results)
    return  {"message": "Successfully updates the JSON"}, 200

def write_to_json(data):
    logger.info("Write to json")
    with open(EVENT_FILE, "w") as f:
        json.dump(data, f, indent=4)
    

def get_checks():
    try:
        with open(EVENT_FILE, 'r') as f:
            stats = json.load(f)
        return stats
    except FileNotFoundError:
        logger.error(f"File {EVENT_FILE} not found.")
        return {"message": "No checks have been run"}, 404

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("check.yaml", base_path="/consistency_check", strict_validation=True, validate_responses=True)
app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    app.run(port=8300, host="0.0.0.0")
