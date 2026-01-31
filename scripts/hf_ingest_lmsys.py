"""
HuggingFace LMSYS Dataset Ingester

Lädt Daten direkt von HuggingFace und sendet sie an Kafka.
Liest HF_TOKEN automatisch aus .env

Usage:
    python scripts/hf_ingest_lmsys.py --limit 1000
    python scripts/hf_ingest_lmsys.py --limit 5000 --user-only
"""

import argparse
import json
import os
import time
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from kafka import KafkaProducer
from loguru import logger

# Load .env file
load_dotenv()

# Auto-login to HuggingFace
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN:
    os.environ["HF_TOKEN"] = HF_TOKEN
    os.environ["HUGGING_FACE_HUB_TOKEN"] = HF_TOKEN
    logger.info("HuggingFace token loaded from .env")
else:
    logger.warning("No HF_TOKEN found in .env - gated datasets won't work")

try:
    from datasets import load_dataset
    from huggingface_hub import login
    
    if HF_TOKEN:
        try:
            login(token=HF_TOKEN, add_to_git_credential=False)
            logger.info("HuggingFace login successful!")
        except Exception as e:
            logger.warning(f"HuggingFace login failed: {e}")
    
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logger.error("datasets not installed. Run: pip install datasets huggingface_hub")


def create_producer(bootstrap_servers: str) -> KafkaProducer:
    """Create Kafka producer"""
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers.split(","),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
    )


def extract_messages(conversation: dict, user_only: bool = False, dataset_name: str = ""):
    """Extract messages from conversation format"""
    conv_id = conversation.get("conversation_id", str(uuid.uuid4()))
    messages = []
    
    # LMSYS format
    if "conversation" in conversation:
        messages = conversation.get("conversation", [])
    elif "messages" in conversation:
        messages = conversation.get("messages", [])
    elif "chosen" in conversation:
        text = conversation.get("chosen", "")
        if text:
            return [{
                "conversation_id": conv_id,
                "text": text.strip()[:5000],
                "speaker": "user",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {"source": "huggingface", "dataset": dataset_name}
            }]
    elif "text" in conversation:
        text = conversation.get("text", "")
        if text:
            return [{
                "conversation_id": conv_id,
                "text": text.strip()[:5000],
                "speaker": "user",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {"source": "huggingface", "dataset": dataset_name}
            }]
    
    extracted = []
    for i, msg in enumerate(messages):
        if isinstance(msg, dict):
            role = msg.get("role", msg.get("from", "unknown"))
            content = msg.get("content", msg.get("text", msg.get("value", "")))
        elif isinstance(msg, str):
            role = "user"
            content = msg
        else:
            continue
        
        if not content or not content.strip():
            continue
        
        if user_only and role not in ["user", "human", "prompter"]:
            continue
        
        extracted.append({
            "conversation_id": f"{conv_id}_{i}",
            "text": content.strip()[:5000],
            "speaker": role,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "source": "huggingface",
                "dataset": dataset_name,
                "original_conv_id": str(conv_id),
                "message_index": i,
            }
        })
    
    return extracted


def main():
    parser = argparse.ArgumentParser(description="Ingest data from HuggingFace to Kafka")
    parser.add_argument("--dataset", default="lmsys/lmsys-chat-1m", help="HuggingFace dataset")
    parser.add_argument("--split", default="train", help="Dataset split")
    parser.add_argument("--limit", type=int, default=1000, help="Max conversations")
    parser.add_argument("--user-only", action="store_true", help="Only user messages")
    parser.add_argument("--bootstrap-servers", default="localhost:9092", help="Kafka servers")
    parser.add_argument("--topic", default="llm.conversations", help="Kafka topic")
    parser.add_argument("--delay", type=float, default=0.01, help="Delay between messages")
    parser.add_argument("--batch-size", type=int, default=100, help="Log progress interval")

    args = parser.parse_args()

    if not HF_AVAILABLE:
        logger.error("Please install datasets: pip install datasets huggingface_hub")
        return

    stats = {"conversations": 0, "messages_sent": 0, "errors": 0, "start_time": time.time()}

    logger.info("=" * 60)
    logger.info("HuggingFace Dataset Ingester")
    logger.info("=" * 60)
    logger.info(f"Dataset: {args.dataset}")
    logger.info(f"Limit: {args.limit} conversations")
    logger.info(f"Kafka: {args.bootstrap_servers} -> {args.topic}")
    logger.info(f"HF Token: {'✓ Loaded' if HF_TOKEN else '✗ Not found'}")
    logger.info("=" * 60)

    logger.info("Loading dataset from HuggingFace...")
    
    try:
        dataset = load_dataset(args.dataset, split=args.split, streaming=True)
        logger.info("Dataset loaded with streaming!")
    except Exception as e:
        logger.warning(f"Streaming failed: {e}")
        try:
            dataset = load_dataset(args.dataset, split=args.split)
            logger.info("Dataset loaded!")
        except Exception as e2:
            logger.error(f"Failed to load dataset: {e2}")
            return

    logger.info("Connecting to Kafka...")
    try:
        producer = create_producer(args.bootstrap_servers)
        logger.info("Kafka producer connected!")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        return

    logger.info("Starting ingestion...")
    
    try:
        for conversation in dataset:
            if stats["conversations"] >= args.limit:
                break
            
            messages = extract_messages(conversation, args.user_only, args.dataset)
            
            for msg in messages:
                try:
                    producer.send(args.topic, value=msg)
                    stats["messages_sent"] += 1
                    if args.delay > 0:
                        time.sleep(args.delay)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    stats["errors"] += 1
            
            stats["conversations"] += 1
            
            if stats["conversations"] % args.batch_size == 0:
                elapsed = time.time() - stats["start_time"]
                rate = stats["messages_sent"] / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {stats['conversations']}/{args.limit} | {stats['messages_sent']} msg | {rate:.1f} msg/s")
        
        producer.flush()
        
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
    finally:
        producer.close()

    elapsed = time.time() - stats["start_time"]
    logger.info("=" * 60)
    logger.info("Ingestion Complete!")
    logger.info(f"Conversations: {stats['conversations']} | Messages: {stats['messages_sent']} | Errors: {stats['errors']}")
    logger.info(f"Time: {elapsed:.1f}s | Rate: {stats['messages_sent'] / elapsed:.1f} msg/s")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
