"""
Playwright scraper for KFUEIT website.
Runs via Celery Beat daily at 2am.
Scraped content → chunked → Pinecone integrated embedding → namespace: public or per-student
"""
import re

from django.conf import settings

from .pinecone_api import upsert_text_records
from .pinecone_utils import resolve_namespace


KFUEIT_URLS = [
    "https://kfueit.edu.pk/",
    "https://kfueit.edu.pk/academics/",
    "https://kfueit.edu.pk/admissions/",
    "https://kfueit.edu.pk/departments/",
    "https://kfueit.edu.pk/faculty/",
    "https://kfueit.edu.pk/sfsc/",
    "https://kfueit.edu.pk/examination/",
    "https://kfueit.edu.pk/fee-structure/",
    "https://kfueit.edu.pk/academic-calendar/",
    "https://kfueit.edu.pk/rules-regulations/",
]


def scrape_page(url: str) -> str:
    """Scrape a single page using Playwright with bot-detection bypass."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--headless=new"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = context.new_page()

        # Override navigator.webdriver to bypass bot detection
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            content = page.evaluate("""() => {
                const remove = document.querySelectorAll('script, style, nav, footer, header, .cookie-banner');
                remove.forEach(el => el.remove());
                return document.body.innerText;
            }""")
        except Exception as e:
            content = f"[Failed to scrape {url}: {str(e)}]"
        finally:
            browser.close()

    return content


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return [c for c in chunks if len(c.strip()) > 50]


def embed_and_upsert(chunks: list[str], source_url: str, namespace: str | None = None):
    """Upsert source text into an integrated-embedding Pinecone index."""
    if not chunks:
        return

    target_namespace = resolve_namespace(namespace=namespace, use_public_default=True)

    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        records = [
            {
                "id": f"{source_url}_{i + j}",
                settings.PINECONE_TEXT_FIELD: chunk,
                "source_url": source_url,
                "chunk_index": i + j,
            }
            for j, chunk in enumerate(batch)
        ]

        upsert_text_records(namespace=target_namespace, records=records)


def scrape_and_index_all(roll_no: str | None = None, namespace: str | None = None):
    """Full pipeline: scrape all KFUEIT pages → chunk → embed → Pinecone."""
    target_namespace = resolve_namespace(
        roll_no=roll_no,
        namespace=namespace,
        use_public_default=True,
    )
    for url in KFUEIT_URLS:
        print(f"Scraping: {url}")
        content = scrape_page(url)
        chunks = chunk_text(content)
        embed_and_upsert(chunks, source_url=url, namespace=target_namespace)
        print(f"  Indexed {len(chunks)} chunks from {url} into namespace: {target_namespace}")
