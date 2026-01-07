"""
News Agent - Scrapes, summarizes, and categorizes cybersecurity news
"""
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from typing import List, Optional
from datetime import datetime
from enum import Enum

from .base import (
    AgentDependencies, 
    UrgencyLevel, 
    OWASPCategory,
    NEWS_AGENT_SYSTEM,
    get_llm_model
)


# =============================================================================
# OUTPUT MODELS
# =============================================================================

class NewsArticleSummary(BaseModel):
    """Structured summary of a news article"""
    title: str = Field(description="Concise, attention-grabbing title")
    summary: str = Field(description="2-3 sentence summary for SMB audience")
    urgency: str = Field(description="Urgency level: low, medium, high, or critical")
    owasp_categories: List[str] = Field(
        default_factory=list,
        description="Relevant OWASP categories (e.g., 'A01:2021 - Injection')"
    )
    action_required: bool = Field(
        default=False,
        description="Does this require immediate SMB action?"
    )
    action_items: List[str] = Field(
        default_factory=list,
        description="Specific actions SMBs should take"
    )
    affected_industries: List[str] = Field(
        default_factory=list,
        description="Industries most affected"
    )
    source_url: str = Field(default="", description="Original article URL")
    published_at: Optional[datetime] = None


class DailyNewsBriefing(BaseModel):
    """Daily news briefing for homepage alerts"""
    date: datetime = Field(default_factory=datetime.utcnow)
    top_story: NewsArticleSummary
    breaking_alerts: List[NewsArticleSummary] = Field(
        default_factory=list,
        description="Critical news requiring attention"
    )
    other_news: List[NewsArticleSummary] = Field(
        default_factory=list,
        description="Other relevant news"
    )
    threat_level: str = Field(
        default="low",
        description="Overall threat level for today: low, medium, high, or critical"
    )
    summary_headline: str = Field(
        description="One-line summary for homepage banner"
    )


class NewsAnalysisRequest(BaseModel):
    """Request to analyze news content"""
    raw_content: str
    source_url: str = ""
    source_name: str = ""


# =============================================================================
# NEWS AGENT
# =============================================================================

# =============================================================================
# AGENT BUILDERS
# =============================================================================

def build_news_agent():
    """Create and configure the News Agent"""
    agent = Agent(
        model=get_llm_model(),
        system_prompt=NEWS_AGENT_SYSTEM,
        deps_type=AgentDependencies,
        output_type=NewsArticleSummary,
    )
    
    @agent.tool
    async def assess_urgency(ctx: RunContext[AgentDependencies], content: str) -> str:
        """Assess the urgency level of a cybersecurity news item"""
        urgency_criteria = """
        CRITICAL: Active exploitation, zero-day, immediate action needed
        HIGH: Significant vulnerability, patch available, act within 24-48h
        MEDIUM: Notable threat, plan remediation within 1-2 weeks
        LOW: Informational, good to know, no immediate action
        """
        return f"Assess based on: {urgency_criteria}"

    @agent.tool
    async def identify_owasp_category(ctx: RunContext[AgentDependencies], threat_description: str) -> str:
        """Map a threat to OWASP Top 10 categories"""
        return "Map the threat to relevant OWASP Top 10 2021 categories"

    @agent.tool
    async def generate_smb_action_items(ctx: RunContext[AgentDependencies], threat: str, urgency: str) -> str:
        """Generate practical action items for SMBs"""
        return """
        Generate 2-4 specific, actionable items that a small business can implement.
        Consider: limited IT staff, budget constraints, need for simple solutions.
        """
        
    return agent

def build_briefing_agent():
    """Create and configure the Daily Briefing Agent"""
    return Agent(
        model=get_llm_model(),
        system_prompt=NEWS_AGENT_SYSTEM + """

    Additional context for daily briefings:
    - Prioritize news by impact to European SMBs
    - Create a compelling but accurate headline
    - Don't sensationalize but don't undersell real threats
    - Group related news items together
    """,
        deps_type=AgentDependencies,
        output_type=DailyNewsBriefing,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def analyze_article(content: str, source_url: str = "") -> NewsArticleSummary:
    """Analyze a single news article"""
    deps = AgentDependencies(session_id="news-scraper")
    agent = build_news_agent()
    result = await agent.run(
        f"Analyze this cybersecurity news article:\n\n{content}\n\nSource: {source_url}",
        deps=deps
    )
    return result.output


async def generate_daily_briefing(articles: List[NewsArticleSummary]) -> DailyNewsBriefing:
    """Generate daily briefing from analyzed articles"""
    deps = AgentDependencies(session_id="daily-briefing")
    
    articles_text = "\n\n".join([
        f"Title: {a.title}\nSummary: {a.summary}\nUrgency: {a.urgency}"
        for a in articles
    ])
    
    agent = build_briefing_agent()
    result = await agent.run(
        f"Create a daily briefing from these analyzed articles:\n\n{articles_text}",
        deps=deps
    )
    return result.output
