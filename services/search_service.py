from sentence_transformers import CrossEncoder
import google.generativeai as genai
from google.generativeai import types
import numpy as np
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, google_api_key: str, reranker_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"):
        self.reranker = CrossEncoder(reranker_model)
        genai.configure(api_key=google_api_key)
    
    def rerank_results(self, query: str, results: List[Tuple[str, float]], top_k: int = 5) -> List[str]:
        """Rerank search results using cross-encoder"""
        if not results:
            return []
        
        # Prepare inputs for reranking
        texts = [result[0] for result in results]
        reranker_inputs = [(query, text) for text in texts]
        
        # Get reranking scores
        scores = self.reranker.predict(reranker_inputs)
        
        # Sort by score and return top_k
        scored_results = list(zip(texts, scores))
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [text for text, _ in scored_results[:top_k]]
    
    def generate_answer(self, query: str, context_snippets: List[str]) -> str:
        """Generate answer using Gemini API"""
        combined_context = "\n".join(context_snippets)
        prompt = f"""Answer based on the following query and retrieved relevant info:

Query: {query}

Relevant Info: {combined_context}

Please provide a concise and accurate answer based only on the provided information."""
        try:
            response = genai.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                generation_config=types.GenerationConfig(
                    max_output_tokens=150,
                    temperature=0.1
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return "I apologize, but I couldn't generate an answer at this time."