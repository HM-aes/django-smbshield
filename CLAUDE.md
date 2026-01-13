# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SMBShield is a B2B SaaS cybersecurity education platform for European SMBs built with Django 5.1+ and Pydantic AI agents. The platform provides OWASP Top 10 training, AI-powered assessments, and curated cybersecurity news.

## Commands

### Development Server
```bash
python manage.py runserver
```

### Database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### News Scraping
```bash
python manage.py scrape_news                    # Basic scrape
python manage.py scrape_news --generate-briefing # With daily briefing
python manage.py scrape_news --limit 10         # Limit articles
```

### Testing & Code Quality
```bash
pytest                      # Run tests
pytest path/to/test.py     # Run single test file
pytest -k test_name        # Run specific test
black .                    # Format code
isort .                    # Sort imports
ruff check .               # Lint
```

## Architecture

### AI Agents (Pydantic AI)

The `agents/` module contains three AI agents built with Pydantic AI:

1. **Professor Shield** (`professor_shield.py`) - AI tutor for OWASP Top 10 education
   - `professor_shield` agent for Q&A responses (`TutorResponse`)
   - `lesson_generator` agent for structured lessons (`LessonContent`)
   - Uses dynamic system prompts that inject user context via `@agent.system_prompt` decorator

2. **Assessment Bot** (`assessment_bot.py`) - Quiz generation and evaluation
   - `assessment_bot` agent for answer feedback (`AnswerFeedback`)
   - `quiz_generator` agent for complete quizzes (`Quiz`)
   - Tracks knowledge gaps and adjusts difficulty

3. **News Agent** (`news_agent.py`) - Cybersecurity news analysis
   - `news_agent` for article analysis (`NewsArticleSummary`)
   - `briefing_agent` for daily briefings (`DailyNewsBriefing`)

All agents use shared configuration from `agents/base.py`:
- `AgentDependencies` - injected context with user info and session
- `UserContext` - user profile for personalization
- System prompts define agent behavior and SMB focus
- `get_llm_model()` returns configured model string based on `LLM_PROVIDER` env var

**Agent Factory Pattern**: Agents are created per-request via `build_*_agent()` functions (e.g., `build_professor_agent()`). This allows dynamic system prompts and fresh LLM configuration.

### LLM Provider Configuration

Set `LLM_PROVIDER` env var to switch providers:
- `groq` (default): Uses `llama-3.3-70b-versatile`
- `anthropic`: Uses `claude-sonnet-4-20250514`
- `gemini`: Uses `gemini-2.0-flash`
- `deepseek`: Uses `deepseek-chat` (OpenAI-compatible API)

Override model with `DEFAULT_LLM_MODEL` env var.

### Custom User Model

`core.models.User` extends `AbstractUser` with:
- Company profile (name, size, industry)
- Subscription tracking (Stripe integration, tiers: free/pro/enterprise)
- Learning progress (OWASP level, scores, streaks)
- Trial system (30-day trial, first 2 OWASP modules always free)

Key properties:
- `has_full_access` - True if user is pro subscriber OR in active trial
- `can_access_module(code)` - Checks if user can access specific OWASP module
- `trial_days_remaining` - Days left in trial period

Always use `settings.AUTH_USER_MODEL` when referencing the User model.

### URL Structure

- `/` - Core/public pages
- `/news/` - Cybersecurity news
- `/blog/` - Blog content
- `/dashboard/` - Members-only area
- `/learn/` - Education/lessons
- `/assess/` - Assessments/quizzes
- `/api/agents/` - AI agent endpoints (async views)

### Access Control (`core/mixins.py`)

Subscription-based access control for views:
- `SubscriptionRequiredMixin` - Requires `has_full_access` (trial or Pro), redirects to pricing
- `ModuleAccessMixin` - Checks `can_access_module(code)` for OWASP module access
- `@subscription_required` - Decorator for function-based views
- `@subscription_required_json` - Decorator for API views (returns JSON, works with async)

### Agent API Pattern

Agent views in `agents/views.py` are async class-based views with subscription checks:
```python
@method_decorator(csrf_exempt, name='dispatch')
class ProfessorShieldView(LoginRequiredMixin, View):
    async def post(self, request):
        if not request.user.has_full_access:
            return JsonResponse({'error': 'subscription_required'}, status=403)
        user_context = get_user_context(request.user)
        response = await ask_professor(question, user_context)
        return JsonResponse({...})
```

### Education Data Model

- `OWASPModule` - Top-level OWASP categories (A01-A10)
- `Lesson` - Individual lessons with JSON content structure
- `UserProgress` - Tracks completion, time spent, quick check results
- `ChatHistory` - Professor Shield conversation logs

Lesson content stored as JSON with keys: `why_it_matters`, `what_it_is`, `real_world_example`, `how_to_protect`, `quick_check_question`, `quick_check_answer`, `key_takeaway`

## Environment Variables

Required (at least one LLM provider key):
- `GROQ_API_KEY` - For Groq (default provider)
- `ANTHROPIC_API_KEY` - For Anthropic Claude
- `GOOGLE_API_KEY` - For Google Gemini
- `DEEPSEEK_API_KEY` - For DeepSeek
- `SECRET_KEY` - Django secret key

Optional:
- `LLM_PROVIDER` - Switch LLM provider (groq/anthropic/gemini/deepseek)
- `DEFAULT_LLM_MODEL` - Override default model for chosen provider
- `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` - Payments
- `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - PostgreSQL config

## Frontend Stack

- Tailwind CSS v4 with dark theme (background: `#0a0a0a`)
- GSAP for animations (classes: `fade-up`, `slide-left`, `scale-in`; use `data-delay` for staggered animations)
- HTMX for interactivity
- django-cotton for reusable template components
- Space Grotesk font for display/body, JetBrains Mono for code

Design colors:
- Shield Green: `#22c55e` (primary brand, success)
- Threat levels: Low (green), Medium (amber), High (orange), Critical (red)

## Additional Patterns

### Async Views
Agent API views use async class-based views. Use `async def post(self, request)` and `await` for agent calls.

### SiteSettings Singleton
`SiteSettings.get_settings()` returns site-wide configuration including feature flags for enabling/disabling agents (`news_agent_enabled`, `professor_shield_enabled`, `assessment_bot_enabled`).

### Testing
Uses pytest-django. Run `pytest` from project root.

### Templates
Templates use django-cotton components. Look for `<c-componentname>` syntax in templates. Component definitions are in `templates/cotton/` directory.
