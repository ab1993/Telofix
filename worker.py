import os
import json
from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv
from agent import run_agent

load_dotenv()

# --- Kafka Consumer Configuration ---
KAFKA_CONF = {
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    'group.id': 'telofix-worker-group',
    'auto.offset.reset': 'earliest' # Start from the beginning if no offset is found
}

TOPIC_NAME = os.getenv("KAFKA_TOPIC_TASKS", "telofix-tasks")

def start_worker():
    consumer = Consumer(KAFKA_CONF)
    consumer.subscribe([TOPIC_NAME])

    print(f"👷 Telofix Worker is active. Listening for tasks on '{TOPIC_NAME}'...")

    try:
        while True:
            # Poll for a message (1.0 second timeout)
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"❌ [Worker] Consumer error: {msg.error()}")
                    break

            # Parse the task
            task_data = json.loads(msg.value().decode('utf-8'))
            issue_key = task_data.get("issue_key")

            print(f"\n⚡ [Worker] New task received: {issue_key}")
            print(f"🤖 Handing over to Telofix Agent...")

            try:
                # TRIGGER THE AI BRAIN
                run_agent(issue_key)
                print(f"✅ [Worker] Task {issue_key} completed successfully.")
            except Exception as e:
                print(f"❌ [Worker] Agent failed on {issue_key}: {str(e)}")

    except KeyboardInterrupt:
        print("\n🛑 Worker shutting down...")
    finally:
        consumer.close()

if __name__ == "__main__":
    start_worker()