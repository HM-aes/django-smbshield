"""
News Scraper Management Command
Run with: python manage.py scrape_news
Schedule with cron for daily updates
"""
import asyncio
import feedparser
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from news.models import NewsSource, NewsArticle, DailyBriefing
from agents import analyze_article, generate_daily_briefing, NewsArticleSummary


class Command(BaseCommand):
    help = 'Scrape and analyze cybersecurity news from configured sources'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--sources',
            nargs='+',
            help='Specific source names to scrape'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Maximum articles to process'
        )
        parser.add_argument(
            '--generate-briefing',
            action='store_true',
            help='Generate daily briefing after scraping'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting news scrape...'))
        
        # Run async scraper
        asyncio.run(self.scrape_news(
            sources=options.get('sources'),
            limit=options['limit'],
            generate_briefing=options['generate_briefing']
        ))
        
        self.stdout.write(self.style.SUCCESS('News scrape complete!'))
    
    async def scrape_news(self, sources=None, limit=20, generate_briefing=False):
        """Main scraping logic"""
        
        # Get active sources
        queryset = NewsSource.objects.filter(is_active=True)
        if sources:
            queryset = queryset.filter(name__in=sources)
        
        news_sources = list(queryset)
        
        if not news_sources:
            # Use default sources from settings
            for url in settings.NEWS_SOURCES:
                source, _ = NewsSource.objects.get_or_create(
                    url=url,
                    defaults={'name': url.split('/')[2], 'feed_type': 'rss'}
                )
                news_sources.append(source)
        
        articles_analyzed = []
        
        for source in news_sources:
            self.stdout.write(f'Scraping: {source.name}')
            
            try:
                if source.feed_type == 'rss':
                    articles = await self.scrape_rss(source, limit // len(news_sources))
                    articles_analyzed.extend(articles)
                    
                    # Update last fetched
                    source.last_fetched = timezone.now()
                    source.save()
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error scraping {source.name}: {e}'))
        
        self.stdout.write(f'Analyzed {len(articles_analyzed)} articles')
        
        # Generate daily briefing
        if generate_briefing and articles_analyzed:
            await self.create_daily_briefing(articles_analyzed)
    
    async def scrape_rss(self, source, limit):
        """Scrape RSS feed"""
        feed = feedparser.parse(source.url)
        analyzed = []
        
        for entry in feed.entries[:limit]:
            # Check if already exists
            if NewsArticle.objects.filter(original_url=entry.link).exists():
                continue
            
            # Extract content
            content = entry.get('summary', '') or entry.get('description', '')
            title = entry.get('title', 'Untitled')
            
            # Skip if too short
            if len(content) < 100:
                continue
            
            try:
                # Analyze with AI
                self.stdout.write(f'  Analyzing: {title[:50]}...')
                summary = await analyze_article(content, entry.link)
                
                # Parse published date
                published = entry.get('published_parsed')
                if published:
                    published_at = datetime(*published[:6], tzinfo=timezone.utc)
                else:
                    published_at = timezone.now()
                
                # Save to database
                article = NewsArticle.objects.create(
                    source=source,
                    original_url=entry.link,
                    original_title=title,
                    original_content=content,
                    title=summary.title,
                    summary=summary.summary,
                    urgency=summary.urgency.value,
                    owasp_categories=[c.value for c in summary.owasp_categories],
                    affected_industries=summary.affected_industries,
                    action_required=summary.action_required,
                    action_items=summary.action_items,
                    published_at=published_at,
                    is_breaking=summary.urgency.value == 'critical',
                )
                
                analyzed.append(summary)
                self.stdout.write(self.style.SUCCESS(f'    ✓ Saved: {summary.urgency.value}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ✗ Error: {e}'))
        
        return analyzed
    
    async def create_daily_briefing(self, articles):
        """Create daily briefing from analyzed articles"""
        self.stdout.write('Generating daily briefing...')
        
        try:
            briefing = await generate_daily_briefing(articles)
            
            # Get today's date
            today = timezone.now().date()
            
            # Create or update briefing
            db_briefing, created = DailyBriefing.objects.update_or_create(
                date=today,
                defaults={
                    'headline': briefing.summary_headline,
                    'summary': f"Top story: {briefing.top_story.title}. {len(briefing.breaking_alerts)} breaking alerts today.",
                    'threat_level': briefing.threat_level.value,
                }
            )
            
            self.stdout.write(self.style.SUCCESS(f'Daily briefing {"created" if created else "updated"}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Briefing error: {e}'))
