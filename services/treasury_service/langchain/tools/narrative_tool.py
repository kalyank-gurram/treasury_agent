"""Narrative tool for LangChain Treasury Agent - separate file for clean imports."""

from .rag_tool import NarrativeTool

# Re-export for backward compatibility
__all__ = ['NarrativeTool']