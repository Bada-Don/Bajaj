from sentence_transformers import CrossEncoder
import google.generativeai as genai
from google.generativeai import types
import numpy as np
from typing import List, Tuple
import logging

import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, google_api_key: str, reranker_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"):
        self.reranker = CrossEncoder(reranker_model)
        genai.configure(api_key=google_api_key)
        # It's better to initialize the model once
        self.genai_model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def rerank_results(self, query: str, results: List[Tuple[str, float]], top_k: int = 5) -> List[str]:
        # ... (this function remains the same, it's CPU-bound) ...
        if not results:
            return []
        
        texts = [result[0] for result in results]
        reranker_inputs = [(query, text) for text in texts]
        
        scores = self.reranker.predict(reranker_inputs)
        
        scored_results = list(zip(texts, scores))
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [text for text, _ in scored_results[:top_k]]

    async def generate_answer_async(self, query: str, context_snippets: List[str]) -> str:
        """Generate answer asynchronously using Gemini API"""
        if not context_snippets:
            logger.warning(f"No context snippets provided for query: {query}")
            return "I apologize, but I couldn't find relevant information to answer this question."
        
        combined_context = "\n".join(context_snippets)
        prompt = f"""Answer based on the following query and retrieved relevant info:

Query: {query}

Relevant Info: {combined_context}

Please provide a concise and accurate answer based only on the provided information."""
        
        try:
            logger.info(f"Calling Gemini API asynchronously for query: {query[:30]}...")
            response = await self.genai_model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(max_output_tokens=150)
            )
            logger.info("Successfully received async response from Gemini API.")
            return response.text
        except Exception as e:
            logger.error(f"Async answer generation failed: {str(e)}")
            return "I apologize, but I couldn't generate an answer at this time."