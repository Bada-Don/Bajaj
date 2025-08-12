from sentence_transformers import CrossEncoder
import google.generativeai as genai
from google.generativeai import types
import numpy as np
from typing import List, Tuple
import logging
import asyncio
from config import Config  # Import Config to access the DEVICE setting
import re

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
    
    def clean_text(self, text: str) -> str:
        """
        A more comprehensive function to remove common markdown symbols and artifacts.
        """
        # Remove headings (e.g., #, ##, ###)
        text = re.sub(r'#+\s*', '', text)
        
        # Remove quotes
        text = text.replace('"', '')
        text = text.replace("'", "")

        # Remove bold and italics
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'__(.*?)__', r'\1', text)  # __bold__
        text = re.sub(r'\*(.*?)\*', r'\1', text)    # *italic*
        text = re.sub(r'_(.*?)_', r'\1', text)    # _italic_
        
        # Remove strikethrough
        text = re.sub(r'~~(.*?)~~', r'\1', text)
        
        # Remove inline code backticks
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Remove list markers (*, -, +, 1., 2.)
        text = re.sub(r'^\s*[\*\-\+]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)
        
        # Remove blockquotes
        text = re.sub(r'^\s*>\s*', '', text, flags=re.MULTILINE)
        
        # Remove horizontal rules
        text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        # Handle simple tables by replacing pipes with spaces
        text = text.replace('|', ' ')
        
        # Replace newlines and multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

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
        prompt = f"""You are a legal expert assistant. Your task is to answer the user's query by synthesizing information *only* from the provided "Relevant Info". You must follow the example pattern.

## Example ##
Query: What is the purpose of Article 17?
Relevant Info: "Article 17. Abolition of Untouchability.—Untouchability” is abolished and its practice in any form is forbidden. The enforcement of any disability arising out of “Untouchability” shall be an offence punishable in accordance with law."
Answer: Article 17 is significant because it abolishes the practice of Untouchability, making its enforcement a punishable offense under the law.

## Your Task ##

**Query:**
{query}

**Relevant Info:**
{combined_context}
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
            raw_answer = response.text
            cleaned_answer = self.clean_text(raw_answer)
            logger.info(f"Cleaned Answer: {cleaned_answer}")
            return cleaned_answer
            
        except Exception as e:
            logger.error(f"Async answer generation failed for query '{query}': {str(e)}")
            # Return the required "not found" phrase on failure
            return "The answer to this question is not available in the provided information."