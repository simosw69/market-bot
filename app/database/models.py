from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Annuncio(Base):
    __tablename__ = 'annunci'

    id = Column(Integer, primary_key=True, index=True)
    piattaforma = Column(String(50), index=True)  # e.g., subito, vinted, ebay
    titolo = Column(String(255))
    descrizione = Text()
    prezzo = Column(Float)
    valuta = Column(String(10), default='EUR')
    data_annuncio = Column(DateTime)
    data_scraping = Column(DateTime, default=datetime.utcnow)
    url = Column(String(500), unique=True, index=True)
    immagine_url = Column(String(500))  # main image URL
    luogo = Column(String(100))
    condizioni = Column(String(50))  # nuovo, usato, etc.
    categoria = Column(String(100))  # category from scraping
    # AI analysis fields
    sentiment_score = Column(Integer)  # 0-10 (affidabilità)
    categoria_ai = Column(String(100))  # category from AI
    e_affare = Column(Boolean)  # whether AI thinks it's a good deal
    motivo_ai = Column(Text)  # reason from AI
    verified_price = Column(Float)  # average price from historical data or AI estimate
    deal_score = Column(Float)  # how good of a deal (0-100)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Annuncio {self.titolo} ({self.piattaforma})>"