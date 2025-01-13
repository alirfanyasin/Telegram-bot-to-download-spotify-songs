from aiogram import Bot, Dispatcher, types  # Mengimpor modul utama untuk membuat bot Telegram
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton  # Mengimpor elemen antarmuka bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage  # Penyimpanan state untuk state machine
from aiogram.dispatcher.filters.state import State, StatesGroup  # Membuat dan mengelola state pada bot
from aiogram.dispatcher import FSMContext  # Konteks untuk menangani state machine
from aiogram.utils import executor  # Untuk menjalankan polling bot
import base64  # Mengencode dan decode string ke Base64
import io  # Modul untuk manajemen file dalam memori
from requests import post, get  # Mengirimkan HTTP POST dan GET request
import json  # Untuk memproses data dalam format JSON
import spotdl  # Library untuk mendownload lagu
import os  # Mengelola operasi file dan direktori

# Konfigurasi token dan kredensial API
client_id = 'c99e4a8b2be04bc3934baf5d94f57f42'
client_secret = '68644cff9e4846d9a65ec8980b8d0a82'
botfather_token = '7827161682:AAFBgTUY_IwWOauDSVN0JxANH9rmz1W03Wk'

# Inisialisasi bot, penyimpanan state, dan dispatcher
bot = Bot(token=botfather_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Definisi state untuk mesin state pada bot
class SearchState(StatesGroup):
    waiting_for_input = State()
    waiting_for_download = State()
    
    
# Fungsi untuk mendapatkan token autentikasi Spotify
def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]  # Mendapatkan token akses dari respon
    return token


# Fungsi untuk membuat header autentikasi
def get_auth_header(token):
    return{"Authorization": "Bearer " + token}

# Mendapatkan token Spotify saat aplikasi dijalankan
token = get_token()

# Handler untuk perintah /start
@dp.message_handler(commands=["start"])
async def start_command_handler(message: types.Message):

    # Membuat keyboard dengan tombol opsi pencarian
    button_keyword = InlineKeyboardButton("Text", callback_data="search_by_text")
    button_other_option = InlineKeyboardButton("Mood", callback_data="search_by_mood")
    keyboard = InlineKeyboardMarkup().add(button_keyword, button_other_option)

    # Mengirim pesan selamat datang
    await bot.send_photo(
        chat_id=message.chat.id,
        photo="https://static.wixstatic.com/media/f92fc5_64f5f26fd42a419fa859d8ab05afa8a2~mv2.png/v1/fill/w_568,h_328,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/f92fc5_64f5f26fd42a419fa859d8ab05afa8a2~mv2.png",
        caption="Welcome to MusicMusic! Feel free to explore by clicking the button below:",
        reply_markup=keyboard
    )


# Handler untuk pencarian berdasarkan teks
@dp.callback_query_handler(lambda callback_query: callback_query.data == "search_by_text")
async def handle_search_by_text(callback_query: types.CallbackQuery, state: FSMContext):

    await bot.answer_callback_query(callback_query.id)
    # Meminta pengguna mengetikkan kata kunci lagu atau artis
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="Just type any song, name artist, or anything related to music you want..."
    )
    await SearchState.waiting_for_input.set()
    
# Fungsi untuk mencari lagu di Spotify berdasarkan teks
async def search_for_track(token, artist_track):

    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_track}&type=track"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["tracks"]["items"]
    return json_result

# Membuat keyboard dinamis untuk hasil pencarian lagu
async def build_inline_keyboard(search_result):
    inline_keyboard = InlineKeyboardMarkup(row_width=5)

    for idx, item in enumerate(search_result[:10]):
        callback_data = f"song_{idx}"
        text = f"{idx+1}"
        inline_keyboard.insert(InlineKeyboardButton(text=text, callback_data=callback_data))

    # Tombol tambahan untuk kembali ke menu utama
    extra_button_callback_data = "Home"
    extra_button_text = "🫡 Looking Other Songs? "
    extra_button = InlineKeyboardButton(text=extra_button_text, callback_data=extra_button_callback_data)
    inline_keyboard.row(extra_button)

    return inline_keyboard


