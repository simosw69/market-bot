# Mercatini dell'Usato Aggregator

Un sistema di aggregazione per mercatini dell'usato (Subito, Vinted, eBay, ecc.) con funzionalità di ricerca, filtrazione, identificazione di affari tramite AI e notifiche tramite Telegram.

## Architettura

Il sistema segue un'architettura a microservizi basata su Docker, ottimizzata per l'esecuzione in locale.

### Componenti

1. **Ingestion Layer (Scrapers)**: Worker Python (Playwright) che eseguono lo scraping dei siti di annunci.
2. **Normalization Layer**: Modulo di pulizia che standardizza i dati (prezzi, date, valute) in un formato comune.
3. **Database**: SQLite (file locale gestito via SQLAlchemy).
4. **Intelligence Layer (AI/ML)**: Ollama (locale) per analisi del sentiment e classificazione annunci.
5. **Notification Layer**: Bot Telegram dedicato per inviare notifiche.
6. **Orchestratore**: APScheduler (integrato nel backend) per gestire la frequenza dei task di scraping.

## Struttura del Progetto

```
market-bot/
├── app/                    # Applicazione Python principale
│   ├── __init__.py
│   ├── main.py             # Punto di ingresso
│   ├── database/           # Modelli e gestione database
│   │   ├── __init__.py
│   │   ├── models.py       # Modelli SQLAlchemy
│   │   └── database.py     # Engine e session
│   ├── intelligence/       # Integrazione con Ollama (AI)
│   │   ├── __init__.py
│   │   └── ollama_client.py
│   ├── notification/       # Notifiche (Telegram)
│   │   ├── __init__.py
│   │   └── telegram_bot.py
│   ├── orchestrator/       # Pianificazione task (APScheduler)
│   │   ├── __init__.py
│   │   └── scheduler.py
│   └── scrapers/           # Scraper per varie piattaforme
│       ├── __init__.py
│       ├── base.py         # Classe base per gli scraper
│       ├── subito.py       # Esempio di scraper per Subito
│       ├── vinted.py       # Da implementare
│       └── ebay.py         # Da implementare
├── data/                   # Directory per il database SQLite (montato come volume)
├── logs/                   # Directory per i file di log
├── Dockerfile              # Definizione dell'immagine Docker per il backend
├── docker-compose.yaml     # Orchestrazione dei servizi
├── requirements.txt        # Dipendenze Python
└── .env.example            # Esempio di variabili d'ambiente
```

## Avvio Rapido

### Prerequisiti

- Docker e Docker Compose installati
- (Opzionale) Git per clonare il repository

### Passi

1. **Clona il repository** (se applicabile) o copia i file in una directory sul tuo server domestico.

2. **Copia il file di esempio delle variabili d'ambiente**:
   ```bash
   cp .env.example .env
   ```

3. **Modifica il file `.env`** con le tue configurazioni:
   - `TELEGRAM_BOT_TOKEN`: Token del tuo bot Telegram (ottenuto da @BotFather)
   - `TELEGRAM_CHAT_ID`: ID della chat o del canale dove vuoi ricevere le notifiche
   - `SEARCH_TERMS`: Elenco di termini di ricerca separati da virgola (es. `smartphone,laptop,bicicletta`)
   - `OLLAMA_MODEL`: Modello Ollama da usare (default: `phi3`)
   - `SCRAPE_INTERVAL_MINUTES`: Intervallo in minuti tra le esecuzioni dello scraping (default: 30)
   - `LOG_LEVEL`: Livello di log (DEBUG, INFO, WARNING, ERROR)
   - `LOG_FILE`: Percorso del file di log

4. **Avvia i servizi con Docker Compose**:
   ```bash
   docker-compose up -d
   ```
   Questo avvierà:
   - Un servizio `backend` che contiene l'applicazione Python (scraper, AI, notifiche, scheduler)
   - Un servizio `ollama` per eseguire il modello linguistico locale

5. **Monitora i log**:
   ```bash
   docker-compose logs -f backend
   ```

6. **Ferma i servizi**:
   ```bash
   docker-compose down
   ```

## Dettagli dei Servizi

### Backend (Python)

L'applicazione Python svolge tutte le funzioni principali:
- Esegue gli scraper secondo lo schedule definito da APScheduler.
- Salva i dati raccolti in un database SQLite locale.
- Utilizza Ollama (modello locale come `phi3` o `llama3`) per analizzare i titoli e le descrizioni degli annunci, determinando se si tratta di un "affare" (prezzo sotto la media) e fornendo un punteggio di affidabilità.
- Invia notifiche tramite Telegram quando viene trovato un potenziale affare.
- Gestisce il database tramite SQLAlchemy (modello `Annuncio`).

### Ollama

Il servizio Ollama esegue un modello linguistico locale (default: `phi3`). Questo modello viene utilizzato per:
- Analizzare il titolo e la descrizione di un annuncio per determinare la congruenza del prezzo.
- Classificare la categoria dell'oggetto.
- Fornire una spiegazione del giudizio.

È possibile cambiare il modello impostando la variabile d'ambiente `OLLAMA_MODEL` nel file `.env`. Modelli consigliati: `phi3` (veloce e leggero), `llama3` (più potente ma richiede più risorse).

### Database

Il database è un file SQLite chiamato `annunci.db` situato nella directory `data/`. Questo file è montato come volume nel container `backend` per garantire la persistenza dei dati tra i riavvii del container.

## Personalizzazione

### Aggiungere nuovi scraper

Per aggiungere un nuovo scraper (ad esempio per un nuovo sito di annunci):
1. Creare un nuovo file Python nella directory `app/scrapers/` (es. `subito_newsito.py`).
2. Far ereditare la classe dalla classe `BaseScraper` (in `app/scrapers/base.py`).
3. Implementare i metodi astratti `search` e `scrape_listing` utilizzando Playwright o Selenium.
4. Afrom `app.scrapers.base.BaseScraper`.
3. Implementare i metodi `search(query: str, filters: dict = None) -> List[Dict]` e `scrape_listing(url: str) -> Dict`.
4. Aggiungere l'istanza del nuovo scraper nella lista `scraper_instances` nella funzione `setup_scraper_jobs()` in `app/main.py`.

### Modificare il modello di dati

Se è necessario aggiungere nuovi campi al modello `Annuncio`, modificare `app/database/models.py` e poi ricostruire il container:
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Cambiare l'intervallo di scraping

Impostare la variabile d'ambiente `SCRAPE_INTERVAL_MINUTES` nel file `.env` (default: 30 minuti).

## Note Importanti

- **Rispetto dei siti web**: Assicurati di rispettare i termini di servizio e i limiti di velocità dei siti che stai facendo scraping. Il progetto include già alcune best practice (random sleep, rotazione di user-agent, uso di playwright-stealth) ma è tua responsabilità usarli in modo etico e legale.
- **Risorse di sistema**: L'esecuzione di modelli AI locali come Ollama può essere intensiva in termini di RAM e CPU. Assicurati che il tuo server domestico abbia risorse sufficienti.
- **Aggiornamenti**: Per aggiornare il codice, semplicemente eseguire `git pull` (se hai clonato il repository) e poi `docker-compose up -d --build`.

## License

Questo progetto è rilasciato sotto la licenza MIT. Vedi il file `LICENSE` per ulteriori dettagli.

---

**Nota**: Questo è un punto di partenza per lo sviluppo. Alcuni componenti (come gli scraper specifici per Vinted e eBay, la normalizzazione avanzata dei dati, e le funzionalità avanzate di AI) sono da implementare secondo le proprie esigenze.