import asyncio
import logging
import os
import signal
import sys
from dotenv import load_dotenv
from apscheduler.triggers.interval import IntervalTrigger

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "logs/app.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import application components
from app.database.database import create_db_and_tables, SessionLocal
from app.intelligence.ollama_client import OllamaClient
from app.notification.telegram_bot import TelegramNotifier
from app.orchestrator.scheduler import scheduler
from app.scrapers.subito import SubitoScraper
# from app.scrapers.vinted import VintedScraper
# from app.scrapers.ebay import EbayScraper

async def initialize_services():
    """Initialize database and other services."""
    logger.info("Initializing database...")
    create_db_and_tables()
    logger.info("Database initialized.")

    # Test Ollama connection
    try:
        ollama = OllamaClient()
        # We'll just instantiate; actual usage will happen in scrapers
        logger.info("Ollama client initialized.")
    except Exception as e:
        logger.error(f"Could not initialize Ollama client: {e}")
        # Continue without AI if needed

    # Test Telegram notifier
    notifier = TelegramNotifier()
    if notifier.bot is not None:
        logger.info("Telegram notifier initialized.")
        # Send a startup message
        await notifier.send_message("🤖 Avvio del bot di monitoraggio mercatini dell'usato.")
    else:
        logger.warning("Telegram notifier not configured.")

async def run_scraper_for_term(scraper, term: str):
    """Run a single scraper for a given search term and save results."""
    logger.info(f"Running scraper {scraper.platform_name} for term '{term}'")
    try:
        results = await scraper.search(term)
        for result in results:
            scraper.save_annuncio(result)
        logger.info(f"Saved {len(results)} results for term '{term}' from {scraper.platform_name}")
    except Exception as e:
        logger.error(f"Error running scraper {scraper.platform_name} for term '{term}': {e}", exc_info=True)
    finally:
        scraper.close()

def setup_scraper_jobs():
    """Set up scheduled jobs for each platform scraper."""
    # Get search terms from environment
    search_terms_str = os.getenv("SEARCH_TERMS", "")
    if not search_terms_str:
        logger.warning("No SEARCH_TERMS environment variable set. Using default: smartphone, laptop, bicicletta")
        search_terms = ["smartphone", "laptop", "bicicletta"]
    else:
        search_terms = [t.strip() for t in search_terms_str.split(",") if t.strip()]

    if not search_terms:
        logger.warning("No search terms configured after parsing.")
        return

    # List of scraper instances to schedule
    scraper_instances = [
        SubitoScraper(),
        # VintedScraper(),
        # EbayScraper(),
    ]

    if not scraper_instances:
        logger.warning("No scrapers configured.")
        return

    interval_minutes = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "30"))

    for scraper in scraper_instances:
        job_id = f"scraper_{scraper.platform_name}"
        # Remove existing job if any
        if job_id in scheduler.jobs:
            scheduler.remove_job(job_id)

        # Define the async job function
        async def job_fn():
            for term in search_terms:
                await run_scraper_for_term(scraper, term)
                # Wait a bit between terms to avoid being too aggressive
                await asyncio.sleep(5)

        # Wrapper to run the async function in a sync context for APScheduler
        def job_wrapper():
            asyncio.run(job_fn())

        # Add the job
        scheduler.add_job(
            func=job_wrapper,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            name=f"Scrape {scraper.platform_name} for terms {search_terms}",
            replace_existing=True,
        )
        logger.info(f"Scheduled job '{job_id}' every {interval_minutes} minutes.")

def main():
    """Main application entry point."""
    # Reconfigure logging in case it was changed by environment after import
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "logs/app.log")
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger.info("Avvio dell'applicazione di monitoraggio mercatini dell'usato...")

    # Initialize services (run async initialization)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(initialize_services())

    # Set up scheduled jobs
    setup_scraper_jobs()

    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to exit.")

    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal. Stopping scheduler...")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep the main thread alive
    try:
        # Unix: wait for signal
        signal.pause()
    except AttributeError:
        # Windows: sleep in a loop
        while True:
            import time
            time.sleep(1)

if __name__ == "__main__":
    main()