# Handler untuk menerima input pesan pengguna ketika berada di state 'waiting_for_input'
@dp.message_handler(state=SearchState.waiting_for_input)
async def process_user_input(message: types.Message, state: FSMContext):
    
    # Mengambil teks yang dikirimkan oleh pengguna (misalnya nama lagu atau artis)
    artist_track = message.text
    await state.update_data(artist_track=artist_track)

    try:
        # Mencari lagu menggunakan fungsi search_for_track berdasarkan token Spotify dan input pengguna
        search_result = await search_for_track(token, artist_track)
    except Exception as e:
         # Jika terjadi error saat mencari lagu, kirimkan pesan error ke pengguna
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"Error while searching for tracks: {e}"
        )
        return
    # Menyimpan hasil pencarian ke dalam state
    await state.update_data(search_result=search_result)

    # Menyusun string yang berisi hasil pencarian lagu, memformat nama lagu dan artis
    result_artists = ''
    for idx, item in enumerate(search_result[:10]):
        artist = [artist["name"] for artist in item["artists"]]
        artist_name = ", ".join(artist).title()
        track_name = item['name'].title()
        result_artists += f"{idx + 1}. {track_name} by {artist_name}\n"

    inline_keyboard = await build_inline_keyboard(search_result)

    # Mengirim pesan ke pengguna dengan daftar lagu yang ditemukan, dan keyboard inline untuk memilih lagu
    await bot.send_message(
        chat_id=message.chat.id,
        text=f"Here are the top 10 songs:\n\n{result_artists}\n"
             "Feel free to click any number of songs to download it!",
        parse_mode=ParseMode.HTML,
        reply_markup=inline_keyboard
    )

    # Mengubah state menjadi 'waiting_for_download', menunggu pengguna memilih lagu untuk diunduh
    await SearchState.waiting_for_download.set()



# ========================================================================================================
# Search by Mood
# Handler untuk menangani callback ketika pengguna memilih opsi "search_by_mood" 
@dp.callback_query_handler(lambda callback_query: callback_query.data == "search_by_mood")
async def handle_search_by_mood(callback_query: types.CallbackQuery):
    # Menanggapi callback query dari pengguna untuk memberitahu bahwa query telah diproses
    await bot.answer_callback_query(callback_query.id)

    # Membuat keyboard inline untuk memilih mood
    mood_keyboard = InlineKeyboardMarkup()
    
    # Menambahkan tombol pilihan mood ke dalam keyboard
    mood_keyboard.add(
        InlineKeyboardButton("Normal", callback_data="mood_normal"), 
        InlineKeyboardButton("Happy", callback_data="mood_happy"), 
        InlineKeyboardButton("Sad", callback_data="mood_sad")   
    )

    # Mengirim pesan kepada pengguna, meminta mereka untuk memilih mood
    await bot.send_message(
        chat_id=callback_query.from_user.id,  
        text="Please select your mood:",    
        reply_markup=mood_keyboard            # Menyertakan keyboard inline yang telah dibuat
    )


# Handler untuk menangani callback ketika pengguna memilih mood (normal, happy, atau sad)
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith("mood_"))
async def handle_mood_selection(callback_query: types.CallbackQuery):
    
    # Menanggapi callback query dari pengguna untuk memberitahu bahwa query telah diproses
    await bot.answer_callback_query(callback_query.id)

    # Mengambil nilai mood yang dipilih pengguna dari callback data
    selected_mood = callback_query.data.split("_")[1]

    # Menentukan query pencarian berdasarkan mood yang dipilih
    mood_to_query = {
        "normal": "calm relaxing",  
        "happy": "happy upbeat",   
        "sad": "sad emotional"   
    }
    
    # Mendapatkan query pencarian berdasarkan mood yang dipilih, jika tidak ada pilih "calm relaxing"
    query = mood_to_query.get(selected_mood, "calm relaxing")

    try:
        # Mencari lagu berdasarkan query yang telah ditentukan
        search_result = await search_for_track(token, query)
    except Exception as e:
        # Jika terjadi kesalahan saat pencarian lagu, mengirim pesan kesalahan kepada pengguna
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text=f"Error while searching for tracks: {e}"
        )
        return

    # Menyiapkan daftar hasil pencarian untuk ditampilkan ke pengguna
    result_artists = ''
    for idx, item in enumerate(search_result[:10]):
        artist = [artist["name"] for artist in item["artists"]]
        artist_name = ", ".join(artist).title()
        track_name = item['name'].title()
        result_artists += f"{idx + 1}. {track_name} by {artist_name}\n"  # Menambahkan informasi lagu ke daftar

    # Membuat keyboard inline untuk memilih lagu
    inline_keyboard = await build_inline_keyboard(search_result)

    # Mengirim pesan kepada pengguna dengan hasil pencarian lagu yang sesuai dengan mood yang dipilih
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text=f"Top 10 songs for mood '{selected_mood.title()}':\n\n{result_artists}\n"
             "Feel free to click any number of songs to download it!",  # Pesan dengan daftar lagu
        parse_mode=ParseMode.HTML,
        reply_markup=inline_keyboard  # Menyertakan keyboard inline dengan opsi lagu
    )

    # Menyimpan data hasil pencarian di state untuk digunakan nanti
    await SearchState.waiting_for_download.set()
    await dp.current_state(user=callback_query.from_user.id).update_data(search_result=search_result)


