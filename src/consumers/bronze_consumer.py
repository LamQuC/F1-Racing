import sys
import os
# Thêm đường dẫn gốc để import được src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import json
import os
from kafka import KafkaConsumer
from src.utils.db_connection import DBManager
from src.config.config import settings

def ensure_partitioned_raw_table(cursor):
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS f1_raw_telemetry (
            driver TEXT,
            year INT NOT NULL,
            event_name TEXT NOT NULL,
            session_time TEXT,
            speed INT,
            rpm INT,
            gear INT,
            throttle NUMERIC,
            brake NUMERIC,
            location_x NUMERIC,
            location_y NUMERIC,
            UNIQUE (driver, year, event_name, session_time)
        ) PARTITION BY LIST (year);
    """)
    
    for year in range(2023, 2027):
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS f1_raw_telemetry_{year}
            PARTITION OF f1_raw_telemetry
            FOR VALUES IN ({year});
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS f1_raw_telemetry_default
        PARTITION OF f1_raw_telemetry
        DEFAULT;
    """)

def start_consumer():
    try:
        conn = DBManager().get_engine().raw_connection()
        cursor = conn.cursor()
        ensure_partitioned_raw_table(cursor)
        conn.commit()
        print("✅ Kết nối Postgres thành công")
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}"); return

    consumer = KafkaConsumer(
        'f1-telemetry',
        bootstrap_servers=[os.getenv("KAFKA_BROKER", "localhost:9092")],
        auto_offset_reset='earliest',
        group_id=settings['kafka']['group_id'], 
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    batch_size = 500
    records = []
    try:
        for message in consumer:
            data = message.value
        
            raw_brake = data.get('brake')
            if isinstance(raw_brake, bool):
                brake_val = 100.0 if raw_brake else 0.0
            else:
            
                try:
                    brake_val = float(raw_brake) if raw_brake is not None else 0.0
                except:
                    brake_val = 0.0

            query = """
                INSERT INTO f1_raw_telemetry 
                (driver, year, event_name, session_time, speed, rpm, gear, throttle, brake, location_x, location_y)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (driver, year, event_name, session_time) 
                DO NOTHING;
            """
            
            values = (
                data.get('driver'),
                data.get('year', 0),
                data.get('event_name', 'Unknown'),
                data.get('session_time'),
                data.get('speed'),
                data.get('rpm'),
                data.get('gear'),
                data.get('throttle'),
                brake_val,  # Sử dụng giá trị đã xử lý
                data.get('location')[0] if data.get('location') else 0, 
                data.get('location')[1] if data.get('location') else 0
            )
            
            
            records.append((query, values))
            if len(records) >= batch_size:
                for q, v in records:
                    cursor.execute(q, v)
                conn.commit()
                records = []

            if message.offset % 50 == 0:
                print(f"📥 Saved offset {message.offset} for {data.get('driver')}")
    except Exception as e:
        print(f"Lỗi khi lưu DB: {e}")
        conn.rollback()
if __name__ == "__main__":
    start_consumer()