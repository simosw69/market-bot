from abc import ABC, abstractmethod
import logging
from typing import List, Dict
from ..database.models import Annuncio
from ..database.database import SessionLocal
from ..intelligence.ollama_client import OllamaClient
from ..notification.telegram_bot import TelegramNotifier

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.db = SessionLocal()
        self.ollama = OllamaClient()
        self.notifier = TelegramNotifier()

    @abstractmethod
    async def search(self, query: str, filters: dict = None) -> List[Dict]:
        """
        Search for items on the platform.
        Returns a list of dictionaries with keys: titolo, descrizione, prezzo, url, immagini, categoria, luogo, condizioni, etc.
        """
        pass

    @abstractmethod
    async def scrape_listing(self, url: str) -> Dict:
        """
        Scrape a single listing given its URL.
        Returns a dictionary with the listing details.
        """
        pass

    def save_annuncio(self, annuncio_data: dict):
        """Save or update an announcement in the database."""
        # Check if exists by URL
        existing = self.db.query(Annuncio).filter(Annuncio.url == annuncio_data['url']).first()
        if existing:
            # Update existing
            for key, value in annuncio_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
        else:
            # Create new
            annuncio = Annuncio(**annuncio_data)
            self.db.add(annuncio)
        self.db.commit()
        # Optionally run AI analysis
        self.analyze_and_notify(annuncio_data)

    def analyze_and_notify(self, annuncio_data: dict):
        """Run AI analysis on the annuncio and send notification if it's a good deal."""
        titolo = annuncio_data.get('titolo', '')
        descrizione = annuncio_data.get('descrizione', '')
        if titolo and descrizione:
            analysis = self.ollama.analyze_listing(titolo, descrizione)
            if analysis:
                # Update the annuncio with analysis results
                # We'll update the database record
                annuncio_obj = self.db.query(Annuncio).filter(Annuncio.url == annuncio_data['url']).first()
                if annuncio_obj:
                    annuncio_obj.sentiment_score = analysis.get('affidabilita')
                    annuncio_obj.categoria_ai = analysis.get('categoria')
                    annuncio_obj.e_affare = analysis.get('prezzo_giusto')  # assuming field name
                    # ... etc
                    self.db.commit()
                # If it's a good deal, send a notification
                if analysis.get('prezzo_giusto') == True:  # or however we determine
                    message = f"🔥 Affare trovato su {self.platform_name}!\nTitolo: {titolo}\nPrezzo: {annuncio_data.get('prezzo')}\nLink: {annuncio_data.get('url')}"
                    # Send via telegram (we need to make this async, but for simplicity we'll use asyncio.run)
                    import asyncio
                    asyncio.run(self.notifier.send_message(message))

    def close(self):
        self.db.close()