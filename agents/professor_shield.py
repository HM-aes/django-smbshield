"""
Professor Shield - AI Cybersecurity Tutor
Teaches OWASP Top 10 adapted for SMBs
"""
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from typing import List, Optional
from datetime import datetime

from .base import (
    AgentDependencies,
    UserContext,
    OWASPCategory,
    DifficultyLevel,
    PROFESSOR_SHIELD_SYSTEM,
    get_llm_model
)


# =============================================================================
# OUTPUT MODELS
# =============================================================================

class LessonContent(BaseModel):
    """Structured lesson content"""
    title: str
    owasp_category: str = Field(description="The OWASP Top 10 category (e.g., 'A01:2021 - Injection')")
    difficulty: DifficultyLevel
    estimated_minutes: int = Field(default=10, ge=5, le=60)
    
    # Content sections
    why_it_matters: str = Field(description="Business impact explanation")
    what_it_is: str = Field(description="Technical explanation adapted to level")
    real_world_example: str = Field(description="SMB-relevant example")
    how_to_protect: List[str] = Field(description="Actionable protection steps")
    
    # Engagement
    quick_check_question: str = Field(description="Single question to verify understanding")
    quick_check_answer: str
    key_takeaway: str = Field(description="One sentence to remember")
    
    # Metadata
    prerequisites: List[str] = Field(default_factory=list)
    next_lessons: List[str] = Field(default_factory=list)


class TutorResponse(BaseModel):
    """Response from Professor Shield during Q&A"""
    answer: str = Field(description="Clear, helpful answer")
    confidence: float = Field(ge=0, le=1, description="Confidence in answer")
    related_owasp: Optional[str] = Field(default=None, description="Related OWASP category if applicable")
    follow_up_suggestion: Optional[str] = Field(
        default=None,
        description="Suggested next question or topic"
    )
    code_example: Optional[str] = Field(
        default=None,
        description="Code snippet if relevant"
    )
    resources: List[str] = Field(
        default_factory=list,
        description="Links to learn more"
    )


class LearningPath(BaseModel):
    """Personalized learning path"""
    user_level: DifficultyLevel
    completed_topics: List[str]
    current_topic: str
    next_topics: List[str]
    estimated_completion_hours: float
    weak_areas: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    recommended_focus: str


# =============================================================================
# PROFESSOR SHIELD AGENT FACTORY
# =============================================================================

def get_professor_agent():
    """Create a Professor Shield agent with the current LLM configuration"""
    return Agent(
        model=get_llm_model(),
        system_prompt=PROFESSOR_SHIELD_SYSTEM,
        deps_type=AgentDependencies,
        output_type=TutorResponse,
    )

def get_lesson_agent():
    """Create a Lesson Generator agent with the current LLM configuration"""
    return Agent(
        model=get_llm_model(),
        system_prompt=PROFESSOR_SHIELD_SYSTEM + """

    You are now generating a structured lesson. Create comprehensive but digestible content.
    Keep explanations clear and avoid unnecessary jargon.
    Every example should be relatable to a small business context.
    """,
        deps_type=AgentDependencies,
        output_type=LessonContent,
    )


# =============================================================================
# AGENT BUILDER
# =============================================================================

