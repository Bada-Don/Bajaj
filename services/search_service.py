from sentence_transformers import CrossEncoder
import google.generativeai as genai
from google.generativeai import types
import numpy as np
from typing import List, Tuple
import logging
import asyncio
from config import Config  # Import Config to access the DEVICE setting

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, google_api_key: str, reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        # Initialize the CrossEncoder on the configured device (GPU or CPU)
        self.reranker = CrossEncoder(reranker_model, device=Config.DEVICE)
        
        genai.configure(api_key=google_api_key)
        # Initialize the generative model once for reuse
        self.genai_model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        logger.info(f"SearchService: Reranker model loaded onto '{Config.DEVICE}'")

    def rerank_results(self, query: str, results: List[Tuple[str, float]], top_k: int = 5) -> List[str]:
        """Rerank search results using cross-encoder. This is a CPU/GPU-bound task."""
        if not results:
            return []
        
        texts = [result[0] for result in results]
        reranker_inputs = [(query, text) for text in texts]
        
        # Get reranking scores. show_progress_bar=False keeps logs clean.
        scores = self.reranker.predict(reranker_inputs, show_progress_bar=False)
        
        # Sort by score and return the top_k texts
        scored_results = list(zip(texts, scores))
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [text for text, _ in scored_results[:top_k]]

    async def generate_answer_async(self, query: str, context_snippets: List[str]) -> str:
        """
        Generate a competition-optimized answer asynchronously using the Gemini API.
        """
        if not context_snippets:
            logger.warning(f"No context snippets provided for query: {query}")
            return "The answer to this question is not available in the provided information."
            
        # Use a clear separator for the model to distinguish between chunks
        combined_context = "\n---\n".join(context_snippets)
        
        # --- COMPETITION-GRADE PROMPT ---
        prompt = f"""You are a precise and methodical Q&A system for a competition.

**Your Task:**
Answer the user's 'Query' using *only* the information available in the 'Relevant Info' section.

**Rules:**
1.  **Strict Grounding:** Your entire answer must be derived from the 'Relevant Info'. Do not add outside information or make assumptions.
2.  **"Not Found" Condition:** If the answer to the 'Query' cannot be found in the 'Relevant Info', you MUST reply with the following exact phrase and nothing else: `The answer to this question is not available in the provided information.`
3.  **No Formatting:** Do not use any markdown like bold (`**`), italics (`*`), or lists. Respond in plain text only.
4.  **Completeness:** Formulate a complete, comprehensive answer. Do not leave sentences unfinished.

**Relevant Info:**
{combined_context}

**Query:**
{query}

**Answer:**
"""
        
        try:
            logger.info(f"Calling Gemini API with competition prompt for query: {query[:30]}...")
            response = await self.genai_model.generate_content_async(
                prompt,
                # --- UPDATED GENERATION CONFIG FOR ACCURACY ---
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,  # Increased to prevent truncated answers
                    temperature=0.0,      # Set for factual, deterministic responses
                )
            )
            
            logger.info(f"Successfully received async response from Gemini API for query: {query[:30]}...")
            
            # Ensure the response is not empty or blocked
            if not response.parts:
                logger.warning(f"Gemini returned an empty or blocked response for query: {query}")
                return "The answer to this question is not available in the provided information."

            # Return the clean text, stripping any potential leading/trailing whitespace
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Async answer generation failed for query '{query}': {str(e)}")
            # Return the required "not found" phrase on failure
            return "The answer to this question is not available in the provided information."