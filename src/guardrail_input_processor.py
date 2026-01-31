import json
from pathlib import Path
from loguru import logger

from src.config import KafkaInputConfig
from src.kafka.conversation_consumer import ConversationConsumer
from src.kafka.violation_producer import ViolationProducer
from src.processors.guardrail_processor import GuardrailProcessor


class GuardrailInputProcessor:
    """
    Kafka-based input processor for LLM conversations

    Responsibilities:
    - Consume conversations from Kafka
    - Delegate policy decisions to GuardrailProcessor
    - Emit violations (binary decision)
    - Track operational statistics
    """

    def __init__(self, config: KafkaInputConfig):
        self.config = config

        # Kafka consumer (input)
        self.consumer = ConversationConsumer(
            bootstrap_servers=config.BOOTSTRAP_SERVERS,
            topic=config.INPUT_TOPIC,
            consumer_group=config.CONSUMER_GROUP,
            enabled=True,
        )

        # 🔥 Policy + decision engine (NO detoxify threshold here)
        self.processor = GuardrailProcessor()

        # Kafka producer (output)
        self.producer = ViolationProducer(
            bootstrap_servers=config.BOOTSTRAP_SERVERS,
            topic=config.OUTPUT_TOPIC,
            enabled=True,
        )

        # Ensure backup directory exists
        output_path = Path(config.OUTPUT_FILE)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Runtime statistics (policy-agnostic)
        self.stats = {
            "conversations_processed": 0,
            "violations_detected": 0,
            "violations_by_bucket": {
                "low": 0,
                "medium": 0,
                "high": 0,
            },
        }

    # ------------------------------------------------------------------

    def run(self):
        """Main processing loop"""
        logger.info("=" * 60)
        logger.info("Starting Guardrail Input Processor")
        logger.info(f"Input Topic: {self.config.INPUT_TOPIC}")
        logger.info(f"Output Topic: {self.config.OUTPUT_TOPIC}")
        logger.info(f"Backup Output: {self.config.OUTPUT_FILE}")
        logger.info("=" * 60)

        try:
            with open(self.config.OUTPUT_FILE, "a") as backup_file:
                for conversation in self.consumer.consume_conversations():
                    self._process_conversation(conversation, backup_file)

        except KeyboardInterrupt:
            logger.warning("Shutdown requested by user")
        except Exception as e:
            logger.exception(f"Fatal error in processing loop: {e}")
            raise
        finally:
            self._log_shutdown_stats()
            self.consumer.close()
            self.producer.close()

    # ------------------------------------------------------------------

    def _process_conversation(self, conversation, backup_file):
        """
        Process a single conversation message
        """
        self.stats["conversations_processed"] += 1

        # 🔥 Policy decision happens here
        violation = self.processor.process_conversation(conversation)

        if violation is None:
            logger.debug(
                f"Conversation {conversation.conversation_id}: clean"
            )
            return

        # Binary violation confirmed
        self.stats["violations_detected"] += 1
        self.stats["violations_by_bucket"][violation.severity.value] += 1

        logger.info(
            f"[Violation] conversation={violation.conversation_id} "
            f"severity={violation.severity.value} "
            f"score={violation.weighted_score:.4f} "
        )

        # Persist locally (audit / replay)
        backup_file.write(json.dumps(violation.to_dict()) + "\n")
        backup_file.flush()

        # Emit downstream
        self.producer.send_violation(violation)

    # ------------------------------------------------------------------

    def _log_shutdown_stats(self):
        """Log final statistics"""
        logger.info("\n" + "=" * 60)
        logger.info("Guardrail Input Processor shutdown")
        logger.info(f"Conversations processed: {self.stats['conversations_processed']}")
        logger.info(f"Violations detected: {self.stats['violations_detected']}")

        for bucket, count in self.stats["violations_by_bucket"].items():
            logger.info(f"  {bucket.upper()}: {count}")

        logger.info("=" * 60)


def main():
    """Service entrypoint"""
    config = KafkaInputConfig()
    service = GuardrailInputProcessor(config)
    service.run()


if __name__ == "__main__":
    main()
