"""
Assessment Bot - Quiz Generation and Knowledge Testing
"""
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum

from .base import (
    AgentDependencies,
    UserContext,
    OWASPCategory,
    DifficultyLevel,
    ASSESSMENT_BOT_SYSTEM,
    get_llm_model
)


# =============================================================================
# OUTPUT MODELS
# =============================================================================

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SCENARIO = "scenario"
    FILL_BLANK = "fill_blank"


class QuizQuestion(BaseModel):
    """Individual quiz question"""
    id: str
    question_type: str = Field(description="Type: multiple_choice, true_false, scenario, or fill_blank")
    question: str
    owasp_category: str = Field(description="OWASP category (e.g., 'A01:2021 - Injection')")
    difficulty: str = Field(description="Difficulty: beginner, intermediate, or advanced")
    
    # For multiple choice
    options: List[str] = Field(default_factory=list)
    correct_answer: Union[str, int, bool]
    
    # Explanation
    explanation: str = Field(description="Why this answer is correct")
    wrong_answer_explanations: dict = Field(
        default_factory=dict,
        description="Explanations for why wrong answers are wrong"
    )
    
    # Metadata
    points: int = Field(default=10)
    time_limit_seconds: int = Field(default=60)
    hint: Optional[str] = None


class Quiz(BaseModel):
    """Complete quiz"""
    id: str
    title: str
    description: str
    owasp_categories: List[str] = Field(description="List of OWASP categories covered")
    difficulty: str = Field(description="Overall difficulty level")
    questions: List[QuizQuestion]
    
    total_points: int
    passing_score: int
    time_limit_minutes: int
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuizResult(BaseModel):
    """Quiz attempt result"""
    quiz_id: str
    user_id: int
    score: int
    max_score: int
    percentage: float
    passed: bool
    
    # Detailed breakdown
    correct_answers: int
    wrong_answers: int
    skipped: int
    
    # Analysis
    weak_areas: List[str] = Field(description="List of weak OWASP categories")
    strong_areas: List[str] = Field(description="List of strong OWASP categories")
    recommendations: List[str]
    
    time_taken_seconds: int
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class AnswerFeedback(BaseModel):
    """Feedback for a single answer"""
    is_correct: bool
    correct_answer: str
    explanation: str
    related_lesson: Optional[str] = None
    encouragement: str


class KnowledgeGap(BaseModel):
    """Identified knowledge gap"""
    owasp_category: OWASPCategory
    gap_description: str
    severity: str  # minor, moderate, significant
    recommended_lessons: List[str]
    practice_questions: int = Field(default=3)


# =============================================================================
# AGENT BUILDERS
# =============================================================================

def build_assessment_bot():
    """Create and configure the Assessment Bot Agent"""
    agent = Agent(
        model=get_llm_model(),
        system_prompt=ASSESSMENT_BOT_SYSTEM,
        deps_type=AgentDependencies,
        output_type=AnswerFeedback,
    )
    
    @agent.system_prompt
    async def add_assessment_context(ctx: RunContext[AgentDependencies]) -> str:
        """Add user learning context"""
        if ctx.deps.user:
            user = ctx.deps.user
            return f"""
            
Learner being assessed:
- Current Level: {user.current_level}/10
- Knowledge Score: {user.knowledge_score:.1f}%
- Completed Topics: {', '.join(user.completed_topics) or 'None'}

Adjust question difficulty and feedback accordingly.
Be encouraging but honest about areas needing improvement.
"""
        return ""

    @agent.tool
    async def evaluate_answer(
        ctx: RunContext[AgentDependencies],
        question: str,
        user_answer: str,
        correct_answer: str
    ) -> str:
        """Evaluate a user's answer"""
        return f"""
        Evaluate this answer:
        Question: {question}
        User's answer: {user_answer}
        Correct answer: {correct_answer}
        
        Provide constructive feedback. If wrong, explain why clearly.
        """

    @agent.tool
    async def identify_knowledge_gaps(
        ctx: RunContext[AgentDependencies],
        wrong_answers: List[str]
    ) -> str:
        """Identify patterns in wrong answers"""
        return f"""
        Analyze these incorrect answers to identify knowledge gaps:
        {wrong_answers}
        
        Look for patterns and recommend specific topics to review.
        """

    @agent.tool
    async def adjust_difficulty(
        ctx: RunContext[AgentDependencies],
        recent_performance: str
    ) -> str:
        """Adjust quiz difficulty based on performance"""
        return f"""
        Based on recent performance: {recent_performance}
        Recommend difficulty adjustment for next quiz.
        """
        
    return agent

