"""
SMBShield AI Agents Package

Three specialized agents:
1. News Agent - Scrapes and summarizes cybersecurity news
2. Professor Shield - AI tutor for OWASP Top 10
3. Assessment Bot - Quiz generation and knowledge testing
"""
from .base import (
    AgentDependencies,
    UserContext,
    UrgencyLevel,
    OWASPCategory,
    DifficultyLevel,
)

from .news_agent import (
    NewsArticleSummary,
    DailyNewsBriefing,
    analyze_article,
    generate_daily_briefing,
)

from .professor_shield import (
    LessonContent,
    TutorResponse,
    LearningPath,
    ask_professor,
    generate_lesson,
    get_learning_path,
)

from .assessment_bot import (
    Quiz,
    QuizQuestion,
    QuizResult,
    AnswerFeedback,
    KnowledgeGap,
    generate_quiz,
    evaluate_quiz_answer,
    get_personalized_quiz,
)

__all__ = [
    # Base
    'AgentDependencies',
    'UserContext',
    'UrgencyLevel',
    'OWASPCategory',
    'DifficultyLevel',
    
    # News Agent
    'NewsArticleSummary',
    'DailyNewsBriefing',
    'analyze_article',
    'generate_daily_briefing',
    
    # Professor Shield
    'LessonContent',
    'TutorResponse',
    'LearningPath',
    'ask_professor',
    'generate_lesson',
    'get_learning_path',
    
    # Assessment Bot
    'Quiz',
    'QuizQuestion',
    'QuizResult',
    'AnswerFeedback',
    'KnowledgeGap',
    'generate_quiz',
    'evaluate_quiz_answer',
    'get_personalized_quiz',
]
