#! /bin/env python

import os
import datetime
from telethon.sync import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeImageSize
from telethon.tl import types

import json

CONFIG_FILE = "config.json"

# Funktion zum Laden der Konfigurationsdaten aus der JSON-Datei
def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print(f"Die Konfigurationsdatei '{CONFIG_FILE}' wurde nicht gefunden.")
        return None
    except json.JSONDecodeError:
        print(f"Die Konfigurationsdatei '{CONFIG_FILE}' ist ungültig.")
        return None

# Funktion zum Speichern der Konfigurationsdaten in der JSON-Datei
def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

# Laden der Konfigurationsdaten
config = load_config()

if config is None:
    exit(1)

## Zugriffstoken deines Telegram-Accounts
API_ID = config.get("api_id")
API_HASH = config.get("api_hash")
PHONE_NUMBER = config.get("phone_number")
SAVE_DIRECTORY = config.get("save_directory")
excluded_usernames = config.get("excluded_usernames", [])

# Funktion zum Herunterladen der Dateien
def download_media(message, chat, chat_title,excluded_usernames):
    date = message.date
    chat_id = message.chat_id
    user = message.sender

    # Überprüfen, ob der Benutzername in der Ausschlussliste enthalten ist
    if user.username in excluded_usernames:
        print(f"Datei von Benutzer wird nicht heruntergeladen: '{user.username}'")
        return

    # Erstellen des Verzeichnispfads basierend auf Jahr/Monat/Chat-Titel/Chat-ID/Benutzer-ID/Benutzername
    directory = os.path.join(
        SAVE_DIRECTORY,
        str(date.year),
        str(date.month),
        "TelegramMediaRipper",
        str(chat_title),
        str(chat_id),
        str(user.id),
        user.username if user.username else str(user.id)
    )

    # Überprüfen, ob das Verzeichnis vorhanden ist, andernfalls erstellen
    os.makedirs(directory, exist_ok=True)

    # Herunterladen der Medien und Dateien
    if message.document:
        # Überprüfen, ob das Dokument ein Bild ist
        if any(isinstance(x, DocumentAttributeImageSize) for x in message.document.attributes):
            file_name = next((x.file_name for x in message.document.attributes if isinstance(x, DocumentAttributeFilename)), None)
            if not file_name:
                file_name = f"image.jpg"
            file_path = os.path.join(directory, f"{date.strftime('%Y%m%d%H%M%S')}_{file_name}")
            if not os.path.exists(file_path):
                client.download_media(message, file=file_path)
                print(f"Die Datei wird heruntergeladen: {file_path}")
            else:
                print(f"Die Datei existiert bereits und wird nicht erneut heruntergeladen: {file_path}")


# Telegram-Client-Initialisierung und Authentifizierung
client = TelegramClient('MediaRipper', API_ID, API_HASH)
client.connect()

# Überprüfen, ob eine aktive Sitzung vorhanden ist, andernfalls die Authentifizierung durchführen
if not client.is_user_authorized():
    client.send_code_request(PHONE_NUMBER)
    client.sign_in(PHONE_NUMBER, input('Gib den erhaltenen Verifizierungscode ein: '))

# Handler für eingehende Nachrichten
@client.on(events.NewMessage)
async def handle_message(event):
    chat = await event.get_chat()
    if event.media:
        if isinstance(chat, types.User):
            chat_title = chat.username or "Direct Messages"
        else:
            chat_title = chat.title
        download_media(event.message, chat, chat_title,excluded_usernames)

# Alle vergangenen Nachrichten abrufen und herunterladen
for dialog in client.iter_dialogs():
    chat = dialog.entity
    chat_title = chat.title if hasattr(chat, 'title') else chat.username
    messages = client.iter_messages(chat)
    for message in messages:
        if message.document:
            #image_size = next((x for x in message.document.attributes if isinstance(x, DocumentAttributeImageSize)), None)
            download_media(message, chat, chat_title,excluded_usernames)

# Starte den Telegram-Client
client.run_until_disconnected()
