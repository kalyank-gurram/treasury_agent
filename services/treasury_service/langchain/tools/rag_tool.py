"""RAG and narrative tools for LangChain Treasury Agent."""

from typing import Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ...infrastructure.observability import trace_operation, monitor_performance, get_observability_manager


class RagInput(BaseModel):
    """Input for RAG document search."""
    query: str = Field(description="Search query for documents", default="")
    entity: str = Field(description="Entity context for search", default="")


class NarrativeInput(BaseModel):
    """Input for narrative generation."""
    entity: str = Field(description="Entity ID for narrative report", default="")
    report_type: str = Field(description="Type of narrative report", default="summary")


class RagTool(BaseTool):
    """Tool for RAG document retrieval in Treasury Agent."""
    
    name: str = "search_treasury_documents"
    description: str = "Search treasury documents and policies using RAG (Retrieval Augmented Generation). Use when users ask about policies, procedures, or document searches."
    args_schema: type[BaseModel] = RagInput
    
    @trace_operation("rag_search_langchain")
    @monitor_performance("rag_tool")
    def _run(self, query: str = "", entity: str = "") -> Dict[str, Any]:
        """Execute document search."""
        observability = get_observability_manager()
        logger = observability.get_logger("langchain.tools.rag")
        
        logger.info("Searching documents via LangChain tool", query=query[:50], entity=entity)
        
        try:
            # Simplified RAG search
            result = {
                "query": query,
                "documents": [
                    {"title": "Treasury Policy 001", "relevance": 0.85, "summary": "Cash management procedures"},
                    {"title": "Risk Management Guide", "relevance": 0.72, "summary": "Risk assessment frameworks"}
                ],
                "total_results": 2
            }
            
            logger.info("Document search completed", query=query[:50], results_count=len(result["documents"]))
            
            observability.record_metric(
                "counter", "rag_searches_total", 1,
                {"source": "langchain_tool", "status": "success"}
            )
            
            return {
                "success": True,
                "data": result,
                "query": query,
                "entity": entity
            }
            
        except Exception as e:
            logger.error("Document search failed", 
                        query=query[:50], entity=entity, error=str(e), error_type=type(e).__name__)
            
            observability.record_metric(
                "counter", "rag_searches_total", 1,
                {"source": "langchain_tool", "status": "failed"}
            )
            
            return {
                "success": False,
                "error": f"Failed to search documents: {str(e)}",
                "query": query
            }
    
    async def _arun(self, query: str = "", entity: str = "") -> Dict[str, Any]:
        """Async execution - delegate to sync for now."""
        return self._run(query, entity)


class NarrativeTool(BaseTool):
    """Tool for narrative report generation in Treasury Agent."""
    
    name: str = "generate_treasury_narrative"
    description: str = "Generate narrative reports and summaries of treasury activities. Use when users ask for reports, summaries, or comprehensive overviews."
    args_schema: type[BaseModel] = NarrativeInput
    
    @trace_operation("narrative_generation_langchain")
    @monitor_performance("narrative_tool")
    def _run(self, entity: str = "", report_type: str = "summary") -> Dict[str, Any]:
        """Execute narrative generation."""
        observability = get_observability_manager()
        logger = observability.get_logger("langchain.tools.narrative")
        
        logger.info("Generating narrative via LangChain tool", entity=entity, report_type=report_type)
        
        try:
            # Simplified narrative generation
            result = {
                "report_type": report_type,
                "entity": entity,
                "narrative": f"Treasury {report_type} report for {entity}",
                "sections": [
                    {"title": "Executive Summary", "content": "Overall treasury performance is stable"},
                    {"title": "Key Metrics", "content": "Cash position remains healthy"},
                    {"title": "Risk Assessment", "content": "Risk levels are within acceptable limits"}
                ],
                "generated_at": "2025-11-10T17:50:00Z"
            }
            
            logger.info("Narrative generation completed", entity=entity, report_type=report_type)
            
            observability.record_metric(
                "counter", "narrative_generations_total", 1,
                {"source": "langchain_tool", "type": report_type, "status": "success"}
            )
            
            return {
                "success": True,
                "data": result,
                "entity": entity,
                "report_type": report_type
            }
            
        except Exception as e:
            logger.error("Narrative generation failed", 
                        entity=entity, report_type=report_type, error=str(e), error_type=type(e).__name__)
            
            observability.record_metric(
                "counter", "narrative_generations_total", 1,
                {"source": "langchain_tool", "status": "failed"}
            )
            
            return {
                "success": False,
                "error": f"Failed to generate narrative: {str(e)}",
                "entity": entity
            }
    
    async def _arun(self, entity: str = "", report_type: str = "summary") -> Dict[str, Any]:
        """Async execution - delegate to sync for now."""
        return self._run(entity, report_type)