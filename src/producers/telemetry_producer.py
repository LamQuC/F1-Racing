import fastf1
import json
import time
from kafka import KafkaProducer
import os
from src.config.config import settings

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_NAME = settings['kafka']['topic_name']

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def stream_race_data(year, event_name):
    """Nạp toàn bộ tay đua của một chặng cụ thể"""
    try:
        session = fastf1.get_session(year, event_name, 'Q')
        session.load()
        drivers = session.laps['Driver'].unique().tolist()
        
        telemetry_dict = {}
        for drv in drivers:
            try:
                drv_lap = session.laps.pick_driver(drv).pick_fastest()
                telemetry_dict[drv] = drv_lap.get_telemetry().add_distance()
            except: continue

        if not telemetry_dict: return
        min_steps = min(len(df) for df in telemetry_dict.values())

        for i in range(0, min_steps, 5): 
            for drv, df in telemetry_dict.items():
                row = df.iloc[i]
                
                # CHUẨN HÓA DỮ LIỆU TRƯỚC KHI GỬI
                # Chuyển Brake từ True/False sang 1/0
                brake_val = 1 if row['Brake'] is True else 0
                
                msg = {
                    "driver": drv, 
                    "year": year, 
                    "event_name": event_name,
                    "session_time": str(row['SessionTime']),
                    "speed": int(row['Speed']), 
                    "rpm": int(row['RPM']),
                    "gear": int(row['nGear']), 
                    "throttle": float(row['Throttle']),  # Bổ sung Throttle
                    "brake": brake_val,                  # Bổ sung Brake (đã ép kiểu int)
                    "location": [float(row['X']), float(row['Y'])]
                }
                producer.send(TOPIC_NAME, value=msg)
            
            if i % 50 == 0: 
                producer.flush()
    except Exception as e:
        print(f"Lỗi tại {event_name}: {e}")

def crawl_f1_history():
    fastf1.Cache.enable_cache('cache')
    
    for year in range(2023, 2026):
        print(f"📂 Đang xử lý năm: {year}")
        schedule = fastf1.get_event_schedule(year)
        # Chỉ lấy các chặng chính thức, bỏ qua Testing
        gp_events = schedule[schedule['EventFormat'] != 'testing']['EventName'].tolist()
        
        # Lấy top 3 chặng đua đầu tiên của năm đó
        top_3_events = gp_events[:3]
        
        for event in top_3_events:
            print(f"🏁 Đang nạp toàn bộ tay đua chặng: {event}")
            stream_race_data(year, event)
            time.sleep(2) 

if __name__ == "__main__":
    crawl_f1_history()