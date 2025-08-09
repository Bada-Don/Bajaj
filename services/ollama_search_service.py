import numpy
import ollama
import logging
import asyncio
import os
from config import Config
from typing import List, Tuple
from sentence_transformers import CrossEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", llm_model_name: str = "granite3.1-moe:3b"):
        self.reranker = CrossEncoder(reranker_model, device=Config.DEVICE)
        self.llm_model_name = llm_model_name
        self.ollama_client = ollama.AsyncClient()

        logger.info(f"SearchService: Reranker model '{reranker_model}' loaded onto '{Config.DEVICE}'")
        logger.info(f"SearchService: Using LLM '{self.llm_model_name}' via Ollama async client")

    def rerank_results(self, query: str, results: List[Tuple[str, float]], top_k: int = 5) -> List[str]:
        if not results:
            return []

        texts = [result[0] for result in results]
        reranker_inputs = [(query, text) for text in texts]

        scores = self.reranker.predict(reranker_inputs, show_progress_bar=False)

        scored_results = list(zip(texts, scores))
        scored_results.sort(key=lambda x: x[1], reverse=True)

        return [text for text, _ in scored_results[:top_k]]

    async def generate_answer_async(self, query: str, context_snippets: List[str]) -> str:
        if not context_snippets:
            logger.warning(f"No context snippets provided for query: {query}")
            return "The answer to this question is not available in the provided information."

        instructions_path = os.path.join(os.path.dirname(__file__), "instructions.txt")
        instructions = open(instructions_path, "r").read()
        combined_context = "\n---\n".join(context_snippets)

        prompt = instructions + "\n\n" + "Relevant Info:" + "\n" + combined_context + "\n\n" + "Query:" + "\n" + query

        try:
            logger.info(f"Calling Ollama async API with model '{self.llm_model_name}' for query: {query[:30]}...")
            response = await self.ollama_client.generate(
                model=self.llm_model_name,
                prompt=prompt,
                options={
                    'num_predict': 512,
                    'temperature': 0.0,
                }
            )

            logger.info(f"Successfully received async response from Ollama for query: {query[:30]}...")

            if response and 'response' in response:
                return response['response'].strip()
            else:
                logger.warning(f"Ollama returned an unexpected response format for query: {query}")
                return "The answer to this question is not available in the provided information."

        except Exception as e:
            logger.error(f"Async answer generation with Ollama failed for query '{query}': {str(e)}")
            return "The answer to this question is not available in the provided information."
