# LLM Guardrails Monitoring 3.0

## Project Goal

**Real-time toxicity detection for LLM conversations** - Monitor and filter harmful content before it reaches your users.

This system analyzes messages in real-time using machine learning (Detoxify), detects toxic content across 7 categories (insults, threats, hate speech, etc.), and provides a live monitoring dashboard with alerts.

### What It Does

```
User Message → Kafka → Toxicity Analysis → Violation Detection → Alert Dashboard
```

1. **Ingests** conversations from CSV files or HuggingFace datasets
2. **Analyzes** each message using Detoxify ML model (7 toxicity labels)
3. **Scores** content with configurable severity weights (threats weighted higher)
4. **Classifies** violations as LOW / MEDIUM / HIGH severity
5. **Aggregates** violations over time windows to generate alerts
6. **Visualizes** everything in a real-time Streamlit dashboard

### Use Cases

- **Content Moderation**: Pre-filter user messages before they reach an LLM
- **Safety Monitoring**: Track toxic patterns in chatbot conversations
- **Compliance**: Audit trail of all detected violations
- **Research**: Analyze toxicity patterns in conversation datasets

---

## Quick Start (5 Minutes)

### Prerequisites

- **Docker Desktop** - [Download for Windows](https://docs.docker.com/desktop/install/windows-install/) | [Download for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Python 3.10+**
- **Guardrails Token** (free) - [Get one here](https://hub.guardrailsai.com/)
- **HuggingFace Token** (optional) - [Get one here](https://huggingface.co/settings/tokens) - Only needed for LMSYS dataset

### Step 1: Clone & Configure

**Clone repository:**

| OS | Command |
|----|---------|
| **Windows & Mac** | `git clone https://github.com/gez2code/LLM-Guardrails-Monitoring-3.0.git` |
| **Windows & Mac** | `cd LLM-Guardrails-Monitoring-3.0` |

**Create environment file:**

| OS | Command |
|----|---------|
| **Windows (PowerShell/CMD)** | `copy .env.example .env` |
| **Mac / Linux** | `cp .env.example .env` |

**Edit `.env`** and add your tokens:

```env
# Required
GUARDRAILS_TOKEN=your_guardrails_token_here

# Optional (only for HuggingFace dataset)
HF_TOKEN=your_huggingface_token_here
```

### Step 2: Start Services

| OS | Command |
|----|---------|
| **Windows & Mac** | `docker compose up --build -d` |

First build takes ~10 minutes (downloads ML models).

**Verify all containers are running:**

| OS | Command |
|----|---------|
| **Windows & Mac** | `docker compose ps` |

All containers should show "running" or "healthy".

### Step 3: Setup Python Environment

**Create virtual environment:**

| OS | Command |
|----|---------|
| **Windows** | `python -m venv venv` |
| **Mac / Linux** | `python3 -m venv venv` |

**Activate virtual environment:**

| OS | Command |
|----|---------|
| **Windows (PowerShell)** | `.\venv\Scripts\Activate.ps1` |
| **Windows (CMD)** | `venv\Scripts\activate.bat` |
| **Mac / Linux** | `source venv/bin/activate` |

**Install dependencies:**

| OS | Command |
|----|---------|
| **Windows & Mac** | `pip install -r requirements.txt` |

### Step 4: Ingest Data

Choose **ONE** of the following options:

#### Option A: CSV Sample Data (Quick Test)

Uses included sample file with 28 messages. No additional setup needed.

| OS | Command |
|----|---------|
| **Windows** | `python scripts/fast_ingest_lmsys.py --csv-path data/raw/conversations.csv` |
| **Mac / Linux** | `python3 scripts/fast_ingest_lmsys.py --csv-path data/raw/conversations.csv` |

#### Option B: HuggingFace Dataset (More Data)

Loads real conversations from LMSYS-Chat-1M dataset.

**Prerequisites:**
1. Add `HF_TOKEN` to your `.env` file
2. Request dataset access at [huggingface.co/datasets/lmsys/lmsys-chat-1m](https://huggingface.co/datasets/lmsys/lmsys-chat-1m)
3. Wait for approval (can take minutes to days)

| OS | Command |
|----|---------|
| **Windows** | `python scripts/hf_ingest_lmsys.py --limit 100` |
| **Mac / Linux** | `python3 scripts/hf_ingest_lmsys.py --limit 100` |

**Parameters:**
- `--limit 100` = Load 100 conversations
- `--limit 1000` = Load 1000 conversations
- `--user-only` = Only analyze user messages (skip assistant responses)

### Step 5: Open Dashboard

🎉 **Open http://localhost:8501 in your browser**

You should see violations appearing within seconds!

### Quick Links

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:8501 | Real-time monitoring UI |
| **Kafka UI** | http://localhost:8080 | Message inspection & debugging |

### Stop Services

| OS | Command | Description |
|----|---------|-------------|
| **Windows & Mac** | `docker compose down` | Stop containers (keep data) |
| **Windows & Mac** | `docker compose down -v` | Stop and remove all data |

---

## Features

- **Multi-Label Toxicity Detection**: 7 categories via Detoxify ML model
- **Weighted Severity Scoring**: Threats and hate speech weighted higher
- **Real-Time Processing**: Kafka-based streaming architecture
- **Sliding Window Alerts**: Time-aggregated alert generation
- **Horizontal Scaling**: Run multiple processors in parallel
- **Monitoring Dashboard**: Live Streamlit visualization
- **Dockerized**: One command to start everything

> **Version 3.0** - Complete rewrite with improved configuration, better error handling, and comprehensive documentation.
>
> Based on the original project by [TipsyPanda](https://github.com/TipsyPanda/LLM-Monitoring-guardrails)

---

## Understanding Kafka in This Project

### What is Kafka?

**Apache Kafka** is a distributed event streaming platform - think of it as a high-speed message highway between services.

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Producer  │ ──────► │    KAFKA    │ ──────► │   Consumer  │
│ (sends msg) │         │   (stores)  │         │ (reads msg) │
└─────────────┘         └─────────────┘         └─────────────┘
```

**Why Kafka instead of direct connections?**
- **Decoupling**: Producers and consumers don't need to know about each other
- **Buffering**: Messages are stored even if consumers are slow or offline
- **Scalability**: Multiple consumers can read from the same topic in parallel
- **Reliability**: Messages aren't lost if a service crashes

### Topics Explained

A **Topic** is like a named channel or mailbox where messages are stored.

```
┌─────────────────────────────────────────────────────────────┐
│                         KAFKA                                │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Topic: llm.conversations                            │   │
│   │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐           │   │
│   │  │msg 1│ │msg 2│ │msg 3│ │msg 4│ │msg 5│ ──►       │   │
│   │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘           │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Topic: guardrail.violations                         │   │
│   │  ┌─────┐ ┌─────┐ ┌─────┐                            │   │
│   │  │vio 1│ │vio 2│ │vio 3│ ──►                        │   │
│   │  └─────┘ └─────┘ └─────┘                            │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Topics in This Project

| Topic | Purpose | Producer | Consumer |
|-------|---------|----------|----------|
| `llm.conversations` | Raw user messages waiting to be analyzed | Ingestion scripts | Guardrails Processor |
| `guardrail.violations` | Detected toxic content | Guardrails Processor | Alert Consumer |

### How Messages Flow

```
                        YOUR DATA
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 1: You run an ingestion script                                  │
│                                                                       │
│  python scripts/fast_ingest_lmsys.py                                 │
│         │                                                             │
│         ▼                                                             │
│  Script reads CSV/HuggingFace data and sends each message to Kafka   │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 2: Messages land in llm.conversations topic                     │
│                                                                       │
│  Kafka stores them and waits for a consumer to read them             │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 3: Guardrails Processor (Docker container) reads messages       │
│                                                                       │
│  For each message:                                                    │
│  • Runs Detoxify ML model                                            │
│  • Calculates toxicity scores                                        │
│  • If toxic → sends to guardrail.violations topic                    │
│  • If clean → discards                                               │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 4: Alert Consumer (Docker container) reads violations           │
│                                                                       │
│  • Aggregates violations in 5-minute windows                         │
│  • Generates alerts when thresholds exceeded                         │
│  • Writes to outputs/alerts.jsonl                                    │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 5: Dashboard reads output files and displays results            │
│                                                                       │
│  http://localhost:8501                                               │
└──────────────────────────────────────────────────────────────────────┘
```

### Consumer Groups

A **Consumer Group** is a team of consumers that work together to read from a topic. Kafka ensures each message is processed by only ONE consumer in the group.

```
                    llm.conversations
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
     ┌─────────┐    ┌─────────┐    ┌─────────┐
     │Processor│    │Processor│    │Processor│
     │   #1    │    │   #2    │    │   #3    │
     └─────────┘    └─────────┘    └─────────┘
          │               │               │
          └───────────────┴───────────────┘
                          │
                Consumer Group:
          "guardrail-input-processor-group"
          
     Kafka distributes messages evenly!
     No message is processed twice.
```

| Consumer Group | Service | Can Scale? | Purpose |
|----------------|---------|------------|---------|
| `guardrail-input-processor-group` | Guardrails Processor | Yes (1-N) | Parallel toxicity analysis |
| `alert-consumer-group` | Alert Consumer | No (1 only) | Maintains time-window state |

### Viewing Kafka Data

**Kafka UI (Recommended):** Open http://localhost:8080

- Click **Topics** → See all topics and message counts
- Click a topic → **Messages** → See actual message content
- Click **Consumer Groups** → See processing progress and lag

**Command Line:**

| OS | Command | Description |
|----|---------|-------------|
| **Windows & Mac** | `docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list` | List all topics |
| **Windows & Mac** | `docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic llm.conversations --from-beginning` | Read all messages |

Press `Ctrl+C` to stop reading messages.

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

## Token Setup (Detailed)

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

---

## Architecture

### System Overview

This system implements a **real-time toxicity monitoring pipeline** using event-driven architecture. Messages flow through Kafka topics, get analyzed by ML models, and results are aggregated into actionable alerts.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER COMPOSE                                  │
│                                                                              │
│  ┌─────────────┐      ┌─────────────┐      ┌──────────────┐                 │
│  │  Zookeeper  │◄────►│    Kafka    │◄────►│   Kafka UI   │                 │
│  │    :2181    │      │    :9092    │      │    :8080     │                 │
│  └─────────────┘      └──────┬──────┘      └──────────────┘                 │
│         │                    │                    │                          │
│   Cluster         Message Broker          Web Interface                     │
│   Coordination    (Event Streaming)       (Monitoring)                      │
│                              │                                               │
│              ┌───────────────┴───────────────┐                              │
│              │                               │                              │
│              ▼                               ▼                              │
│   Topic: llm.conversations       Topic: guardrail.violations                │
│   (Raw user messages)            (Detected toxic content)                   │
│              │                               ▲                              │
│              ▼                               │                              │
│  ┌───────────────────────┐                   │                              │
│  │  Guardrails Processor │───────────────────┘                              │
│  │  ┌─────────────────┐  │                                                  │
│  │  │ Detoxify Model  │  │  ML-based toxicity detection                    │
│  │  │ (7 labels)      │  │  with multi-label classification                │
│  │  └─────────────────┘  │                                                  │
│  │  ┌─────────────────┐  │                                                  │
│  │  │ Weighted Scoring│  │  Configurable impact weights                    │
│  │  │ (threat=2.0x)   │  │  prioritize dangerous content                   │
│  │  └─────────────────┘  │                                                  │
│  │  ┌─────────────────┐  │                                                  │
│  │  │ Severity Bucket │  │  LOW / MEDIUM / HIGH                            │
│  │  │ Classification  │  │  based on weighted scores                       │
│  │  └─────────────────┘  │                                                  │
│  └───────────────────────┘                                                  │
│              │                                                               │
│              │ Violations only (toxic messages)                             │
│              ▼                                                               │
│  ┌───────────────────────┐                                                  │
│  │    Alert Consumer     │                                                  │
│  │  ┌─────────────────┐  │                                                  │
│  │  │ Sliding Window  │  │  5-minute aggregation window                    │
│  │  │ (300 seconds)   │  │  per conversation                               │
│  │  └─────────────────┘  │                                                  │
│  │  ┌─────────────────┐  │                                                  │
│  │  │ Score Summation │  │  Cumulative violation scores                    │
│  │  │ & Thresholds    │  │  trigger alert levels                           │
│  │  └─────────────────┘  │                                                  │
│  └───────────┬───────────┘                                                  │
│              │                                                               │
│              ▼                                                               │
│  ┌───────────────────────┐      ┌───────────────────────┐                   │
│  │   outputs/            │      │      Dashboard        │                   │
│  │   ├─ violations.jsonl │◄────►│        :8501          │                   │
│  │   └─ alerts.jsonl     │      │   (Streamlit UI)      │                   │
│  └───────────────────────┘      └───────────────────────┘                   │
│         │                              │                                     │
│   Persistent Storage           Real-time Visualization                      │
│   (Audit Trail)                (Monitoring Dashboard)                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

#### 1. Zookeeper (Port 2181)
**Role:** Distributed coordination service for Kafka cluster management.

- Maintains broker metadata and topic configurations
- Handles leader election for Kafka partitions
- Stores consumer group offsets (legacy mode)
- Required for Kafka to function

#### 2. Kafka Broker (Port 9092)
**Role:** Distributed event streaming platform - the backbone of the system.

- Receives messages from producers (ingestion scripts)
- Stores messages in topics with configurable retention
- Delivers messages to consumers (processors)
- Enables decoupled, scalable architecture

**Topics:**
| Topic | Purpose | Retention |
|-------|---------|-----------|
| `llm.conversations` | Incoming user messages to analyze | 7 days |
| `guardrail.violations` | Detected toxic content | 7 days |

#### 3. Kafka UI (Port 8080)
**Role:** Web-based interface for Kafka monitoring and debugging.

- View topic contents and message flow
- Monitor consumer group lag
- Inspect message payloads
- Debug connectivity issues

#### 4. Guardrails Processor (Container)
**Role:** Core ML processing engine - analyzes messages for toxic content.

**Processing Pipeline:**
```
Input Message
    │
    ▼
┌─────────────────────────────────────┐
│         DETOXIFY MODEL              │
│  Multilingual BERT-based classifier │
│  trained on Wikipedia toxicity data │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│      7-LABEL CLASSIFICATION         │
│  toxicity:        0.0 - 1.0        │
│  severe_toxicity: 0.0 - 1.0        │
│  insult:          0.0 - 1.0        │
│  threat:          0.0 - 1.0        │
│  identity_attack: 0.0 - 1.0        │
│  obscene:         0.0 - 1.0        │
│  sexual_explicit: 0.0 - 1.0        │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│       WEIGHTED SCORING              │
│  Apply impact weights:              │
│  • threat × 2.0 (dangerous)         │
│  • identity_attack × 2.0 (hate)     │
│  • severe_toxicity × 2.5 (extreme)  │
│  • others × 1.0 (baseline)          │
│                                     │
│  weighted_score = MAX(all weighted) │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│       BINARY DECISION GATE          │
│                                     │
│  weighted_score >= 0.10 ?           │
│     YES → Violation (continue)      │
│     NO  → Clean (discard)           │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│      SEVERITY CLASSIFICATION        │
│                                     │
│  0.10 - 0.59 → LOW (yellow)         │
│  0.60 - 0.84 → MEDIUM (orange)      │
│  0.85+       → HIGH (red)           │
└─────────────────┬───────────────────┘
                  │
                  ▼
           Output Violation
```

#### 5. Alert Consumer (Container)
**Role:** Aggregates violations over time and generates alerts.

**Why Aggregation?**
- Single violations may be false positives
- Patterns over time indicate real problems
- Reduces alert fatigue for operators

**Sliding Window Algorithm:**
```
Time ────────────────────────────────────────────►

Window (300 seconds)
├─────────────────────────────────────────────────┤

Violations in window:
┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐
│ V1  │  │ V2  │  │ V3  │  │ V4  │
│0.45 │  │0.85 │  │0.32 │  │0.91 │
└─────┘  └─────┘  └─────┘  └─────┘
    │        │        │        │
    └────────┴────────┴────────┘
                  │
                  ▼
    window_score = Σ = 2.53
                  │
                  ▼
    2.53 >= 0.80 → HIGH ALERT 🚨
```

**Alert Thresholds:**
| Window Score | Alert Level | Action |
|--------------|-------------|--------|
| ≥ 0.15 | LOW | Log for review |
| ≥ 0.40 | MEDIUM | Notify moderator |
| ≥ 0.80 | HIGH | Immediate action |

#### 6. Dashboard (Port 8501)
**Role:** Real-time visualization and monitoring interface.

**Features:**
- Live violation feed with severity highlighting
- Time-series charts of violation trends
- Alert history and statistics
- Filter by severity, time range, conversation
- Export data for further analysis

### Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW                                       │
└──────────────────────────────────────────────────────────────────────────┘

STEP 1: INGESTION
─────────────────
    CSV File                    HuggingFace                 Custom App
        │                           │                           │
        ▼                           ▼                           ▼
    fast_ingest_lmsys.py    hf_ingest_lmsys.py          Kafka Producer
        │                           │                           │
        └───────────────────────────┴───────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  llm.conversations    │
                        │  (Kafka Topic)        │
                        └───────────┬───────────┘
                                    │
STEP 2: PROCESSING                  │
──────────────────                  ▼
                        ┌───────────────────────┐
                        │  Guardrails Processor │
                        │  • Consume message    │
                        │  • Run Detoxify       │
                        │  • Calculate scores   │
                        │  • Classify severity  │
                        └───────────┬───────────┘
                                    │
                            ┌───────┴───────┐
                            │               │
                        CLEAN           VIOLATION
                        (discard)           │
                                            ▼
                        ┌───────────────────────┐
                        │ guardrail.violations  │
                        │ (Kafka Topic)         │
                        └───────────┬───────────┘
                                    │
STEP 3: AGGREGATION                 │
───────────────────                 ▼
                        ┌───────────────────────┐
                        │    Alert Consumer     │
                        │  • Consume violation  │
                        │  • Add to window      │
                        │  • Check thresholds   │
                        │  • Generate alert     │
                        └───────────┬───────────┘
                                    │
                            ┌───────┴───────┐
                            │               │
                     NO ALERT          ALERT TRIGGERED
                     (continue)             │
                                            ▼
STEP 4: OUTPUT                  ┌───────────────────┐
──────────────                  │  outputs/         │
                                │  ├─ violations.jsonl
                                │  └─ alerts.jsonl  │
                                └─────────┬─────────┘
                                          │
STEP 5: VISUALIZATION                     │
─────────────────────                     ▼
                                ┌───────────────────┐
                                │    Dashboard      │
                                │  • Read JSONL     │
                                │  • Render charts  │
                                │  • Show alerts    │
                                └───────────────────┘
```

### Horizontal Scaling

The architecture supports horizontal scaling for high-throughput scenarios:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SCALED DEPLOYMENT                                 │
│                                                                          │
│    llm.conversations (3 partitions)                                     │
│    ┌─────────┬─────────┬─────────┐                                      │
│    │ Part 0  │ Part 1  │ Part 2  │                                      │
│    └────┬────┴────┬────┴────┬────┘                                      │
│         │         │         │                                            │
│         ▼         ▼         ▼                                            │
│    ┌─────────┐ ┌─────────┐ ┌─────────┐                                  │
│    │Processor│ │Processor│ │Processor│  Consumer Group                  │
│    │   #1    │ │   #2    │ │   #3    │  (load balanced)                 │
│    └────┬────┘ └────┬────┘ └────┬────┘                                  │
│         │         │         │                                            │
│         └─────────┴─────────┘                                            │
│                   │                                                      │
│                   ▼                                                      │
│         guardrail.violations                                            │
│                   │                                                      │
│                   ▼                                                      │
│            ┌─────────────┐                                              │
│            │   Alert     │  Single aggregator                           │
│            │  Consumer   │  (maintains window state)                    │
│            └─────────────┘                                              │
└─────────────────────────────────────────────────────────────────────────┘

Scale command:
docker compose up --scale guardrails-processor=3 -d
```

**Scaling Considerations:**
- **Partitions = Max Parallelism**: One partition can only be consumed by one processor
- **State Management**: Alert Consumer should remain single instance (maintains window state)
- **Resource Limits**: Each processor loads the Detoxify model (~400MB memory)

### Message Formats

#### Input Message (llm.conversations)
```json
{
  "conversation_id": "conv_abc123",
  "text": "The actual message content to analyze",
  "timestamp": "2025-01-31T10:30:00Z",
  "speaker": "user",
  "metadata": {
    "source": "chat_app",
    "user_id": "user_456"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conversation_id` | string | ✓ | Unique identifier for the conversation |
| `text` | string | ✓ | Message content to analyze |
| `timestamp` | ISO8601 | ✗ | When the message was sent |
| `speaker` | string | ✗ | Who sent the message (user/assistant) |
| `metadata` | object | ✗ | Additional context |

#### Violation Message (guardrail.violations)
```json
{
  "conversation_id": "conv_abc123",
  "original_text": "The toxic message content",
  "weighted_score": 0.8234,
  "severity": "high",
  "toxicity_labels": ["toxicity", "insult", "threat"],
  "timestamp": "2025-01-31T10:30:01Z",
  "metadata": {
    "scores": {
      "toxicity": 0.72,
      "severe_toxicity": 0.15,
      "insult": 0.68,
      "threat": 0.41,
      "identity_attack": 0.08,
      "obscene": 0.45,
      "sexual_explicit": 0.02
    },
    "weights_applied": {
      "threat": 2.0,
      "identity_attack": 2.0,
      "severe_toxicity": 2.5
    },
    "violation_threshold": 0.10,
    "model": "detoxify-original"
  }
}
```

#### Alert Message (outputs/alerts.jsonl)
```json
{
  "alert_id": "alert_conv_abc123_1706729400",
  "conversation_id": "conv_abc123",
  "danger_level": "high",
  "window_score": 2.53,
  "violation_count": 4,
  "window_size_minutes": 5,
  "timestamp": "2025-01-31T10:35:00Z",
  "summary": {
    "labels": ["toxicity", "insult", "threat"],
    "max_severity": "high",
    "violations": [
      {"score": 0.45, "severity": "low"},
      {"score": 0.85, "severity": "high"},
      {"score": 0.32, "severity": "low"},
      {"score": 0.91, "severity": "high"}
    ]
  }
}
```

### Consumer Groups

| Consumer Group | Service | Instances | Purpose |
|----------------|---------|-----------|---------|
| `guardrail-input-processor-group` | Guardrails Processor | 1-N | Parallel processing; Kafka distributes partitions |
| `alert-consumer-group` | Alert Consumer | 1 | Single aggregator; maintains time-window state |

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
