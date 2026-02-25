"""
Direct answer node for queries that don't need RAG.

Answers queries directly without document retrieval.
"""

from artemis.agent.state import AgentState
from artemis.agent.config import AgentConfig
from artemis.agent.llm.groq_client import GroqClient
from artemis.agent.llm.openai_client import OpenAIClient
from artemis.utils import get_logger

logger = get_logger(__name__)


def direct_answer_node(state: AgentState, config: AgentConfig) -> AgentState:
    """
    Generate direct answer without RAG.
    
    Args:
        state: Current agent state
        config: Agent configuration
        
    Returns:
        Updated state with final_answer
    """
    query = state.get("query", "")
    
    if not query:
        logger.warning("Empty query in direct answer node")
        return {
            **state,
            "final_answer": "I need a query to provide an answer.",
            "error": "Empty query"
        }
    
    logger.info(f"Direct answer node processing query: '{query[:50]}...'")
    
    # Initialize LLM client
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
    
    system_prompt = """You are a helpful AI assistant. Answer questions clearly and concisely.

If you don't know something or need more context, say so honestly.
Be helpful, accurate, and friendly."""
    
    user_prompt = query
    
    try:
        final_answer = llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        logger.info(f"Generated direct answer ({len(final_answer)} chars)")
        
        return {
            **state,
            "final_answer": final_answer,
            "retrieved_docs": []  # No docs for direct answers
        }
        
    except Exception as e:
        logger.exception(f"Error generating direct answer: {e}")
        return {
            **state,
            "final_answer": f"I encountered an error while generating an answer: {str(e)}",
            "error": f"Direct answer error: {str(e)}"
        }
