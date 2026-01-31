import pandas as pd
from typing import Iterator
from src.models.conversation import Conversation
from loguru import logger

class DatasetLoader:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path

    def load_conversations(self) -> Iterator[Conversation]:
        """Load conversations from CSV file"""
        logger.info(f"Loading dataset from {self.dataset_path}")

        df = pd.read_csv(self.dataset_path)

        for _, row in df.iterrows():
            try:
                yield Conversation.from_dict(row.to_dict())
            except Exception as e:
                logger.warning(f"Skipping malformed row: {e}")
                continue
