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
        if not context_snippets:
            logger.warning(f"No context snippets provided for query: {query}")
            return "I apologize, but I couldn't find relevant information to answer this question."
            
        combined_context = "\n".join(context_snippets)
        logger.info(f"Processing query: {query}")
        logger.info(f"Context length: {len(combined_context)} characters")
        logger.debug(f"Context snippets: {context_snippets}")
        
        prompt = f"""Answer based on the following query and retrieved relevant info:

Query: {query}

Relevant Info: {combined_context}

Please provide a concise and accurate answer based only on the provided information."""
        
        try:
            logger.info("Calling Gemini API...")
            # Get the model
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            # Generate response using generate_content
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=150,
                )
            )
            
            logger.info("Successfully received response from Gemini API")
            return response.text
            
        except Exception as e:
            logger.error(f"Answer generation failed: {str(e)}")
            logger.exception("Full exception details:")
            return "I apologize, but I couldn't generate an answer at this time."