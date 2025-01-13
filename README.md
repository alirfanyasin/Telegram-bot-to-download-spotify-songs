# Telegram Bot To Download Spotify Song

## Requirements

```py
# Library
pip3 install aiogram==2.25.1
pip3 install spotdl==4.2.10
pip3 install python-dotenv==1.0.1
pip3 install requests==2.32.3

# (Optional) Verify versions
pip3 show aiogram
pip3 show spotdl
pip3 show python-dotenv
pip3 show requests

```


Download FFmpeg at this link : <br>
https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip <br><br>

Donwload Visual Studi Code at this link : https://code.visualstudio.com <br><br>


## Usage

After creating an API Token on Spotify and creating a BotFather, change the token to the token you own.
```py
client_id = 'MASUKKAN_CLIENT_ID_SPOTIFY_KAMU'
client_secret = 'MASUKKAN_CLIENT_SECRET_SPOTIFY_KAMU'
botfather_token = 'MASUKKAN_KODE_BOTFATHER_KAMU'
```

And then, change the directory save location to save the downloaded songs.
```py
 output_dir = r'E:\\Code_Project\\06_Song_Download\\Music'
```
