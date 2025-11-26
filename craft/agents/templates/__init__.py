"""Agent Templates package."""

from craft.agents.templates.base import TemplateAgent
from craft.agents.templates.customer_support import CustomerSupportAgent
from craft.agents.templates.code_review import CodeReviewAgent
from craft.agents.templates.data_analyst import DataAnalystAgent
from craft.agents.templates.research import ResearchAgent
from craft.agents.templates.content_writer import ContentWriterAgent

__all__ = [
    "TemplateAgent",
    "CustomerSupportAgent",
    "CodeReviewAgent",
    "DataAnalystAgent",
    "ResearchAgent",
    "ContentWriterAgent",
]
