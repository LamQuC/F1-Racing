# F1 Racing Analytics - Quốc Lâm

## Mục tiêu dự án
Dự án xây dựng hệ thống thu thập, xử lý, phân tích và trực quan hóa dữ liệu Telemetry của giải đua xe Công thức 1 (F1) theo thời gian thực. Hệ thống mô phỏng pipeline hiện đại với các thành phần: Kafka, PostgreSQL, FastF1, dbt, Streamlit.

---

## Kiến trúc tổng quan

```
[FastF1] → [Kafka Producer] → [Kafka Broker] → [Kafka Consumer] → [Postgres] → [dbt] → [Streamlit Dashboard]
```

- **FastF1**: Crawl & chuẩn hóa dữ liệu Telemetry từ các chặng đua F1.
- **Kafka**: Truyền dữ liệu streaming giữa Producer và Consumer.
- **Postgres**: Lưu trữ dữ liệu thô (bronze layer).
- **dbt**: Chuyển đổi, tổng hợp dữ liệu (silver/gold layer).
- **Streamlit**: Dashboard trực quan hóa, mô phỏng & phân tích kỹ thuật.

---

## Hướng dẫn cài đặt

### 1. Yêu cầu hệ thống
- Python 3.9+
- Docker (hoặc cài riêng Postgres, Kafka)

### 2. Khởi tạo môi trường
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Khởi động dịch vụ bằng Docker
```bash
cd docker
# Khởi động Postgres & Kafka
# (Cần Docker Desktop)
docker compose up -d
```

### 4. Thiết lập biến môi trường
Tạo file `.env` ở thư mục gốc (đã có mẫu):
```
DB_USER=de_user
DB_PASS=de_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
KAFKA_BROKER=localhost:9092
```

### 5. Chạy pipeline
- **Producer**: Crawl & gửi dữ liệu lên Kafka
  ```bash
  python src/producers/telemetry_producer.py
  ```
- **Consumer**: Nhận & ghi dữ liệu vào Postgres
  ```bash
  python src/consumers/bronze_consumer.py
  ```
- **Dashboard**: Phân tích & trực quan hóa
  ```bash
  streamlit run src/dashboard/app.py
  ```

### 6. Chạy dbt để xử lý dữ liệu
```bash
cd f1_transformation
# Cấu hình profile trong profiles.yml
# Chạy các model chuyển đổi
 dbt run
```

---

## Cấu trúc thư mục

```
F1-Racing/
├── cache/                # Lưu cache FastF1
├── data/                 # Dữ liệu thô
├── docker/               # Docker Compose cho Postgres, Kafka
├── f1_transformation/    # Dự án dbt (model hóa dữ liệu)
├── logs/                 # Log hệ thống
├── notebook/             # Notebook phân tích
├── src/
│   ├── config/           # Cấu hình hệ thống
│   ├── consumers/        # Kafka Consumer
│   ├── dashboard/        # Ứng dụng Streamlit
│   ├── producers/        # Kafka Producer
│   └── utils/            # Tiện ích kết nối DB
├── test/                 # Test scripts
├── requirements.txt      # Thư viện Python
├── .env                  # Biến môi trường
├── .gitignore            # File loại trừ khi push git
└── README.md             # Tài liệu này
```

---

## Thành phần chính

### 1. Kafka Producer (`src/producers/telemetry_producer.py`)
- Crawl dữ liệu telemetry từng chặng đua qua FastF1.
- Chuẩn hóa & gửi từng bản ghi lên Kafka topic.

### 2. Kafka Consumer (`src/consumers/bronze_consumer.py`)
- Nhận dữ liệu từ Kafka, ghi vào bảng partitioned trong Postgres.
- Tự động tạo bảng partition theo năm.

### 3. Dashboard (`src/dashboard/app.py`)
- Giao diện Streamlit: chọn năm, chặng, tay đua.
- 3 tab: Race Report, Live Simulator, Performance Charts.
- Mô phỏng trực quan vị trí xe, biểu đồ tốc độ, ga, phanh, RPM.

### 4. dbt Transformation (`f1_transformation/`)
- Xây dựng các model silver/gold tổng hợp thống kê, bảng xếp hạng.
- Kết nối trực tiếp với Postgres.

---

## Đóng góp & phát triển
- Fork repo, tạo branch mới, commit & tạo pull request.
- Mọi ý kiến đóng góp vui lòng mở issue hoặc liên hệ trực tiếp.

---

## Tác giả
- Quốc Lâm
- Liên hệ: [vlam711003@gmail.com]