# ========================================================================================================



# Handler untuk menangani callback query ketika pengguna memilih lagu untuk diunduh
@dp.callback_query_handler(state=SearchState.waiting_for_download)
async def process_callback_query(callback_query: types.CallbackQuery, state: FSMContext):
    
    # Mendapatkan data dari callback query yang dikirimkan
    callback_data = callback_query.data

    if not callback_data.startswith("song_"):
        return

    await bot.answer_callback_query(callback_query.id)

    idx = int(callback_data.split("_")[1])

    # Mendapatkan data yang tersimpan di state
    user_data = await state.get_data()
    search_result = user_data.get("search_result") 
    artist_track = user_data.get("artist_track")

    # Jika tidak ada hasil pencarian atau index yang dipilih tidak valid
    if not search_result or idx >= len(search_result):
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text="Invalid song selection. Please try again."
        )
        return

    # Mengambil informasi lagu yang dipilih berdasarkan index
    selected_song = search_result[idx]
    song_url = selected_song['external_urls']['spotify']  # URL lagu di Spotify
    song_name = selected_song['name']  # Nama lagu
    artist_name = ", ".join([artist["name"] for artist in selected_song["artists"]])  # Nama artis

    # Mengirim pesan bahwa proses unduhan lagu sedang berlangsung
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=f"Downloading your song: {song_name} by {artist_name}...",
        parse_mode=ParseMode.HTML
    )

    # Menentukan direktori output untuk menyimpan file lagu
    output_dir = r'C:\\Users\\Irfan Yasin\\Music'
    command = f'spotdl "{song_url}" --output "{output_dir}"'
    response = os.system(command)

    # Jika unduhan berhasil
    if response == 0:
        # Menentukan path file audio yang diunduh
        audio_file_path = os.path.join(output_dir, f"{artist_name} - {song_name}.mp3")
        # Menyiapkan keyboard inline untuk tombol kembali ke halaman utama
        keyboard_go_back = InlineKeyboardMarkup()
        go_back_button = InlineKeyboardButton("🫡 Looking Other Songs?", callback_data="Home")
        keyboard_go_back.add(go_back_button)

        # Mencoba mengirimkan file audio yang sudah diunduh ke pengguna
        try:
            with open(audio_file_path, "rb") as audio:
                await bot.send_audio(
                    chat_id=callback_query.message.chat.id,
                    audio=audio,  # Mengirimkan file audio
                    caption=f"✅ Your song '{song_name} - {song_name}' has been downloaded successfully, enjoy it! Thanks for using our bot.",
                    reply_markup=keyboard_go_back  # Menambahkan tombol untuk kembali
                )
        except Exception as e:
            # Jika ada kesalahan saat mengirimkan file audio, kirim pesan kesalahan
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text=f"❌ An error occurred while sending the file: {e}",
                reply_markup=keyboard_go_back  # Menambahkan tombol untuk kembali
            )

    else:
        # Jika ada kesalahan dalam proses unduhan, kirim pesan kesalahan
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text="❌ An error occurred during the download process.",
            reply_markup=keyboard_go_back  # Menambahkan tombol untuk kembali
        )

    # Menyelesaikan state dan mengakhiri sesi
    await state.finish()


# Menangani callback query ketika data dari query sama dengan "Home"
@dp.callback_query_handler(lambda callback_query: callback_query.data == "Home")
async def handle_go_home(callback_query: types.CallbackQuery):
    # Mengirimkan respons bahwa callback query telah diterima
    await bot.answer_callback_query(callback_query.id)
    
    # Memanggil fungsi start_command_handler untuk memulai pesan kembali
    await start_command_handler(callback_query.message)

# Menjalankan polling untuk menangani update callback yang masuk
if __name__ == '__main__':
    # Memulai polling dan melewati update yang tidak diperlukan
    executor.start_polling(dp, skip_updates=True)