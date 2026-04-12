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
        cur.execute("ALTER TABLE task_ledger ADD COLUMN IF NOT EXISTS prompt_tokens INTEGER DEFAULT 0;")
        cur.execute("ALTER TABLE task_ledger ADD COLUMN IF NOT EXISTS completion_tokens INTEGER DEFAULT 0;")
        cur.execute("ALTER TABLE task_ledger ADD COLUMN IF NOT EXISTS total_cost_usd FLOAT DEFAULT 0.0;")
        cur.execute("ALTER TABLE task_ledger ADD COLUMN IF NOT EXISTS touched_files JSONB DEFAULT '[]'::jsonb;")
        conn.commit()
        cur.close()
        conn.close()
        print("✅ [Database] Schema is up to date.")
    except Exception as e:
        print(f"❌ [Database] Migration failed: {e}")

# --- NEW: Memory Retrieval Function ---
def get_previous_touched_files(issue_key):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT touched_files FROM task_ledger WHERE issue_key = %s;", (issue_key,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result and result[0]:
            return result[0] # Returns the JSON array as a Python list
    except Exception as e:
        print(f"⚠️ [Database] Could not fetch memory for {issue_key}: {e}")
    return []

# --- UPDATED: Database Logging ---
def log_task_to_db(issue_key, status, exec_time, tokens=None, touched_files=None):
    tokens = tokens or {}
    prompt_tokens = tokens.get("prompt_tokens", 0)
    completion_tokens = tokens.get("completion_tokens", 0)
    touched_files = touched_files or []

    cost = (prompt_tokens * 0.000005) + (completion_tokens * 0.000015)

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO task_ledger
               (issue_key, status, execution_time_sec, prompt_tokens, completion_tokens, total_cost_usd, touched_files)
               VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                   ON CONFLICT (issue_key) DO UPDATE
                                                  SET status = EXCLUDED.status,
                                                  execution_time_sec = EXCLUDED.execution_time_sec,
                                                  prompt_tokens = EXCLUDED.prompt_tokens,
                                                  completion_tokens = EXCLUDED.completion_tokens,
                                                  total_cost_usd = EXCLUDED.total_cost_usd,
                                                  touched_files = EXCLUDED.touched_files""",
            (issue_key, status, exec_time, prompt_tokens, completion_tokens, cost, json.dumps(touched_files))
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ [Database] Failed to log task {issue_key}: {e}")

# --- Kafka Consumer Configuration ---
KAFKA_CONF = {
    'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    'group.id': 'telofix-worker-group',
    'auto.offset.reset': 'earliest'
}
# Only listen to Java tasks now!
TOPIC_NAME = os.getenv("KAFKA_TOPIC_TASKS", "telofix.tasks.java")

def start_worker():
    init_db()
    consumer = Consumer(KAFKA_CONF)
    consumer.subscribe([TOPIC_NAME])

    print(f"👷 Telofix Worker is active. Listening for tasks on '{TOPIC_NAME}'...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error(): continue

            task_data = json.loads(msg.value().decode('utf-8'))
            issue_key = task_data.get("issue_key")

            print(f"\n⚡ [Worker] New task received: {issue_key}")
            print(f"🤖 Handing over to Telofix Agent...")

            # --- NEW: Retrieve Memory ---
            previous_files = get_previous_touched_files(issue_key)
            if previous_files:
                print(f"🧠 Memory Retrieved: Agent remembers modifying {len(previous_files)} files.")

            start_time = time.time()

            # The worker defines its identity based on the topic or an Env variable
            worker_type = os.getenv("WORKER_TYPE", "java")

            try:
                # Pass memory in, get full dictionary out
                agent_result = run_agent(issue_key, worker_type, previous_files=previous_files)

                # Extract values safely
                token_usage = agent_result.get("usage", {})
                new_touched_files = agent_result.get("touched_files", [])

                exec_time = round(time.time() - start_time, 2)
                print(f"✅ [Worker] Task {issue_key} completed successfully in {exec_time}s.")

                # Log everything back to DB
                log_task_to_db(issue_key, "PR_CREATED", exec_time, tokens=token_usage, touched_files=new_touched_files)

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