"""
Planner node for intent classification and routing.

Determines whether a query should use RAG or direct answer path.
"""

from typing import Literal
from artemis.agent.state import AgentState
from artemis.agent.config import AgentConfig
from artemis.agent.llm.groq_client import GroqClient
from artemis.agent.llm.openai_client import OpenAIClient
from artemis.utils import get_logger

logger = get_logger(__name__)


def planner_node(state: AgentState, config: AgentConfig) -> AgentState:
    """
    Classify query intent and set confidence.
    
    Uses LLM to determine if query needs RAG (document retrieval) or
    can be answered directly. Sets intent and confidence in state.
    
    Args:
        state: Current agent state
        config: Agent configuration
        
    Returns:
        Updated state with intent and confidence set
    """
    query = state.get("query", "")
    
    if not query:
        logger.warning("Empty query in planner node")
        return {
            **state,
            "intent": "direct",
            "confidence": 0.0,
            "error": "Empty query"
        }
    
    logger.info(f"Planning for query: '{query[:50]}...'")
    
    # Initialize LLM client based on provider
    if config.provider == "groq":
        llm_client = GroqClient(
            api_key=config.groq_api_key,
            model_name=config.model_name
        )
    else:
        llm_client = OpenAIClient(
            api_key=config.openai_api_key,
            model_name=config.model_name
        )
    
    # System prompt for intent classification
    system_prompt = """You are an intent classifier for a RAG (Retrieval-Augmented Generation) system.

Your task is to determine if a user query requires document retrieval (RAG) or can be answered directly.

Use RAG (intent="rag") when:
- The query asks about specific documents, files, or content that was indexed
- The query references information that might be in the knowledge base
- The query asks "what does X say about Y" or "find information about X"
- The query needs factual information from documents

Use direct answer (intent="direct") when:
- The query is a general question that doesn't reference documents
- The query asks for explanations of concepts (not document-specific)
- The query is conversational or doesn't need retrieval

Respond with ONLY a JSON object in this exact format:
{"intent": "rag" or "direct", "confidence": 0.0-1.0, "reasoning": "brief explanation"}

Confidence should be:
- High (0.8-1.0) if you're very certain
- Medium (0.5-0.8) if somewhat certain
- Low (0.0-0.5) if uncertain
"""
    
    user_prompt = f"Classify this query: {query}"
    
    try:
        response = llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,  # Lower temperature for classification
            max_tokens=200
        )
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            # Fallback: try parsing entire response
            result = json.loads(response.strip())
        
        intent = result.get("intent", "rag").lower()
        confidence = float(result.get("confidence", 0.5))
        reasoning = result.get("reasoning", "")
        
        # Validate intent
        if intent not in ["rag", "direct"]:
            logger.warning(f"Invalid intent '{intent}', defaulting to 'rag'")
            intent = "rag"
        
        # Clamp confidence
        confidence = max(0.0, min(1.0, confidence))
        
        logger.info(f"Intent: {intent}, Confidence: {confidence:.2f}, Reasoning: {reasoning}")
        
        return {
            **state,
            "intent": intent,
            "confidence": confidence
        }
        
    except Exception as e:
        logger.exception(f"Error in planner node: {e}")
        # Default to RAG on error (safer fallback)
        return {
            **state,
            "intent": "rag",
            "confidence": 0.5,
            "error": f"Planner error: {str(e)}"
        }
