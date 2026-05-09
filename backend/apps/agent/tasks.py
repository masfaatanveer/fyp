from celery import shared_task


@shared_task
def scrape_kfueit_website():
    """Celery Beat task — runs daily at 2am to re-scrape KFUEIT website."""
    from .services.scraper import scrape_and_index_all
    scrape_and_index_all()