def build_quiz_generator():
    """Create and configure the Quiz Generator Agent"""
    return Agent(
        model=get_llm_model(),
        system_prompt=ASSESSMENT_BOT_SYSTEM + """

    You are generating quiz questions. Requirements:
    - Scenario-based questions using realistic SMB situations
    - Clear, unambiguous correct answers
    - Plausible but clearly wrong distractors
    - Educational explanations for all answers
    - Mix of question types for engagement
    """,
        deps_type=AgentDependencies,
        output_type=Quiz,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def generate_quiz(
    owasp_categories: List[OWASPCategory],
    difficulty: DifficultyLevel,
    num_questions: int = 10,
    user: Optional[UserContext] = None
) -> Quiz:
    """Generate a complete quiz"""
    deps = AgentDependencies(
        user=user,
        session_id=f"quiz-gen-{datetime.utcnow().timestamp()}"
    )
    
    categories_str = ", ".join([c.value for c in owasp_categories])
    
    prompt = f"""
    Generate a quiz with {num_questions} questions covering:
    Categories: {categories_str}
    Difficulty: {difficulty.value}
    
    Include a mix of question types.
    Make scenarios relevant to European SMBs.
    """
    
    agent = build_quiz_generator()
    result = await agent.run(prompt, deps=deps)
    return result.output


async def evaluate_quiz_answer(
    question: QuizQuestion,
    user_answer: str,
    user: Optional[UserContext] = None
) -> AnswerFeedback:
    """Evaluate a single quiz answer"""
    deps = AgentDependencies(
        user=user,
        session_id=f"eval-{question.id}"
    )
    
    prompt = f"""
    Evaluate this quiz answer:
    
    Question: {question.question}
    Type: {question.question_type.value}
    Options: {question.options if question.options else 'N/A'}
    User's Answer: {user_answer}
    Correct Answer: {question.correct_answer}
    
    Provide feedback that's encouraging but educational.
    """
    
    agent = build_assessment_bot()
    result = await agent.run(prompt, deps=deps)
    return result.output


async def analyze_quiz_results(
    results: List[dict],
    user: UserContext
) -> List[KnowledgeGap]:
    """Analyze quiz results to identify knowledge gaps"""
    deps = AgentDependencies(user=user, session_id=f"analysis-{user.user_id}")
    
    wrong_answers = [r for r in results if not r.get('correct')]
    
    if not wrong_answers:
        return []
    
    prompt = f"""
    Analyze these incorrect answers and identify knowledge gaps:
    
    {wrong_answers}
    
    Group by OWASP category and recommend specific improvements.
    """
    
    # This would return structured knowledge gaps
    # Simplified for now
    agent = build_assessment_bot()
    result = await agent.run(prompt, deps=deps)
    
    return []


async def get_personalized_quiz(user: UserContext) -> Quiz:
    """Generate a quiz tailored to user's weak areas"""
    # Would analyze user history and focus on weak areas
    weak_categories = [OWASPCategory.INJECTION, OWASPCategory.XSS]  # Example
    
    return await generate_quiz(
        owasp_categories=weak_categories,
        difficulty=DifficultyLevel.BEGINNER if user.current_level < 4 else DifficultyLevel.INTERMEDIATE,
        num_questions=5,
        user=user
    )
