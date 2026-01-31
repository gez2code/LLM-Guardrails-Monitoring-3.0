#!/usr/bin/env python3
"""
Mock Conversation Producer

Simulates LLM user messages being sent to Kafka for testing the
guardrail input processor.

Usage:
    python scripts/mock_conversation_producer.py [--mode MODE] [--interval SECONDS]

Modes:
    - random: Random mix of clean and toxic conversations (30% toxic)
    - toxic: Only toxic conversations
    - clean: Only clean conversations
    - csv: Read from existing CSV file
"""

import json
import time
import random
import argparse
from datetime import datetime
from kafka import KafkaProducer
from loguru import logger
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import KafkaInputConfig


# Sample conversation templates
CLEAN_MESSAGES = [
    "Hello! How can I assist you today?",
    "Thank you for your help!",
    "I need help with my account",
    "What a beautiful day!",
    "Can you explain how this works?",
    "I appreciate your patience",
    "This is very helpful, thanks!",
    "Could you provide more information?",
    "I'm looking for recommendations",
    "What are the best practices for this?",
]

TOXIC_MESSAGES = [
    "You're an idiot and this service is pathetic!",
    "I will destroy you all!",
    "You stupid moron, go to hell!",
    "This is the worst service ever, you incompetent fool!",
    "I hate you and everything you stand for!",
    "Shut up you worthless piece of garbage!",
    "You're completely useless and should be fired!",
]

# Preset conversation IDs for consistent testing
CONVERSATION_IDS = [
    "conv_user_001",
    "conv_user_002",
    "conv_user_003",
    "conv_user_004",
    "conv_user_005",
    "conv_user_006",
    "conv_user_007",
    "conv_user_008",
    "conv_user_009",
    "conv_user_010",
]


class MockConversationProducer:
    """Produces mock LLM user messages to Kafka for testing"""

    def __init__(self, bootstrap_servers: str, topic: str):
        """
        Initialize the mock producer

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Topic to produce conversations to
        """
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(','),
            acks='all',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.sent_count = 0
        logger.info(f"Mock producer initialized: {bootstrap_servers}, topic: {topic}")

    def generate_conversation(self, mode: str = 'random') -> dict:
        """
        Generate a mock conversation

        Args:
            mode: 'random', 'toxic', or 'clean'

        Returns:
            Conversation dictionary
        """
        if mode == 'toxic':
            text = random.choice(TOXIC_MESSAGES)
        elif mode == 'clean':
            text = random.choice(CLEAN_MESSAGES)
        else:  # random
            # 30% chance of toxic
            if random.random() < 0.3:
                text = random.choice(TOXIC_MESSAGES)
            else:
                text = random.choice(CLEAN_MESSAGES)

        return {
            'conversation_id': random.choice(CONVERSATION_IDS),
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'speaker': 'user'
        }

    def send_conversation(self, conversation: dict) -> bool:
        """
        Send a conversation to Kafka

        Args:
            conversation: Conversation dictionary

        Returns:
            True if sent successfully
        """
        try:
            future = self.producer.send(
                self.topic,
                key=conversation['conversation_id'].encode('utf-8'),
                value=conversation
            )
            # Block to ensure delivery for testing
            future.get(timeout=10)
            self.sent_count += 1
            text_preview = conversation['text'][:50]
            if len(conversation['text']) > 50:
                text_preview += "..."
            logger.info(
                f"Sent [{self.sent_count}]: {conversation['conversation_id']} | "
                f"\"{text_preview}\""
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send conversation: {e}")
            return False

    def run_continuous(self, mode: str = 'random', interval: float = 2.0, count: int = None):
        """
        Run continuous production of mock conversations

        Args:
            mode: 'random', 'toxic', or 'clean'
            interval: Seconds between messages
            count: Number of messages to send (None for infinite)
        """
        logger.info(f"Starting continuous production: mode={mode}, interval={interval}s")
        if count:
            logger.info(f"Will send {count} messages")
        else:
            logger.info("Press Ctrl+C to stop")

        try:
            messages_sent = 0
            while count is None or messages_sent < count:
                conversation = self.generate_conversation(mode)
                self.send_conversation(conversation)
                messages_sent += 1

                if count is None or messages_sent < count:
                    time.sleep(interval)

        except KeyboardInterrupt:
            logger.info(f"\nStopped. Total conversations sent: {self.sent_count}")
        finally:
            self.producer.flush()
            self.producer.close()

    def send_from_csv(self, csv_path: str, interval: float = 1.0):
        """
        Send conversations from existing CSV file

        Args:
            csv_path: Path to CSV file
            interval: Seconds between messages
        """
        import pandas as pd

        logger.info(f"Sending conversations from: {csv_path}")
        df = pd.read_csv(csv_path)

        try:
            for _, row in df.iterrows():
                conversation = {
                    'conversation_id': row['conversation_id'],
                    'text': row['text'],
                    'timestamp': datetime.now().isoformat(),
                    'speaker': row.get('speaker', 'user')
                }
                self.send_conversation(conversation)
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info(f"\nStopped. Total conversations sent: {self.sent_count}")
        finally:
            self.producer.flush()
            self.producer.close()


def main():
    parser = argparse.ArgumentParser(description='Mock Conversation Producer')
    parser.add_argument(
        '--mode', choices=['random', 'toxic', 'clean', 'csv'],
        default='random', help='Production mode (default: random)'
    )
    parser.add_argument(
        '--interval', type=float, default=2.0,
        help='Seconds between messages (default: 2.0)'
    )
    parser.add_argument(
        '--count', type=int, default=None,
        help='Number of messages to send (default: infinite)'
    )
    parser.add_argument(
        '--csv-path', type=str, default='data/raw/conversations.csv',
        help='CSV file path for csv mode (default: data/raw/conversations.csv)'
    )

    args = parser.parse_args()

    config = KafkaInputConfig()
    producer = MockConversationProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        topic=config.KAFKA_INPUT_TOPIC
    )

    if args.mode == 'csv':
        producer.send_from_csv(args.csv_path, args.interval)
    else:
        producer.run_continuous(args.mode, args.interval, args.count)


if __name__ == "__main__":
    main()
