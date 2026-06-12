# File Store Pro - Telegram Bot

A Telegram bot for file storage and sharing. Built with Python, Pyrogram (pyrofork), MongoDB (motor), and aiohttp.

## Project Structure

- `main.py` — Entry point; runs bot + web server concurrently
- `bot.py` — Bot class (Pyrogram Client subclass), startup logic
- `config.py` — All configuration (tokens, DB URI, channel IDs, messages)
- `plugins/` — Command handlers (start, admins, broadcast, link generator, etc.)
- `helper/` — Database utilities (MongoDB via motor)
- `requirements.txt` — Python dependencies

## Setup

1. Fill in `config.py` with:
   - `TOKEN` — Telegram Bot Token
   - `API_ID` / `API_HASH` — Telegram API credentials
   - `DB_URI` — MongoDB connection string
   - `DB_CHANNEL` — Telegram channel ID used as file database
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python3 main.py`

## Web Server

The aiohttp web server runs on port 5000 and serves a rendered README at `/`.

## User Preferences

- Port: 5000 for the web server (aiohttp)
