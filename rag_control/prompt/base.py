"""
Copyright (c) 2026 RetrievalLabs Co. All rights reserved.
Licensed under the RetrievalLabs Business-Restricted License (RBRL) v1.0.
"""

from abc import ABC, abstractmethod

from rag_control.models.policy import Policy as PolicyModel
from rag_control.models.vector_store import VectorStoreRecord

ChatMessage = dict[str, str]


class PromptBuilder(ABC):
    @abstractmethod
    def build(
        self,
        query: str,
        retrieved_docs: list[VectorStoreRecord],
        policy: PolicyModel | None,
    ) -> list[ChatMessage]:
        """
        Build chat messages for LLM generation from query, retrieved docs, and policy context.
        """
        pass
