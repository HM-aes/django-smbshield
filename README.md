# 🛡️ SMBShield

**AI-Powered Cybersecurity Education Platform for European SMBs**

> Learn cybersecurity. Get tested. Stay current. — €99/month

![Django](https://img.shields.io/badge/Django-5.1+-green.svg)
![Pydantic AI](https://img.shields.io/badge/Pydantic_AI-0.0.14+-blue.svg)
![Tailwind](https://img.shields.io/badge/Tailwind-v4-cyan.svg)
![GSAP](https://img.shields.io/badge/GSAP-3.12-purple.svg)

---

## 🎯 What is SMBShield?

SMBShield is a B2B SaaS platform that makes cybersecurity education accessible for small and medium businesses in Europe. Using AI-powered agents, we deliver:

- **Personalized OWASP Top 10 training** adapted to each learner's level
- **AI-generated quizzes** that identify knowledge gaps
- **Daily threat intelligence** curated for SMB relevance
- **Expert blog content** on AI/LLM security trends

---

## 🤖 AI Agents

### 1. Professor Shield (Teaching)
Your AI cybersecurity tutor. Explains OWASP Top 10, answers questions, and adapts to your learning level.

### 2. Assessment Bot (Testing)
Generates scenario-based quizzes, scores responses, tracks knowledge gaps, and recommends focus areas.

### 3. News Agent (Intel)
Scrapes cybersecurity news daily, summarizes for SMB relevance, tags urgency levels, and powers homepage alerts.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Django 5.1+ (Django 6.0 ready) |
| **AI Framework** | Pydantic AI + Anthropic Claude |
| **Frontend** | Tailwind CSS v4 + GSAP animations |
| **Components** | django-cotton (reusable templates) |
| **Interactivity** | HTMX (no React needed!) |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Payments** | Stripe (€99/month subscriptions) |

---

## 🚀 Quick Start

### 1. Clone & Setup Environment

```bash
cd smbshield
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required keys:
- `ANTHROPIC_API_KEY` - For AI agents
- `STRIPE_*` - For payments (optional for dev)

### 3. Initialize Database

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

## 📁 Project Structure

```
smbshield/
├── smbshield/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/               # Homepage, auth, user model
├── agents/             # Pydantic AI agents
│   ├── base.py         # Shared config & prompts
│   ├── news_agent.py   # News scraping & analysis
│   ├── professor_shield.py  # AI tutor
│   └── assessment_bot.py    # Quiz generation
├── news/               # News articles & briefings
├── blog/               # Blog posts & categories
├── education/          # OWASP lessons & progress
├── assessment/         # Quizzes & results
├── dashboard/          # Members-only dashboard
├── templates/          # Django templates
│   ├── base.html       # Master template (Tailwind + GSAP)
│   └── pages/          # Page templates
├── static/             # CSS, JS, images
├── requirements.txt
└── manage.py
```

---

## 🎨 Design System

### Colors
- **Shield Green** (`#22c55e`) - Primary brand, success
- **Threat Colors**: Low (green), Medium (amber), High (orange), Critical (red)
- **Background**: Dark (`#0a0a0a`) with gradient mesh

### Typography
- **Display**: Space Grotesk (headings)
- **Body**: Space Grotesk (content)
- **Mono**: JetBrains Mono (code)

### Animation Classes
```html
<div class="fade-up">Animates up on scroll</div>
<div class="fade-up" data-delay="0.2">With delay</div>
<div class="slide-left">Slides from left</div>
<div class="scale-in">Scales in</div>
```

---

## 🔧 Management Commands

### Scrape News
```bash
# Basic scrape
python manage.py scrape_news

# With daily briefing generation
python manage.py scrape_news --generate-briefing

# Limit articles
python manage.py scrape_news --limit 10
```

### Seed OWASP Modules
```bash
python manage.py seed_owasp  # Create this command to populate modules
```

---

## 📡 API Endpoints

### Agent APIs (requires auth)
```
POST /api/agents/professor/ask/     # Ask Professor Shield
POST /api/agents/professor/lesson/  # Generate lesson
POST /api/agents/assessment/quiz/   # Generate quiz
POST /api/agents/news/analyze/      # Analyze news article
```

### Example Request
```javascript
fetch('/api/agents/professor/ask/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: 'What is SQL injection?' })
})
```

---

## 💰 Business Model

| Tier | Price | Features |
|------|-------|----------|
| **Free Trial** | €0 (14 days) | Full access, no CC required |
| **Professional** | €99/month | Unlimited users, full platform |
| **Enterprise** | Custom | SSO, dedicated support |

---

## 🛣️ Roadmap

### Phase 1 (Current)
- [x] Core Django structure
- [x] AI agent framework
- [x] Homepage & dashboard templates
- [x] News scraper command

### Phase 2
- [ ] Complete all page templates
- [ ] Stripe integration
- [ ] User onboarding flow
- [ ] Email notifications

### Phase 3
- [ ] Team management
- [ ] Progress reports (PDF export)
- [ ] API for enterprise integrations
- [ ] Mobile app (Django REST + React Native)

---

## 🧪 Development

### Run Tests
```bash
pytest
```

### Code Style
```bash
# Format
black .
isort .

# Lint
ruff check .
```

---

## 📚 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Pydantic AI Docs](https://ai.pydantic.dev/)
- [GSAP Animation](https://greensock.com/gsap/)
- [OWASP Top 10](https://owasp.org/Top10/)
- [Tailwind CSS](https://tailwindcss.com/)

---

## 👨‍💻 Author

**HiTek** - AI Engineer & Full-Stack Developer

Building the future of cybersecurity education for European SMBs.

---

## 📄 License

MIT License - See LICENSE file

---

*"New Year, New Career — El Senior AI Engineer is coming!"* 🚀
