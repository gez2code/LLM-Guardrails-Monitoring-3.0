import json
from kafka import KafkaConsumer
from loguru import logger
from typing import Iterator

from src.models.conversation import Conversation


class ConversationConsumer:
    """Kafka consumer for receiving LLM conversation events"""

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str = "llm.conversations",
        consumer_group: str = "guardrail-input-processor-group",
        enabled: bool = True,
        auto_offset_reset: str = "earliest",  # 🔥 DEV-FRIENDLY DEFAULT
    ):
        self.enabled = enabled
        self.topic = topic
        self.consumer_group = consumer_group
        self.receive_count = 0
        self.error_count = 0

        if not self.enabled:
            logger.warning("Kafka conversation consumer is DISABLED")
            return

        try:
            self.consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers.split(","),
                group_id=consumer_group,
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )

            logger.info(
                "Kafka conversation consumer initialized | "
                f"topic={topic} "
                f"group={consumer_group} "
                f"offset_reset={auto_offset_reset}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            self.enabled = False
            raise

    def consume_conversations(self) -> Iterator[Conversation]:
        """
        Generator that yields Conversation objects from Kafka
        """
        if not self.enabled:
            logger.warning("consume_conversations called but consumer is disabled")
            return

        logger.info("Starting to consume conversations from Kafka")

        for message in self.consumer:
            try:
                raw = message.value

                # 🔍 Deep debug (toggle if noisy)
                logger.debug(
                    f"[Kafka] raw message received | "
                    f"partition={message.partition} "
                    f"offset={message.offset}"
                )

                conversation = Conversation.from_dict(raw)
                self.receive_count += 1

                logger.debug(
                    f"Received conversation | "
                    f"id={conversation.conversation_id}"
                )

                yield conversation

            except Exception as e:
                self.error_count += 1
                logger.warning(
                    "Error parsing conversation message | "
                    f"error={e} | payload={message.value}"
                )
                continue

    def close(self):
        """Close the consumer"""
        if self.enabled and hasattr(self, "consumer"):
            try:
                logger.info(
                    f"Closing Kafka consumer | "
                    f"received={self.receive_count} "
                    f"errors={self.error_count}"
                )
                self.consumer.close()
                logger.info("Kafka consumer closed successfully")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {e}")

    def get_stats(self):
        return {
            "enabled": self.enabled,
            "received": self.receive_count,
            "errors": self.error_count,
            "topic": self.topic,
            "group": self.consumer_group,
        }
