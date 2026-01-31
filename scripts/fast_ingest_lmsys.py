#!/usr/bin/env python3
"""
Fast LMSYS Dataset Ingestion Script

Ingests the LMSYS dataset into Kafka as fast as possible (no time delays).
This is the "3te Option" mentioned in the to-do.

Usage:
    python scripts/fast_ingest_lmsys.py --csv-path data/raw/lmsys_conversations.csv
"""

import json
import argparse
import pandas as pd
from datetime import datetime
from kafka import KafkaProducer
from loguru import logger
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import KafkaInputConfig


class FastLMSYSIngester:
    """Fast ingestion of LMSYS dataset into Kafka"""

    def __init__(self, bootstrap_servers: str, topic: str):
        """
        Initialize the fast ingester

        Args:a
            bootstrap_servers: Kafka bootstrap servers
            topic: Topic to produce conversations to
        """
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(','),
            acks='all',
            batch_size=16384,  # Larger batch for faster throughput
            linger_ms=10,  # Small linger for batching
            compression_type=None,  # Compression for better performance
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.sent_count = 0
        self.error_count = 0
        logger.info(f"Fast ingester initialized: {bootstrap_servers}, topic: {topic}")

    def send_conversation(self, conversation: dict) -> bool:
        """
        Send a conversation to Kafka (non-blocking)

        Args:
            conversation: Conversation dictionary

        Returns:
            True if sent successfully
        """
        try:
            # Non-blocking send for maximum throughput
            self.producer.send(
                self.topic,
                key=conversation['conversation_id'].encode('utf-8'),
                value=conversation
            )
            self.sent_count += 1
            
            # Log progress every 1000 messages
            if self.sent_count % 1000 == 0:
                logger.info(f"Sent {self.sent_count} messages...")
            
            return True
        except Exception as e:
            self.error_count += 1
            if self.error_count <= 10:  # Only log first 10 errors
                logger.error(f"Failed to send conversation: {e}")
            return False

    def ingest_from_csv(self, csv_path: str, user_only: bool = False):
        """
        Ingest all conversations from CSV file as fast as possible

        Args:
            csv_path: Path to CSV file
            user_only: If True, only send user messages (not agent messages)
        """
        csv_path = Path(csv_path)
        
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return

        logger.info(f"Loading dataset from: {csv_path}")
        df = pd.read_csv(csv_path)
        
        total_messages = len(df)
        logger.info(f"Total messages in dataset: {total_messages}")
        
        if user_only:
            df = df[df['speaker'] == 'user']
            logger.info(f"Filtering to user messages only: {len(df)} messages")
        
        logger.info("Starting fast ingestion (no delays)...")
        start_time = datetime.now()

        try:
            for _, row in df.iterrows():
                conversation = {
                    'conversation_id': row['conversation_id'],
                    'text': row['text'],
                    'timestamp': row['timestamp'],
                    'speaker': row['speaker']
                }
                self.send_conversation(conversation)

        except KeyboardInterrupt:
            logger.info(f"\nIngestion interrupted by user")
        except Exception as e:
            logger.error(f"Error during ingestion: {e}")
        finally:
            # Flush all pending messages
            logger.info("Flushing pending messages...")
            self.producer.flush()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("\n" + "="*60)
            logger.info("Ingestion Complete!")
            logger.info("="*60)
            logger.info(f"Total messages sent: {self.sent_count}")
            logger.info(f"Total errors: {self.error_count}")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Throughput: {self.sent_count/duration:.2f} messages/second")
            logger.info("="*60)
            
            self.producer.close()


def main():
    parser = argparse.ArgumentParser(
        description='Fast ingestion of LMSYS dataset into Kafka'
    )
    parser.add_argument(
    '--csv-path', type=str, 
    default='data/raw/conversations.csv',  # <-- Default value
    help='Path to LMSYS CSV file'
)
    parser.add_argument(
        '--user-only', action='store_true',
        help='Only ingest user messages (skip agent responses)'
    )
    parser.add_argument(
        '--bootstrap-servers', type=str, default=None,
        help='Kafka bootstrap servers (default: from config)'
    )
    parser.add_argument(
        '--topic', type=str, default=None,
        help='Kafka topic (default: from config)'
    )

    args = parser.parse_args()

    # Load config
    config = KafkaInputConfig()
    bootstrap_servers = args.bootstrap_servers or config.BOOTSTRAP_SERVERS
    topic = args.topic or config.INPUT_TOPIC

    # Create ingester
    ingester = FastLMSYSIngester(
        bootstrap_servers=bootstrap_servers,
        topic=topic
    )

    # Run ingestion
    ingester.ingest_from_csv(
        csv_path=args.csv_path,
        user_only=args.user_only
    )


if __name__ == "__main__":
    main()