def build_professor_agent():
    """Create and configure the Professor Shield agent"""
    agent = Agent(
        model=get_llm_model(),
        system_prompt=PROFESSOR_SHIELD_SYSTEM,
        deps_type=AgentDependencies,
        output_type=TutorResponse,
    )
    
    # Register dynamic system prompt
    @agent.system_prompt
    async def add_user_context(ctx: RunContext[AgentDependencies]) -> str:
        if ctx.deps.user:
            user = ctx.deps.user
            return f"""
            
Current learner profile:
- Name: {user.username}
- Company: {user.company_name or 'Not specified'}
- Industry: {user.industry or 'General'}
- Current Level: {user.current_level}/10
- Knowledge Score: {user.knowledge_score:.1f}%
- Completed Topics: {', '.join(user.completed_topics) or 'None yet'}

Adapt your teaching to this learner's level and context.
"""
        return ""

    # Register tools
    @agent.tool
    async def get_owasp_explanation(
        ctx: RunContext[AgentDependencies], 
        category: str,
        depth: str = "overview"
    ) -> str:
        """Get detailed explanation of an OWASP category"""
        return f"""
        Provide a {depth} explanation of {category} suitable for:
        - SMB context (small IT team, limited budget)
        - Current user level: {ctx.deps.user.current_level if ctx.deps.user else 1}
        - Practical, actionable information
        """

    @agent.tool
    async def generate_example_scenario(
        ctx: RunContext[AgentDependencies],
        owasp_category: str,
        industry: str = "general"
    ) -> str:
        """Generate a realistic attack scenario"""
        return f"""
        Create a realistic but educational scenario showing how {owasp_category} 
        could affect a small business in the {industry} sector.
        Include: attack vector, impact, and prevention steps.
        """

    @agent.tool
    async def suggest_next_topic(
        ctx: RunContext[AgentDependencies],
        current_topic: str,
        performance: str
    ) -> str:
        """Suggest the next topic based on performance"""
        return f"""
        Based on performance ({performance}) in {current_topic},
        suggest the optimal next learning topic.
        Consider prerequisites and logical progression.
        """

    @agent.tool
    async def search_knowledge_base(
        ctx: RunContext[AgentDependencies],
        query: str,
        category: str = "all"
    ) -> str:
        """
        Search the cybersecurity knowledge base for detailed information.

        Use this tool when you need to find specific technical details,
        best practices, or in-depth explanations from the knowledge base.

        Args:
            query: The search query (e.g., "SQL injection prevention techniques")
            category: Filter by category - "owasp", "general", "smb_specific", or "all"
        """
        try:
            from rag.services import rag_retriever

            filter_conditions = None
            if category and category != "all":
                filter_conditions = {"category": category}

            # Search the knowledge base
            results = await rag_retriever.search_async(
                question=query,
                filter_conditions=filter_conditions
            )

            if not results:
                return "No relevant information found in the knowledge base for this query."

            # Format results for the agent
            formatted_results = []
            for i, chunk in enumerate(results[:5], 1):
                source = chunk.get('source', 'Unknown')
                page = chunk.get('page')
                text = chunk.get('text', '')[:500]  # Limit text length

                source_info = f"Source: {source}"
                if page:
                    source_info += f", Page {page}"

                formatted_results.append(f"""
--- Knowledge Base Result {i} ---
{source_info}

{text}
""")

            return "\n".join(formatted_results)

        except ImportError:
            return "Knowledge base search is not available. RAG system not installed."
        except Exception as e:
            return f"Error searching knowledge base: {str(e)}"

    return agent

def build_lesson_agent():
    """Create and configure the Lesson Generator agent"""
    return Agent(
        model=get_llm_model(),
        system_prompt=PROFESSOR_SHIELD_SYSTEM + """

    You are now generating a structured lesson. Create comprehensive but digestible content.
    Keep explanations clear and avoid unnecessary jargon.
    Every example should be relatable to a small business context.
    """,
        deps_type=AgentDependencies,
        output_type=LessonContent,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def ask_professor(
    question: str, 
    user: Optional[UserContext] = None
) -> TutorResponse:
    """Ask Professor Shield a question"""
    deps = AgentDependencies(
        user=user,
        session_id=f"tutor-{user.user_id if user else 'guest'}"
    )
    agent = build_professor_agent()
    result = await agent.run(question, deps=deps)
    return result.output


async def generate_lesson(
    owasp_category: OWASPCategory,
    difficulty: DifficultyLevel,
    user: Optional[UserContext] = None
) -> LessonContent:
    """Generate a complete lesson"""
    deps = AgentDependencies(
        user=user,
        session_id=f"lesson-gen-{user.user_id if user else 'guest'}"
    )
    
    prompt = f"""
    Generate a complete lesson on: {owasp_category.value}
    Difficulty level: {difficulty.value}
    
    Make it practical, engaging, and relevant to European SMBs.
    """
    
    agent = build_lesson_agent()
    result = await agent.run(prompt, deps=deps)
    return result.output


async def get_learning_path(user: UserContext) -> LearningPath:
    """Generate personalized learning path"""
    deps = AgentDependencies(user=user, session_id=f"path-{user.user_id}")
    
    # This would query user progress and generate path
    # Simplified for now
    agent = build_professor_agent()
    result = await agent.run(
        "Generate a personalized learning path for this user",
        deps=deps
    )
    
    return LearningPath(
        user_level=DifficultyLevel.BEGINNER,
        completed_topics=user.completed_topics,
        current_topic="A01:2021 - Injection",
        next_topics=["A02:2021 - Broken Authentication", "A03:2021 - Sensitive Data"],
        estimated_completion_hours=8.5,
        recommended_focus="Start with the fundamentals"
    )
