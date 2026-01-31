import json
from kafka import KafkaProducer
from kafka.errors import KafkaError
from loguru import logger
from src.models.violation import Violation
from datetime import datetime, timezone



class ViolationProducer:
    """Kafka producer for publishing violation events"""

    def __init__(self, bootstrap_servers: str, topic: str = "guardrail.violations", enabled: bool = True):
        """
        Initialize the Kafka producer

        Args:
            bootstrap_servers: Kafka bootstrap servers (e.g., "localhost:9092")
            topic: Topic name to publish violations to
            enabled: Whether Kafka producer is enabled
        """
        self.enabled = enabled
        self.topic = topic
        self.send_count = 0
        self.error_count = 0

        if not self.enabled:
            logger.info("Kafka producer is disabled")
            return

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers.split(','),
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,  # Retry failed sends
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                compression_type='gzip',  # Compress messages
                enable_idempotence=True,  # Prevent duplicates
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info(f"Kafka producer initialized: {bootstrap_servers}, topic: {topic}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.enabled = False
            raise

    def send_violation(self, violation: Violation) -> bool:
        """
        Send violation to Kafka topic

        Args:
            violation: Violation object to send

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Convert violation to dict for serialization
            violation_dict = violation.to_dict()

            violation_dict["ingestion_timestamp"] = (
                datetime.now(timezone.utc).isoformat()
            )

            # Send to Kafka with conversation_id as key for partitioning
            future = self.producer.send(
                self.topic,
                key=violation.conversation_id.encode('utf-8'),
                value=violation_dict
            )

            # Add callbacks for async handling
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)

            self.send_count += 1
            return True

        except Exception as e:
            logger.error(f"Failed to send violation to Kafka: {e}")
            self.error_count += 1
            return False

    def _on_send_success(self, metadata):
        """Callback for successful send"""
        logger.debug(
            f"Violation sent to topic: {metadata.topic}, "
            f"partition: {metadata.partition}, offset: {metadata.offset}"
        )

    def _on_send_error(self, exception):
        """Callback for send errors"""
        logger.error(f"Failed to send violation: {exception}")
        self.error_count += 1

    def close(self):
        """Flush and close the producer"""
        if self.enabled and hasattr(self, 'producer'):
            try:
                logger.info(f"Flushing Kafka producer (sent: {self.send_count}, errors: {self.error_count})")
                self.producer.flush()
                self.producer.close()
                logger.info("Kafka producer closed successfully")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")

    def get_stats(self):
        """Get producer statistics"""
        return {
            'enabled': self.enabled,
            'sent': self.send_count,
            'errors': self.error_count
        }
