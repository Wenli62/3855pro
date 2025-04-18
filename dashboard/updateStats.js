/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

const PROCESSING_STATS_API_URL = "/processing/stats";
const ANALYZER_API_URL = {
    stats: "/analyzer/stats",
    online: "/analyzer/online-orders",
    store: "/analyzer/store-sales"
};
const CONSISTENCY_API_URL = "/consistency_check/checks";

// This function fetches and updates the general statistics
const makeReq = (url, cb) => {
    fetch(url)
        .then(res => res.json())
        .then((result) => {
            console.log("Received data: ", result)
            cb(result);
        }).catch((error) => {
            updateErrorMessages(error.message)
        })
}

const updateProcessing = (result) => {
    document.getElementById("num_online_in_processing").innerText = result["num_online_orders"]
    document.getElementById("num_instore_in_processing").innerText = result["num_store_sales"]
    document.getElementById("max_amount_online").innerText = result["max_online_order"]
    document.getElementById("max_amount_instore").innerText = result["max_store_sale"]
    document.getElementById("last_updated").innerText = result["last_updated"]
}

const updateAnalyzer = (result) => {
    document.getElementById("num_online_in_analyzer").innerText = result["num_online_orders"]
    document.getElementById("num_instore_in_analyzer").innerText = result["num_store_sales"]
}

const fetchRandomEvent = (eventType, callback) => {
    makeReq(ANALYZER_API_URL.stats, (results) => {
        const maxCount = eventType === "online" ? results.num_online_orders : results.num_store_sales;
        if (!maxCount) {
            console.warn(`No events available for ${eventType}`);
            return;
        }
        const randomIndex = Math.floor(Math.random() * maxCount);
        const eventUrl = eventType === "online" ? ANALYZER_API_URL.online : ANALYZER_API_URL.store;

        makeReq(`${eventUrl}?index=${randomIndex}`, (eventData) => {
            console.log(`Fetched ${eventType} event at index ${randomIndex}:`, eventData);
            callback(eventData);
        });
    });
};

const updateOnlineOrder = (result) => {
    document.getElementById("cid").innerText = result["cid"]
    document.getElementById("order_amount").innerText = result["order_amount"]
    document.getElementById("order_time").innerText = result["order_time"]
    document.getElementById("shipping_address").innerText = result["shipping_address"]
    document.getElementById("online_trace_id").innerText = result["trace_id"]
}

const updateStoreSale = (result) => {
    document.getElementById("sid").innerText = result["sid"]
    document.getElementById("sale_amount").innerText = result["sale_amount"]
    document.getElementById("sale_time").innerText = result["sale_time"]
    document.getElementById("payment_method").innerText = result["payment_method"]
    document.getElementById("store_trace_id").innerText = result["trace_id"]
}

const updateConsistency = (result) => {
    document.getElementById("counts").innerText = JSON.stringify(result["counts"])
    document.getElementById("consistency_last_updated").innerText = JSON.stringify(result["last_updated"])
    document.getElementById("missing_in_db").innerText = JSON.stringify(result["missing_in_db"])
    document.getElementById("missing_in_queue").innerText = JSON.stringify(result["missing_in_queue"])
}
const getLocaleDateStr = () => (new Date()).toLocaleString()

const getStats = () => {
    document.getElementById("last-updated-value").innerText = getLocaleDateStr()
    makeReq(PROCESSING_STATS_API_URL, (result) => updateProcessing (result, "processing-stats"))
    makeReq(ANALYZER_API_URL.stats, (result) => updateAnalyzer(result, "analyzer-stats"))    
    fetchRandomEvent("online", updateOnlineOrder)
    fetchRandomEvent("store", updateStoreSale)
}

async function submitUpdate() {
    try {
        const response = await fetch('/consistency_check/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
        });

        if (response.ok) {
            makeReq(CONSISTENCY_API_URL, (result) => {
                updateConsistency(result); 
                document.getElementById('update_message').textContent = "Update completed!";
            });
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

const updateErrorMessages = (message) => {
    const id = Date.now()
    console.log("Creation", id)
    msg = document.createElement("div")
    msg.id = `error-${id}`
    msg.innerHTML = `<p>Something happened at ${getLocaleDateStr()}!</p><code>${message}</code>`
    document.getElementById("messages").style.display = "block"
    document.getElementById("messages").prepend(msg)
    setTimeout(() => {
        const elem = document.getElementById(`error-${id}`)
        if (elem) { elem.remove() }
    }, 7000)
}

const setup = () => {
    getStats()
    setInterval(() => getStats(), 4000) // Update every 4 seconds
}

document.addEventListener('DOMContentLoaded', setup)
