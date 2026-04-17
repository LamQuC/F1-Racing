# F1 Racing Analytics 

## Project Objective
This project builds a system to collect, process, analyze, and visualize Formula 1 (F1) Telemetry data in real-time. The system simulates a modern data pipeline featuring: Kafka, PostgreSQL, FastF1, dbt, and Streamlit.

---

## Architecture Overview

```
[FastF1] → [Kafka Producer] → [Kafka Broker] → [Kafka Consumer] → [Postgres] → [dbt] → [Streamlit Dashboard]
```

- **FastF1**: Crawls and normalizes Telemetry data from F1 Grand Prix events.
- **Kafka**: Manages streaming data transmission between the Producer and Consumer.
- **Postgres**: Stores raw telemetry data (Bronze layer).
- **dbt**: Transforms and aggregates data (Silver/Gold layers).
- **Streamlit**: Dashboard for visualization, simulation, and technical analysis.

---

## Installation Guide

### 1. System Requirements
- Python 3.9+
- Docker (or standalone installations of Postgres and Kafka)

### 2. Environment Initialization
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Start Services with Docker
```bash
cd docker
# Start Postgres & Kafka
# (Requires Docker Desktop)
docker compose up -d
```

### 4. Set Up Environment Variables
Create a .env file in the root directory (template provided):
```
DB_USER=de_user
DB_PASS=de_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
KAFKA_BROKER=localhost:9092
```

### 5. Run the Pipeline
- **Producer**: Crawls and sends data to Kafka
  ```bash
  python src/producers/telemetry_producer.py
  ```
- **Consumer**:Receives and writes data to Postgres
  ```bash
  python src/consumers/bronze_consumer.py
  ```
- **Dashboard**: Analysis and visualization
  ```bash
  streamlit run src/dashboard/app.py
  ```

### 6.Run dbt for Data Processing
```bash
cd f1_transformation
# Configure profile in profiles.yml
# Run transformation models
 dbt run
```

---

## Directory Structure
```
F1-Racing/
├── cache/                # FastF1 cache storage
├── data/                 # Raw data files
├── docker/               # Docker Compose for Postgres & Kafka
├── f1_transformation/    # dbt project (data modeling)
├── logs/                 # System logs
├── notebook/             # Analysis notebooks
├── src/
│   ├── config/           # System configuration
│   ├── consumers/        # Kafka Consumers
│   ├── dashboard/        # Streamlit application
│   ├── producers/        # Kafka Producers
│   └── utils/            # DB connection utilities
├── test/                 # Test scripts
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── .gitignore            # Git exclusion file
└── README.md             # This documentation
```

---

## Key Components

### 1. Kafka Producer (`src/producers/telemetry_producer.py`)
- Fetches telemetry data for each race session via FastF1.
- Normalizes and sends each record to a Kafka topic.

### 2. Kafka Consumer (`src/consumers/bronze_consumer.py`)
 - Consumes data from Kafka and writes it into partitioned tables in Postgres.
 - Automatically generates table partitions by yea

### 3. Dashboard (`src/dashboard/app.py`)
 - Streamlit interface: Select Year, Grand Prix, and Driver.
 - 3 Tabs: Race Report, Live Simulator, and Performance Charts.
 - Visual simulation of car positions, speed charts, throttle, brake, and RPM.

### 4. dbt Transformation (`f1_transformation/`)
 - Builds Silver/Gold models to aggregate statistics and standings.
 - Connects directly to Postgres.

---

- Liên hệ: [vlam711003@gmail.com]
