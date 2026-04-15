from kafka import KafkaProducer
import json
import time

try:
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    )
    
    test_data = {"status": "connected", "message": "Hello F1 Kafka"}
    producer.send('f1-telemetry', test_data)
    producer.flush() # Đảm bảo dữ liệu đã được đẩy đi hết
    print("Kết nối thành công và đã gửi dữ liệu!")
    
except Exception as e:
    print(f"Vẫn lỗi: {e}")