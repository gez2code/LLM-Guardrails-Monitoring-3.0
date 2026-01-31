# LLM Guardrails Monitoring 3.0

A real-time toxicity monitoring system for LLM conversations using **Detoxify** for multi-label classification and **Guardrails-AI** for policy enforcement. Fully containerized with Docker Compose.

> **Version 3.0** - Complete rewrite with improved configuration, better error handling, and comprehensive documentation.

---

## Quick Start

### Prerequisites

- **Docker Desktop** (with Docker Compose) - [Download here](https://www.docker.com/products/docker-desktop/)
- **Python 3.10+** (Mac users: `brew install python@3.10` or use system Python)
- **Guardrails Token** - Get one free at [hub.guardrailsai.com](https://hub.guardrailsai.com/)
- **HuggingFace Token** (optional) - For LMSYS dataset access at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/gez2code/LLM-Guardrails-Monitoring-3.0.git
cd LLM-Guardrails-Monitoring-3.0

# 2. Configure environment
cp .env.example .env
```

Edit `.env` and add your tokens (see [Token Setup](#token-setup) for detailed instructions):
```env
GUARDRAILS_TOKEN=your_guardrails_token_here
HF_TOKEN=your_huggingface_token_here  # Optional
```

---

## Token Setup

### Guardrails Token (Required)

The Guardrails token is required for the toxicity detection validators.

1. Go to [hub.guardrailsai.com](https://hub.guardrailsai.com/)
2. Click **"Sign Up"** or **"Log In"** (GitHub/Google login available)
3. After login, click on your profile icon (top right)
4. Select **"API Keys"** or **"Settings"**
5. Click **"Create New API Key"**
6. Copy the token and paste it in your `.env` file:
   ```env
   GUARDRAILS_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

> **Note:** The token starts with `eyJ...` and is quite long. Make sure to copy the entire string.

### HuggingFace Token (Optional)

The HuggingFace token is only needed if you want to load the LMSYS dataset directly from HuggingFace. You can skip this if you only use the included CSV sample data.

1. Go to [huggingface.co](https://huggingface.co/) and create an account
2. Go to **Settings** → **Access Tokens**: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. Click **"New token"**
4. Give it a name (e.g., "llm-monitoring")
5. Select **"Read"** access (write not needed)
6. Click **"Generate token"**
7. Copy the token and paste it in your `.env` file:
   ```env
   HF_TOKEN=hf_aBcDeFgHiJkLmNoPqRsTuVwXyZ...
   ```

#### LMSYS Dataset Access (Additional Step)

The LMSYS-Chat-1M dataset is **gated** - you need to request access separately:

1. Go to [huggingface.co/datasets/lmsys/lmsys-chat-1m](https://huggingface.co/datasets/lmsys/lmsys-chat-1m)
2. Make sure you're logged in
3. Click **"Agree and access repository"** or **"Request access"**
4. Fill out the form (usually asks for intended use)
5. Wait for approval (can take minutes to days)

Once approved, the `hf_ingest_lmsys.py` script will work automatically.

```bash
# 3. Start all services (first build takes ~10 minutes)
docker compose up --build -d

# 4. Wait for containers to be healthy
docker compose ps
```

### Ingest Sample Data

```bash
# Create Python virtual environment
# Windows:
python -m venv venv

# Mac/Linux (may need python3):
python3 -m venv venv
```

**Activate virtual environment:**

| OS | Command |
|----|---------|
| **Windows (PowerShell)** | `.\venv\Scripts\Activate.ps1` |
| **Windows (CMD)** | `venv\Scripts\activate.bat` |
| **Mac / Linux** | `source venv/bin/activate` |

```bash
# Install dependencies
pip install -r requirements.txt

# Ingest sample data (included in repo)
python scripts/fast_ingest_lmsys.py --csv-path data/raw/conversations.csv
```

### Access the Dashboard

Open **http://localhost:8501** in your browser.

You should see violations appearing within seconds!

---

## Services Overview

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:8501 | Real-time monitoring UI |
| **Kafka UI** | http://localhost:8080 | Message inspection & debugging |
| **Kafka** | localhost:9092 | Message broker |
| **Zookeeper** | localhost:2181 | Kafka coordination |

---

## Data Ingestion Options

### Option 1: CSV File (Recommended for Testing)

```bash
python scripts/fast_ingest_lmsys.py --csv-path data/raw/conversations.csv
```

A sample CSV with 28 messages is included in the repository.

### Option 2: HuggingFace Dataset (Requires Access)

> **Note:** The LMSYS dataset is gated. You must request access at [huggingface.co/datasets/lmsys/lmsys-chat-1m](https://huggingface.co/datasets/lmsys/lmsys-chat-1m)

```bash
# After access is granted:
python scripts/hf_ingest_lmsys.py --limit 100
```

### Option 3: Custom Data

Send messages directly to Kafka topic `llm.conversations`:

```json
{
  "conversation_id": "conv_001",
  "text": "Your message text here",
  "speaker": "user",
  "timestamp": "2025-01-31T10:30:00Z"
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER COMPOSE                                  │
│                                                                              │
│  ┌─────────────┐      ┌─────────────┐      ┌──────────────┐                 │
│  │  Zookeeper  │◄────►│    Kafka    │◄────►│   Kafka UI   │                 │
│  │    :2181    │      │    :9092    │      │    :8080     │                 │
│  └─────────────┘      └──────┬──────┘      └──────────────┘                 │
│                              │                                               │
│              ┌───────────────┴───────────────┐                              │
│              │                               │                              │
│              ▼                               ▼                              │
│   Topic: llm.conversations       Topic: guardrail.violations                │
│              │                               ▲                              │
│              ▼                               │                              │
│  ┌───────────────────────┐                   │                              │
│  │  Guardrails Processor │───────────────────┘                              │
│  │  • Detoxify Model     │                                                  │
│  │  • Weighted Scoring   │────────────┐                                     │
│  │  • Severity Buckets   │            │                                     │
│  └───────────────────────┘            │                                     │
│                                       ▼                                     │
│                          ┌───────────────────────┐                          │
│                          │    Alert Consumer     │                          │
│                          │  • Sliding Window     │                          │
│                          │  • Score Aggregation  │                          │
│                          └───────────┬───────────┘                          │
│                                      │                                      │
│                                      ▼                                      │
│                          ┌───────────────────────┐                          │
│                          │      Dashboard        │                          │
│                          │        :8501          │                          │
│                          └───────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### 1. Toxicity Detection

Messages are analyzed using Detoxify's 7-label toxicity model:

| Label | Description | Weight |
|-------|-------------|--------|
| `toxicity` | General toxic language | 1.0 |
| `insult` | Personal insults | 1.0 |
| `obscene` | Obscene language | 1.0 |
| `sexual_explicit` | Sexual content | 1.2 |
| `threat` | Threatening language | 2.0 |
| `identity_attack` | Attacks on protected groups | 2.0 |
| `severe_toxicity` | Extremely toxic content | 2.5 |

### 2. Scoring

The weighted score is calculated as the maximum of all (score × weight) values:

```
weighted_score = MAX(toxicity×1.0, insult×1.0, threat×2.0, ...)
```

### 3. Severity Classification

| Weighted Score | Severity |
|----------------|----------|
| < 0.10 | No violation |
| 0.10 - 0.59 | LOW |
| 0.60 - 0.84 | MEDIUM |
| ≥ 0.85 | HIGH |

### 4. Alert Generation

Violations are aggregated in a sliding window (default: 5 minutes). Alerts are triggered based on cumulative scores:

| Window Score | Alert Level |
|--------------|-------------|
| ≥ 0.15 | LOW |
| ≥ 0.40 | MEDIUM |
| ≥ 0.80 | HIGH |

---

## Configuration

### Environment Variables

Edit `.env` to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `GUARDRAILS_TOKEN` | Guardrails Hub API token | **Required** |
| `HF_TOKEN` | HuggingFace token | Optional |
| `ALERT_WINDOW_SIZE_SECONDS` | Sliding window duration | 300 |
| `ALERT_LOW_THRESHOLD` | Low alert threshold | 0.15 |
| `ALERT_MEDIUM_THRESHOLD` | Medium alert threshold | 0.40 |
| `ALERT_HIGH_THRESHOLD` | High alert threshold | 0.80 |

---

## Common Commands

```bash
# Start services
docker compose up -d

# Start with rebuild (after code changes)
docker compose up --build -d

# View logs
docker compose logs -f guardrails-processor
docker compose logs -f alert-consumer
docker compose logs -f dashboard

# Stop services
docker compose down

# Stop and remove all data
docker compose down -v

# Restart a specific service
docker compose restart dashboard
```

---

## Troubleshooting

### Container won't start

```bash
# Check container status
docker compose ps

# Check logs for errors
docker compose logs guardrails-processor
docker compose logs alert-consumer
```

### "Libraries for lz4 compression codec not found"

```bash
pip install lz4
```

### Mac: "python: command not found"

Use `python3` instead of `python`:
```bash
python3 -m venv venv
python3 scripts/fast_ingest_lmsys.py --csv-path data/raw/conversations.csv
```

### Mac: Permission denied on venv activation

```bash
chmod +x venv/bin/activate
source venv/bin/activate
```

### Dashboard shows errors

Make sure all containers are running:
```bash
docker compose ps
```

All services should show "running" or "healthy" status.

### HuggingFace dataset access denied

The LMSYS dataset is gated. Either:
1. Request access at [huggingface.co/datasets/lmsys/lmsys-chat-1m](https://huggingface.co/datasets/lmsys/lmsys-chat-1m)
2. Use the included CSV file instead

### Port already in use

Change ports in `docker-compose.yml` or stop conflicting services:
- 8501: Dashboard
- 8080: Kafka UI
- 9092: Kafka
- 2181: Zookeeper

---

## Project Structure

```
LLM-Guardrails-Monitoring-3.0/
├── docker-compose.yml           # Container orchestration
├── Dockerfile.guardrails        # Processor image
├── Dockerfile.alert-consumer    # Alert consumer image
├── Dockerfile.dashboard         # Dashboard image
├── requirements.txt             # Python dependencies
├── .env.example                 # Configuration template
│
├── src/
│   ├── config.py                      # Configuration classes
│   ├── guardrail_input_processor.py   # Main processor service
│   ├── alert_consumer.py              # Alert aggregation service
│   ├── kafka/                         # Kafka consumer/producer
│   ├── processors/                    # Detoxify + scoring logic
│   ├── alert/                         # Window tracking + alerts
│   └── models/                        # Data models
│
├── scripts/
│   ├── fast_ingest_lmsys.py           # CSV ingestion (fast)
│   └── hf_ingest_lmsys.py             # HuggingFace ingestion
│
├── dashboard/
│   ├── app.py                         # Streamlit application
│   ├── config.py                      # Dashboard settings
│   └── components/                    # UI components
│
├── data/raw/
│   └── conversations.csv              # Sample dataset (28 messages)
│
└── outputs/
    ├── kafka_violations.jsonl         # Violation log
    └── alerts.jsonl                   # Alert log
```

---

## Scripts Reference

### Ingestion Scripts (`scripts/`)

#### `fast_ingest_lmsys.py`
Fast CSV ingestion into Kafka without delays. Best for testing and batch processing.

```bash
# Basic usage (uses default CSV path)
python scripts/fast_ingest_lmsys.py

# Specify custom CSV file
python scripts/fast_ingest_lmsys.py --csv-path data/raw/conversations.csv

# Only ingest user messages (skip assistant responses)
python scripts/fast_ingest_lmsys.py --user-only

# Custom Kafka settings
python scripts/fast_ingest_lmsys.py --bootstrap-servers localhost:9092 --topic llm.conversations
```

| Argument | Description | Default |
|----------|-------------|---------|
| `--csv-path` | Path to CSV file | `data/raw/conversations.csv` |
| `--user-only` | Only send user messages | `False` |
| `--bootstrap-servers` | Kafka broker address | `localhost:9092` |
| `--topic` | Kafka topic name | `llm.conversations` |

---

#### `hf_ingest_lmsys.py`
Load data directly from HuggingFace datasets. Requires HF_TOKEN and dataset access.

```bash
# Load 100 conversations from LMSYS
python scripts/hf_ingest_lmsys.py --limit 100

# Load 1000 conversations (default)
python scripts/hf_ingest_lmsys.py

# Only user messages with custom delay
python scripts/hf_ingest_lmsys.py --limit 500 --user-only --delay 0.05

# Use different dataset
python scripts/hf_ingest_lmsys.py --dataset "HuggingFaceH4/ultrachat_200k" --limit 100
```

| Argument | Description | Default |
|----------|-------------|---------|
| `--dataset` | HuggingFace dataset name | `lmsys/lmsys-chat-1m` |
| `--split` | Dataset split | `train` |
| `--limit` | Max conversations to load | `1000` |
| `--user-only` | Only send user messages | `False` |
| `--bootstrap-servers` | Kafka broker address | `localhost:9092` |
| `--topic` | Kafka topic name | `llm.conversations` |
| `--delay` | Delay between messages (seconds) | `0.01` |
| `--batch-size` | Log progress every N conversations | `100` |

---

### Core Services (`src/`)

#### `guardrail_input_processor.py`
Main processing service that runs in Docker. Consumes messages from Kafka, analyzes toxicity, and produces violations.

**Runs automatically in Docker** - no manual execution needed.

```bash
# View logs
docker compose logs -f guardrails-processor
```

**What it does:**
1. Consumes messages from `llm.conversations` topic
2. Runs Detoxify toxicity analysis
3. Calculates weighted scores
4. Classifies severity (low/medium/high)
5. Produces violations to `guardrail.violations` topic
6. Writes backup to `outputs/kafka_violations.jsonl`

---

#### `alert_consumer.py`
Alert aggregation service that runs in Docker. Consumes violations and generates time-windowed alerts.

**Runs automatically in Docker** - no manual execution needed.

```bash
# View logs
docker compose logs -f alert-consumer
```

**What it does:**
1. Consumes violations from `guardrail.violations` topic
2. Aggregates scores in sliding time window (default: 5 minutes)
3. Generates alerts when thresholds are exceeded
4. Writes alerts to `outputs/alerts.jsonl`

---

#### `config.py`
Configuration classes for all services. Reads from environment variables.

**Classes:**
- `DashboardConfig` - Dashboard settings (file paths, refresh intervals)
- `KafkaInputConfig` - Kafka consumer/producer settings
- `AlertConfig` - Alert thresholds and window settings

---

### Kafka Module (`src/kafka/`)

#### `conversation_consumer.py`
Kafka consumer wrapper for reading conversations.

#### `violation_producer.py`
Kafka producer wrapper for sending violations.

---

### Processors Module (`src/processors/`)

#### `guardrail_processor.py`
Core toxicity analysis and scoring logic.

**Key functions:**
- `process_conversation()` - Analyze a single message
- `calculate_weighted_score()` - Apply weights to toxicity scores
- `classify_severity()` - Determine low/medium/high severity

**Configurable parameters:**
```python
VIOLATION_THRESHOLD = 0.10  # Minimum score to be a violation

WEIGHTS = {
    "toxicity": 1.0,
    "insult": 1.0,
    "obscene": 1.0,
    "sexual_explicit": 1.2,
    "threat": 2.0,
    "identity_attack": 2.0,
    "severe_toxicity": 2.5,
}
```

---

### Alert Module (`src/alert/`)

#### `window_tracker.py`
Sliding window implementation for tracking violations over time.

#### `alert_generator.py`
Alert generation logic based on aggregated window scores.

---

### Models Module (`src/models/`)

#### `conversation.py`
Input data model for conversations.

#### `violation.py`
Violation data model with scores and severity.

#### `alert.py`
Alert data model with danger levels and summaries.

---

### Dashboard (`dashboard/`)

#### `app.py`
Main Streamlit application entry point.

```bash
# Access at
http://localhost:8501
```

#### `config.py`
Dashboard-specific configuration (colors, labels, file paths).

#### `components/`
Reusable UI components:
- `charts.py` - Plotly visualizations
- `tables.py` - Data tables
- `metrics.py` - KPI cards

#### `data/`
Data loading utilities for violations and alerts.

---

## Output Formats

### Violation Record

```json
{
  "conversation_id": "conv_001",
  "original_text": "Example toxic message",
  "weighted_score": 0.72,
  "severity": "medium",
  "toxicity_labels": ["toxicity", "insult"],
  "timestamp": "2025-01-31T10:30:00+00:00"
}
```

### Alert Record

```json
{
  "alert_id": "alert_conv_001_1706729400",
  "conversation_id": "conv_001",
  "danger_level": "high",
  "window_score": 1.62,
  "violation_count": 3,
  "timestamp": "2025-01-31T10:30:00+00:00"
}
```

---

## Kafka Topics

| Topic | Direction | Description |
|-------|-----------|-------------|
| `llm.conversations` | Input | Raw messages to analyze |
| `guardrail.violations` | Output | Detected violations |

---

## Monitoring the Data Flow

### Kafka UI (Recommended)

The easiest way to monitor the data flow is through the Kafka UI:

1. Open **http://localhost:8080** in your browser
2. Click on **"Topics"** in the left sidebar
3. You'll see two topics:
   - `llm.conversations` - Input messages
   - `guardrail.violations` - Detected violations

#### View Messages in a Topic

1. Click on a topic name (e.g., `llm.conversations`)
2. Click on **"Messages"** tab
3. Click **"Fetch"** or enable **"Live mode"** for real-time updates
4. You can see:
   - Message content (JSON)
   - Partition and offset
   - Timestamp
   - Message key

#### Monitor Consumer Groups

1. Click on **"Consumer Groups"** in the left sidebar
2. You'll see:
   - `guardrail-input-processor-group` - The toxicity processor
   - `alert-consumer-group` - The alert aggregator
3. Click on a group to see:
   - Lag (how many messages behind)
   - Current offset vs end offset
   - Which partitions are assigned

### Command Line Monitoring

#### List Topics

```bash
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

#### View Topic Details

```bash
# Describe a topic (partitions, replicas, etc.)
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic llm.conversations
```

#### Read Messages from a Topic

```bash
# Read from beginning (all messages)
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic llm.conversations \
  --from-beginning

# Read only new messages (real-time)
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic llm.conversations

# Read violations
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic guardrail.violations \
  --from-beginning
```

Press `Ctrl+C` to stop reading.

#### Check Consumer Group Status

```bash
# List all consumer groups
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list

# Describe a consumer group (see lag, offsets)
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group guardrail-input-processor-group
```

#### Count Messages in a Topic

```bash
# Get message count per partition
docker compose exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic llm.conversations
```

### Container Logs

The easiest way to monitor the data flow is through Docker Compose logs.

#### Watch All Services at Once

```bash
# Follow all logs in real-time
docker compose logs -f

# Follow all logs with timestamps
docker compose logs -f -t
```

#### Watch Specific Services

```bash
# Watch the guardrails processor (see each message being analyzed)
docker compose logs -f guardrails-processor

# Watch the alert consumer (see violations being aggregated)
docker compose logs -f alert-consumer

# Watch the dashboard
docker compose logs -f dashboard

# Watch Kafka broker
docker compose logs -f kafka
```

#### What You'll See in the Logs

**Guardrails Processor** (`docker compose logs -f guardrails-processor`):
```
# Startup - model loading
INFO | Kafka conversation consumer initialized | topic=llm.conversations
Loading weights: 100%|██████████| 201/201 [00:00<00:00]

# Processing messages
INFO | [Violation] conversation=conv_001 severity=high score=0.9234
INFO | [Violation] conversation=conv_002 severity=medium score=0.6521
DEBUG | Conversation conv_003: clean

# Statistics on shutdown
INFO | Conversations processed: 100
INFO | Violations detected: 45
INFO |   HIGH: 12
INFO |   MEDIUM: 18
INFO |   LOW: 15
```

**Alert Consumer** (`docker compose logs -f alert-consumer`):
```
# Startup
INFO | AlertConsumer initialized | topic=guardrail.violations window=300s

# Processing violations
DEBUG | [Consumer] received violation conversation=conv_001 score=0.9234
DEBUG | [Consumer] window updated conversation=conv_001 count=3
WARNING | [HIGH ALERT] conversation=conv_001 window_score=1.823 violations=3

# Statistics
INFO | Violations processed: 45
INFO | Alerts generated: 8
```

#### Filter and Search Logs

```bash
# Last 50 lines from processor
docker compose logs --tail 50 guardrails-processor

# Last 100 lines from alert consumer
docker compose logs --tail 100 alert-consumer

# Search for violations only
docker compose logs guardrails-processor 2>&1 | grep "Violation"

# Search for alerts only
docker compose logs alert-consumer 2>&1 | grep "ALERT"

# Search for errors
docker compose logs guardrails-processor 2>&1 | grep -i "error"

# Search for high severity only
docker compose logs guardrails-processor 2>&1 | grep "severity=high"
```

#### Monitor Multiple Services Side-by-Side

Open multiple terminal windows:

**Terminal 1 - Input Processing:**
```bash
docker compose logs -f guardrails-processor
```

**Terminal 2 - Alert Generation:**
```bash
docker compose logs -f alert-consumer
```

**Terminal 3 - Send Test Data:**
```bash
python scripts/fast_ingest_lmsys.py --csv-path data/raw/conversations.csv
```

Now you can watch messages flow through the system in real-time!

#### Log Levels

The services use different log levels:
- `DEBUG` - Detailed processing info (clean messages, window updates)
- `INFO` - Important events (violations detected, stats)
- `WARNING` - Alerts and user interrupts
- `ERROR` - Problems that need attention

To see DEBUG messages, check if they're enabled in the service configuration.

### Data Flow Verification

To verify the complete data flow is working:

```bash
# 1. Check input topic has messages
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic llm.conversations \
  --from-beginning \
  --max-messages 1

# 2. Check violations are being produced
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic guardrail.violations \
  --from-beginning \
  --max-messages 1

# 3. Check output files exist
ls -la outputs/

# 4. View latest violations
tail -5 outputs/kafka_violations.jsonl

# 5. View latest alerts
tail -5 outputs/alerts.jsonl
```

### Troubleshooting Data Flow

| Symptom | Check | Solution |
|---------|-------|----------|
| No messages in `llm.conversations` | Run ingestion script | `python scripts/fast_ingest_lmsys.py` |
| Messages in input but not in violations | Check processor logs | `docker compose logs guardrails-processor` |
| Processor shows errors | Check Kafka connection | `docker compose restart guardrails-processor` |
| High consumer lag | Processor too slow | Check CPU/memory, reduce batch size |
| No alerts generated | Check alert consumer | `docker compose logs alert-consumer` |

---

## License

Apache License 2.0

---

## Author

**gez2code**  
GitHub: [github.com/gez2code/LLM-Guardrails-Monitoring-3.0](https://github.com/gez2code/LLM-Guardrails-Monitoring-3.0)

### Credits

Based on the original project by **TipsyPanda**: [github.com/TipsyPanda/LLM-Monitoring-guardrails](https://github.com/TipsyPanda/LLM-Monitoring-guardrails)
