"""
RAG node that retrieves documents and synthesizes an answer.

Calls the Retriever to get relevant documents, then uses LLM to
synthesize a final answer with citations.
"""

from typing import List, Dict, Any
from artemis.agent.state import AgentState
from artemis.agent.config import AgentConfig
from artemis.rag.core.retriever import Retriever
from artemis.agent.llm.groq_client import GroqClient
from artemis.agent.llm.openai_client import OpenAIClient
from artemis.utils import get_logger

logger = get_logger(__name__)


def rag_node(
    state: AgentState,
    config: AgentConfig,
    retriever: Retriever
) -> AgentState:
    """
    Retrieve documents and synthesize answer using RAG.
    
    Args:
        state: Current agent state
        config: Agent configuration
        retriever: Retriever instance for document retrieval
        
    Returns:
        Updated state with retrieved_docs and final_answer
    """
    query = state.get("query", "")
    
    if not query:
        logger.warning("Empty query in RAG node")
        return {
            **state,
            "retrieved_docs": [],
            "final_answer": "I need a query to search for information.",
            "error": "Empty query"
        }
    
    logger.info(f"RAG node processing query: '{query[:50]}...'")
    
    # Step 1: Retrieve documents
    try:
        retrieved_docs = retriever.retrieve(query, k=config.retrieval_k)
        logger.info(f"Retrieved {len(retrieved_docs)} documents")
        
        if not retrieved_docs:
            logger.warning("No documents retrieved, falling back to direct answer")
            return {
                **state,
                "retrieved_docs": [],
                "final_answer": "I couldn't find any relevant information in the knowledge base to answer your query.",
            }
        
    except Exception as e:
        logger.exception(f"Error retrieving documents: {e}")
        return {
            **state,
            "retrieved_docs": [],
            "final_answer": f"I encountered an error while searching: {str(e)}",
            "error": f"Retrieval error: {str(e)}"
        }
    
    # Step 2: Format retrieved documents for LLM
    context_text = _format_documents(retrieved_docs)
    
    # Step 3: Initialize LLM client
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
    
    # Step 4: Synthesize answer with citations
    system_prompt = """You are a helpful assistant that answers questions using retrieved documents.

Your task is to synthesize a clear, accurate answer based on the provided context documents.

Guidelines:
- Use information from the provided documents to answer the query
- Cite sources using [1], [2], etc. when referencing specific documents
- If the documents don't contain enough information, say so clearly
- Be concise but complete
- If multiple documents provide conflicting information, mention this
"""
    
    user_prompt = f"""Query: {query}

Context Documents:
{context_text}

Please provide a comprehensive answer to the query based on the context documents above. Include citations [1], [2], etc. when referencing specific documents."""
    
    try:
        final_answer = llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        logger.info(f"Generated answer ({len(final_answer)} chars)")
        
        return {
            **state,
            "retrieved_docs": retrieved_docs,
            "final_answer": final_answer
        }
        
    except Exception as e:
        logger.exception(f"Error synthesizing answer: {e}")
        return {
            **state,
            "retrieved_docs": retrieved_docs,
            "final_answer": f"I retrieved {len(retrieved_docs)} documents but encountered an error while generating the answer: {str(e)}",
            "error": f"Synthesis error: {str(e)}"
        }


def _format_documents(docs: List[Dict[str, Any]]) -> str:
    """
    Format retrieved documents for LLM context.
    
    Args:
        docs: List of document dicts with 'text', 'score', 'metadata'
        
    Returns:
        Formatted string with numbered documents
    """
    formatted = []
    for i, doc in enumerate(docs, 1):
        text = doc.get("text", "")
        score = doc.get("score", 0.0)
        metadata = doc.get("metadata", {})
        
        # Build document entry
        entry = f"[{i}] (Score: {score:.4f})\n{text}"
        
        # Add metadata if available
        if metadata:
            metadata_str = ", ".join(f"{k}={v}" for k, v in metadata.items() if k != "text")
            if metadata_str:
                entry += f"\nMetadata: {metadata_str}"
        
        formatted.append(entry)
    
    return "\n\n".join(formatted)
