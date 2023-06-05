#! /bin/env python

import os
import datetime
from telethon.sync import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeImageSize, MessageMediaPhoto, PhotoSize, PeerUser
from telethon.tl import types

import json

import asyncio

import datetime

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

# Funktion zum Hinzufügen des Strings zum Archiv
def add_to_archive(chat_id, user_id, message_id):
    file_path = f"{chat_id}_{user_id}_{message_id}"
    with open(ARCHIVE_FILE, "a") as archive:
        archive.write(file_path + "\n")

# Funktion zum Prüfen, ob eine Datei im Archiv vorhanden ist
def is_file_in_archive(chat_id, user_id, message_id):
    file_path = f"{chat_id}_{user_id}_{message_id}"
    with open(ARCHIVE_FILE, "r") as archive:
        file_list = archive.read().splitlines()
        return file_path in file_list

def aktuelles_datum():
    jetzt = datetime.datetime.now()
    datum_formatiert = jetzt.strftime("[%Y-%m-%d-%H-%M-%S]")
    return datum_formatiert

# Laden der Konfigurationsdaten
config = load_config()

if config is None:
    exit(1)

## Zugriffstoken deines Telegram-Accounts
API_ID = config.get("api_id")
API_HASH = config.get("api_hash")
PHONE_NUMBER = config.get("phone_number")
SAVE_DIRECTORY = config.get("save_directory")
ARCHIVE_FILE = config.get("archive_file")
excluded_usernames = config.get("excluded_usernames", [])
excluded_chats = config.get("excluded_chats", [])
excluded_filename = config.get("excluded_filename",[])

# Funktion zum Herunterladen der Dateien
async def download_media(message, chat, chat_title,excluded_usernames):
    date = message.date
    chat_id = message.chat_id
    user = message.sender

    # Überprüfen, ob der Benutzername in der Ausschlussliste enthalten ist
    if isinstance(message.sender_id, PeerUser):
        user = await client.get_entity(message.sender_id.user_id)
        if user.username is not None and user.username in excluded_usernames:
            print(f"{aktuelles_datum()} Datei wird wegen excluded_usernames nicht heruntergeladen: {chat_title} von '{user.username}'")
            return
    else:
        user = message.sender

    if chat_title in excluded_chats:
        print(f"{aktuelles_datum()} Datei aus Chat wird nicht heruntergeladen: '{chat_title}'")
        return

    if user is None and is_file_in_archive(chat_id, message.id, message.id):
        print(f"{aktuelles_datum()} Datei bereits in Archivfile {chat_title} ")
        return
    elif is_file_in_archive(chat_id, user.id, message.id):
        print(f"{aktuelles_datum()} Datei bereits in Archivfile {chat_title} ")
        return

    if user:
        user_id = str(user.id)
    else:
        user_id = "Deleted User"
    if user and user.username:
        user_username = user.username
    elif user and user.first_name != None and user.last_name != None:
        user_username = str(user.first_name) + " " + str(user.last_name) 
    elif user and user.first_name != None:
        user_username = user.first_name
    else:
        user_username = "Deleted User"

    # Erstellen des Verzeichnispfads basierend auf Jahr/Monat/Chat-Titel/Chat-ID/Benutzer-ID/Benutzername
    directory = os.path.join(
        SAVE_DIRECTORY, 
        "TelegramMediaRipper", 
        str(chat_title),
        str(date.year),
        f"{date.month:02d}",
        str(chat_id),
        user_id,
        user_username
    )
 
    # Herunterladen der Medien und Dateien
    if message.document:
        # Überprüfen, ob das Dokument ein Bild ist
        if any(isinstance(x, DocumentAttributeImageSize) for x in message.document.attributes):
            file_name = next((x.file_name for x in message.document.attributes if isinstance(x, DocumentAttributeFilename)), None)
            if not file_name:
                #file_name = f"image.jpg"
                file_name = f"IMG_{date.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.jpg"
            if file_name in excluded_filename:
                print(f"{aktuelles_datum()} Datei wird wegen exluded_filename nicht heruntergeladen: {chat_title} '{file_name}'")
                return
            # Überprüfen, ob das Verzeichnis vorhanden ist, andernfalls erstellen
            os.makedirs(directory, exist_ok=True)
            file_path = os.path.join(directory, f"{date.strftime('%Y%m%d%H%M%S')}_{file_name}")
            if not os.path.exists(file_path):
                await client.download_media(message, file=file_path)
                print(f"{aktuelles_datum()} Die Datei wird heruntergeladen: {chat_title}  {file_name}")
                if user is None:
                    add_to_archive(chat_id, message.id, message.id)
                else:
                    add_to_archive(chat_id, user.id, message.id)
            else:
                print(f"{aktuelles_datum()} Die Datei existiert bereits und wird nicht erneut heruntergeladen: {chat_title} {file_name}")
    elif isinstance(message.media, MessageMediaPhoto):
        # Überprüfen, ob das Medienelement ein Bild ist
        sizes = message.media.photo.sizes
        if any(isinstance(x, PhotoSize) for x in sizes):
            file_name = f"IMG_{date.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.jpg"

            if file_name in excluded_filename:
                print(f"{aktuelles_datum()} Datei wird wegen excluded_filename nicht heruntergeladen: {chat_title} '{file_name}'")
                return
            # Überprüfen, ob das Verzeichnis vorhanden ist, andernfalls erstellen
            os.makedirs(directory, exist_ok=True)
            file_path = os.path.join(directory, f"{date.strftime('%Y%m%d%H%M%S')}_{file_name}")
            if not os.path.exists(file_path):
                await client.download_media(message, file=file_path)
                print(f"{aktuelles_datum()} Die Datei wird heruntergeladen: {chat_title}  {file_name}")
                if user is None:
                    add_to_archive(chat_id, message.id, message.id)
                else:
                    add_to_archive(chat_id, user.id, message.id)
            else:
                print(f"{aktuelles_datum()} Die Datei existiert bereits und wird nicht erneut heruntergeladen:  {chat_title} {file_name}")

# Definition einer asynchronen Funktion
async def process_messages():
    #Alle vergangenen Nachrichten abrufen und herunterladen
    async for dialog in client.iter_dialogs():
        chat = dialog.entity
        chat_title = chat.title if hasattr(chat, 'title') else chat.username
        messages = client.iter_messages(chat)
        async for message in messages:
            if message.document:
                image_size = next((x for x in message.document.attributes if isinstance(x, DocumentAttributeImageSize)), None)
                await download_media(message, chat, chat_title, excluded_usernames)
            elif isinstance(message.media, MessageMediaPhoto):
                image_size = next((x for x in message.media.photo.sizes if isinstance(x, PhotoSize)), None)
                await download_media(message, chat, chat_title, excluded_usernames)


# Erstellen der Archivdatei, wenn sie nicht existiert
if not os.path.exists(ARCHIVE_FILE):
    open(ARCHIVE_FILE, "w").close()

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
    if event.media or event.document:
        if isinstance(chat, types.User):
            chat_title = chat.username or "Direct Messages"
        else:
            chat_title = chat.title
        if chat_title:
            await download_media(event.message, chat, chat_title,excluded_usernames)

# Erhalte den bereits vorhandenen Event-Loop
loop = asyncio.get_event_loop()
# Führe den asynchronen Task im vorhandenen Event-Loop aus
loop.run_until_complete(process_messages())

# Starte den Telegram-Client
client.run_until_disconnected()
