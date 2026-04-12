import os
import json
import time
import psycopg2
from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv
from agent import run_agent

load_dotenv()

DB_URL = os.getenv("POSTGRES_URL")

def init_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS task_ledger (
                                                               issue_key VARCHAR(50) PRIMARY KEY,
                        status VARCHAR(50),
                        execution_time_sec FLOAT,
                        prompt_tokens INTEGER DEFAULT 0,
                        completion_tokens INTEGER DEFAULT 0,
                        total_cost_usd FLOAT DEFAULT 0.0,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
        # If columns don't exist, add them (for existing tables)
        cur.execute("ALTER TABLE task_ledger ADD COLUMN IF NOT EXISTS prompt_tokens INTEGER DEFAULT 0;")
        cur.execute("ALTER TABLE task_ledger ADD COLUMN IF NOT EXISTS completion_tokens INTEGER DEFAULT 0;")
        cur.execute("ALTER TABLE task_ledger ADD COLUMN IF NOT EXISTS total_cost_usd FLOAT DEFAULT 0.0;")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ [Database] Migration failed: {e}")

def log_task_to_db(issue_key, status, exec_time, tokens=None):
    # Ensure tokens is a dict even if None is passed
    tokens = tokens or {}
    prompt_tokens = tokens.get("prompt_tokens", 0)
    completion_tokens = tokens.get("completion_tokens", 0)

    # GPT-4o Pricing Logic ($5/1M input, $15/1M output)
    cost = (prompt_tokens * 0.000005) + (completion_tokens * 0.000015)

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO task_ledger
               (issue_key, status, execution_time_sec, prompt_tokens, completion_tokens, total_cost_usd)
               VALUES (%s, %s, %s, %s, %s, %s)
                   ON CONFLICT (issue_key) DO UPDATE
                                                  SET status = EXCLUDED.status,
                                                  execution_time_sec = EXCLUDED.execution_time_sec,
                                                  prompt_tokens = EXCLUDED.prompt_tokens,
                                                  completion_tokens = EXCLUDED.completion_tokens,
                                                  total_cost_usd = EXCLUDED.total_cost_usd""",
            (issue_key, status, exec_time, prompt_tokens, completion_tokens, cost)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ [Database] Failed to log tokens for {issue_key}: {e}")

# --- Kafka Consumer Configuration ---
KAFKA_CONF = {
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    'group.id': 'telofix-worker-group',
    'auto.offset.reset': 'earliest'
}

TOPIC_NAME = os.getenv("KAFKA_TOPIC_TASKS", "telofix-tasks")

def start_worker():
    init_db()
    consumer = Consumer(KAFKA_CONF)
    consumer.subscribe([TOPIC_NAME])

    print(f"👷 Telofix Worker is active. Listening for tasks on '{TOPIC_NAME}'...")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    continue
                else:
                    print(f"❌ [Worker] Consumer error: {msg.error()}")
                    break

            task_data = json.loads(msg.value().decode('utf-8'))
            issue_key = task_data.get("issue_key")

            print(f"\n⚡ [Worker] New task received: {issue_key}")
            print(f"🤖 Handing over to Telofix Agent...")

            start_time = time.time()
            try:
                # 1. Capture the tokens returned by the agent
                token_usage = run_agent(issue_key)

                exec_time = round(time.time() - start_time, 2)
                print(f"✅ [Worker] Task {issue_key} completed successfully in {exec_time}s.")

                # 2. Pass the tokens to the DB logger
                log_task_to_db(issue_key, "PR_CREATED", exec_time, tokens=token_usage)

            except Exception as e:
                exec_time = round(time.time() - start_time, 2)
                print(f"❌ [Worker] Agent failed on {issue_key}: {str(e)}")
                log_task_to_db(issue_key, "FAILED", exec_time)

    except KeyboardInterrupt:
        print("\n🛑 Worker shutting down...")
    finally:
        consumer.close()

if __name__ == "__main__":
    start_worker()