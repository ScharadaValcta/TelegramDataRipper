# Setup
1. Copy example-config.json -> config.json
2. Edit config.json
    1. api_id and api_hash -> https://telegram.org/apps
    2. phone_number -> your phone number
    3. save_directory -> Path to the directory where the data should be stored
    4. archive_file -> Path to the archive file 
    5. excludeed_username -> list of usernames which will be ignored
    6. excluded_chats -> list of chat titels which will be ignored
    7. excluded_filename -> list of filenames which will be ignored
        - Tipp: "sticker.webp","AnimatedSticker.tgs"
3. python telegramdataripper.py
4. Give the connection authcode from Telegram
5. Wait
6. (optional) run as Service (not described here)