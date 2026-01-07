"""
SMBShield AI Agents - Base Configuration
Using Pydantic AI for type-safe, structured agent responses
"""
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from typing import Optional, List
from enum import Enum
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)


# =============================================================================
# SHARED MODELS & TYPES
# =============================================================================

class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OWASPCategory(str, Enum):
    INJECTION = "A01:2021 - Injection"
    BROKEN_AUTH = "A02:2021 - Broken Authentication"
    SENSITIVE_DATA = "A03:2021 - Sensitive Data Exposure"
    XXE = "A04:2021 - XML External Entities"
    BROKEN_ACCESS = "A05:2021 - Broken Access Control"
    MISCONFIG = "A06:2021 - Security Misconfiguration"
    XSS = "A07:2021 - Cross-Site Scripting"
    INSECURE_DESERIAL = "A08:2021 - Insecure Deserialization"
    VULN_COMPONENTS = "A09:2021 - Using Components with Known Vulnerabilities"
    LOGGING = "A10:2021 - Insufficient Logging & Monitoring"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# =============================================================================
# AGENT DEPENDENCIES (injected context)
# =============================================================================

class UserContext(BaseModel):
    """User context passed to agents"""
    user_id: int
    username: str
    company_name: str = ""
    industry: str = ""
    current_level: int = 1
    knowledge_score: float = 0.0
    completed_topics: List[str] = Field(default_factory=list)


class AgentDependencies(BaseModel):
    """Dependencies injected into all agents"""
    user: Optional[UserContext] = None
    session_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# LLM MODEL CONFIGURATION
# =============================================================================

# Supported LLM providers
LLM_PROVIDERS = {
    'groq': 'groq',
    'anthropic': 'anthropic',
    'gemini': 'google-gla',
    'deepseek': 'openai',  # DeepSeek uses OpenAI-compatible API
}

def get_llm_model():
    """Get configured LLM model

    Supports multiple providers:
    - Groq: Set GROQ_API_KEY env var (fast inference)
    - Anthropic Claude: Set ANTHROPIC_API_KEY env var
    - Google Gemini: Set GOOGLE_API_KEY env var
    - DeepSeek: Set DEEPSEEK_API_KEY env var

    Set LLM_PROVIDER env var to switch between providers.
    """
    # Ensure environment variables are reloaded from .env if it changed
    # Use explicit path to avoid AssertionError in find_dotenv()
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    
    provider = os.getenv('LLM_PROVIDER', 'groq').lower()
    model_name = os.getenv('DEFAULT_LLM_MODEL', '')

    if provider == 'groq':
        # Groq models: llama-3.3-70b-versatile, llama-3.1-8b-instant
        if not model_name:
            model_name = 'llama-3.3-70b-versatile'
        return f"groq:{model_name}"

    elif provider == 'anthropic':
        # Anthropic Claude models
        if not model_name:
            model_name = 'claude-sonnet-4-20250514'
        return f"anthropic:{model_name}"

    elif provider == 'deepseek':
        # DeepSeek uses OpenAI-compatible API
        if not model_name:
            model_name = 'deepseek-chat'
        return f"openai:{model_name}"

    elif provider == 'gemini':
        # Google Gemini models
        if not model_name:
            model_name = 'gemini-2.0-flash'
        return f"google-gla:{model_name}"

    else:
        # Fallback to Groq
        if not model_name:
            model_name = 'llama-3.3-70b-versatile'
        return f"groq:{model_name}"


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

NEWS_AGENT_SYSTEM = """You are the SMBShield News Agent, a cybersecurity news analyst focused on European SMBs.

Your responsibilities:
1. Analyze cybersecurity news articles and extract key information
2. Assess urgency and relevance for small-medium businesses
3. Provide clear, actionable summaries in plain language
4. Tag relevant OWASP categories when applicable
5. Identify if immediate action is required

Always consider:
- Impact on businesses with 10-200 employees
- European regulatory context (GDPR, NIS2)
- Practical, cost-effective recommendations
- Avoid unnecessary alarmism but don't downplay real threats

Output in structured format for easy dashboard display."""


PROFESSOR_SHIELD_SYSTEM = """You are Professor Shield, the AI cybersecurity tutor for SMBShield.

Your teaching philosophy:
1. Adapt explanations to the learner's current level
2. Use real-world SMB examples, not abstract theory
3. Connect concepts to OWASP Top 10 framework
4. Encourage questions and provide step-by-step guidance
5. Celebrate progress and maintain encouraging tone

Teaching style:
- Start with "why it matters" before "how it works"
- Use analogies from everyday business operations
- Provide actionable takeaways after each lesson
- Include quick knowledge checks

Your goal: Transform cybersecurity from scary jargon into practical business knowledge."""


ASSESSMENT_BOT_SYSTEM = """You are the SMBShield Assessment Bot, responsible for testing and tracking cybersecurity knowledge.

Your responsibilities:
1. Generate quizzes tailored to user's current level
2. Test understanding of OWASP Top 10 concepts
3. Identify knowledge gaps and recommend topics to review
4. Provide detailed explanations for wrong answers
5. Track progress and adjust difficulty dynamically

Quiz design principles:
- Scenario-based questions using realistic SMB situations
- Mix of multiple choice, true/false, and short answer
- Include "what would you do" practical questions
- Test recognition of threats AND appropriate responses

Always be encouraging but honest about areas needing improvement."""
