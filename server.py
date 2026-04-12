import os
import json
from fastapi import FastAPI, Request
from confluent_kafka import Producer
from dotenv import load_dotenv
from prometheus_client import make_asgi_app, Counter

load_dotenv()

app = FastAPI()

# --- 1. PROMETHEUS METRICS SETUP ---
# Create an ASGI app for the metrics endpoint and mount it
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Define our first metric: A counter for webhooks
WEBHOOK_COUNTER = Counter('telofix_webhooks_received_total', 'Total Jira webhooks received')

# --- Kafka Configuration ---
KAFKA_CONF = {
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    'client.id': 'telofix-gateway'
}
TOPIC_NAME = os.getenv("KAFKA_TOPIC_TASKS", "telofix-tasks")

# Initialize the Producer
producer = Producer(KAFKA_CONF)

def delivery_report(err, msg):
    """ Callback to confirm if Kafka received the message. """
    if err is not None:
        print(f"❌ [Kafka] Delivery failed: {err}")
    else:
        print(f"📡 [Kafka] Success! Message delivered to {msg.topic()} [Partition: {msg.partition()}]")

@app.post("/webhook/jira-trigger")
async def jira_webhook(request: Request):
    try:
        data = await request.json()
        issue_key = data.get("issue", {}).get("key")

        # 1. Detect Language (Default to 'java' if not provided)
        # In a real Jira setup, this could come from a custom field like data.get("issue").get("fields").get("customfield_10010")
        project_lang = data.get("project_type", "java").lower()

        # 2. Dynamic Topic Construction
        target_topic = f"telofix.tasks.{project_lang}"

        # --- 2. INCREMENT THE PROMETHEUS COUNTER ---
        WEBHOOK_COUNTER.inc()

        if not issue_key:
            return {"status": "ignored", "reason": "No issue key found in payload"}

        # Prepare the message for Kafka
        payload = {
            "issue_key": issue_key,
            "repo_url": os.getenv("TARGET_REPO_URL"),
            "timestamp": "now" # You can add actual timestamps later
        }

        # Produce the message
        print(f"📥 [Telofix] Webhook received for {issue_key}. Sending to Kafka...")

        # 3. Produce to the specific language topic
        producer.produce(
            target_topic,
            key=issue_key,
            value=json.dumps(payload),
            callback=delivery_report
        )

        # Flush ensures the message is sent before the function returns
        producer.flush()

        print(f"🚦 [Gateway] Routed {issue_key} to topic: {target_topic}")

        return {"status": "queued", "topic": target_topic, "issue_key": issue_key}

    except Exception as e:
        print(f"❌ [Telofix] Critical Error: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🤖 Telofix Gateway (Kafka-only) is starting on port 8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080)