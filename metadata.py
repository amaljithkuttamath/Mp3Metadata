import logging
import os
import time
import tkinter.scrolledtext as ScrolledText
from concurrent.futures import ProcessPoolExecutor
import tkinter as tk
from tkinter import ttk
from tkinter import ttk, filedialog, Menu, Text, END
from threading import Thread
import requests
from ShazamAPI import Shazam
from mutagen.id3 import APIC, ID3, USLT
from mutagen.mp3 import EasyMP3
from pprint import pprint

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
# logger = logging.getLogger(__name__)
from threading import Thread

dark_mode = True
# folder_path = StringVar()


def run_in_thread(fun):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fun, args=args, kwargs=kwargs)
        thread.setDaemon(True)
        thread.start()
        return thread

    return wrapper


def fetch_song_details(mp3_file_content):
    """Fetch song details using Shazam API."""
    shazam = Shazam(mp3_file_content)
    try:
        recognize_generator = shazam.recognizeSong()
        song_details = next(recognize_generator)
        if not song_details[1].get("track"):
            logger.info("Can't recognize song")
            return None
        return song_details[1].get("track")
    except Exception as e:
        logger.error(f"Error recognizing song: {e}")
        return None


def update_tags(file_name, title, artist, genre, year, album):
    """Update MP3 tags."""
    try:
        tags = EasyMP3(file_name)
        tags["date"] = year
        tags["genre"] = genre
        tags["title"] = title
        tags["artist"] = artist
        tags["album"] = album
        tags.save()
    except Exception as e:
        logger.error(f"Error updating tags: {e}")


def add_lyrics(file_name, lyrics):
    """Add lyrics to MP3 file."""
    try:
        tags = ID3(file_name)
        uslt_output = USLT(encoding=3, lang="eng", desc="desc", text=lyrics)
        tags["USLT::'eng'"] = uslt_output
        tags.save(file_name)
    except Exception as e:
        logger.error(f"Error adding lyrics: {e}")


def add_album_art(file_name, image_url):
    """Add album art to MP3 file."""
    try:
        img = requests.get(image_url, stream=True).raw
        audio = EasyMP3(file_name, ID3=ID3)
        audio.tags.add(
            APIC(
                encoding=3,
                mime="image/png",
                type=3,
                desc="Cover",
                data=img.read(),
            )
        )
        audio.save()
    except Exception as e:
        logger.error(f"Error adding album art: {e}")


def individual_process(mp3file_name, select_directory):
    file_name = mp3file_name
    mp3_file_content_to_recognize = open(file_name, "rb").read()

    # Fetch song details
    song_details = fetch_song_details(mp3_file_content_to_recognize)
    # pprint(song_details)
    if not song_details:
        return "Unrecognized song"

    # Extract song details
    title = song_details.get("title")
    artist = song_details.get("subtitle")
    genre = song_details.get("genres", {}).get("primary", None)

    # Safely extract year
    sections = song_details.get("sections", [])
    metadata = sections[0].get("metadata", []) if sections else []
    year = metadata[2].get("text") if len(metadata) > 2 else None

    # Safely extract album
    album = metadata[0].get("text") if metadata else None

    # Update tags
    update_tags(file_name, title, artist, genre, year, album)

    # Add lyrics
    lyrics = song_details.get("sections")[1].get("text")
    if lyrics:
        add_lyrics(file_name, lyrics)

    # Add album art
    image_url = song_details.get("share").get("image")
    if image_url:
        add_album_art(file_name, image_url)

    # Rename file
    invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    new_file_name = f"{title} | {artist}.mp3"
    for char in invalid_chars:
        new_file_name = new_file_name.replace(char, "")
    # new_file_name = new_file_name.replace(char, '')

    # new_file_name = f"{title} | {artist}.mp3"
    try:
        os.rename(file_name, os.path.join(select_directory, new_file_name))
        return f"{new_file_name} | Saved"
    except Exception as e:
        logger.error(f"Error renaming file: {e}")
        return f"Error renaming file: {e}"


@run_in_thread
def process():
    select_directory = folder_path.get()
    start = time.perf_counter()
    responses = []
    with ProcessPoolExecutor() as executor:
        for mp3file_name in mp3gen(select_directory):
            responses.append(executor.submit(individual_process, mp3file_name, select_directory))
            # individual_process(mp3file_name, select_directory)
            # ET()
            # executor.map()
    for response in responses:
        logger.info(f"{response.result()}")
    logger.info(f"Time taken : {time.perf_counter() - start}")
    logger.info("-- Thank You --")


def mp3gen(direct):
    """Walks in the dir

    Args:
        direct : directory

    Yields:
        : each filename MP3
    """
    # print(os.walk(direct))
    # logger.info('Searching in : {base}')
    # logger.info(f'Total number of mp3 files {len(files)}')
    x = 0
    for root, dirs, files in os.walk(direct):
        if x == 0:
            logger.info(f"Found Mp3 - {len(files)} Files")
            x = 1
        for filename in files:
            if os.path.splitext(filename)[1] == ".mp3":
                logger.info(f"Recognising Song... | {filename}")
                yield os.path.join(root, filename)
                # ET().stop()
    # logger.info("-- Thank You --")


def browse_button():
    """Button will open a window for directory selection"""
    global folder_path
    selected_directory = filedialog.askdirectory()
    folder_path.set(selected_directory)


def play_music():
    file_path = filedialog.askopenfilename()
    # Use a library like pygame to play the music
    # pygame.mixer.music.load(file_path)
    # pygame.mixer.music.play()


def create_ui():
    global window, title_label, folder_path, style, dark_mode
    window = tk.Tk()
    window.geometry("900x600")
    window.title("MP3 Album Artwork Enhancer")
    window.configure(bg="#f0f0f0")

    # Menu Bar
    menu = Menu(window)
    window.config(menu=menu)

    file_menu = Menu(menu)
    menu.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Open", command=browse_button)
    file_menu.add_command(label="Exit", command=window.quit)

    view_menu = Menu(menu)
    menu.add_cascade(label="View", menu=view_menu)
    # view_menu.add_command(label="Lyrics", command=show_lyrics)
    view_menu.add_command(label="Player", command=play_music)

    # Create a style for the label
    style = ttk.Style()
    style.configure("BG.TLabel", background="#f0f0f0")

    # Title Label with the new style
    title_label = ttk.Label(window, text="MP3 Album Artwork Enhancer", font=("Arial", 24, "bold"), style="BG.TLabel")
    title_label.pack(pady=20)

    # Instructions Label
    instructions_label = ttk.Label(
        window,
        text="Select the directory of MP3 files and enhance them with album artwork and metadata.",
        wraplength=800,
        font=("Arial", 12),
    )
    instructions_label.pack(pady=10)

    # Directory Selection Frame
    directory_frame = ttk.Frame(window)
    directory_frame.pack(pady=20, padx=20, fill=tk.X)

    folder_label = ttk.Label(directory_frame, text="Directory:", font=("Arial", 12))
    folder_label.grid(row=0, column=0, padx=(0, 10))

    folder_path = tk.StringVar()
    folder_entry = ttk.Entry(directory_frame, textvariable=folder_path, width=50)
    folder_entry.grid(row=0, column=1, padx=(0, 10), sticky=tk.W)

    select_directory_button = ttk.Button(directory_frame, text="Select Directory", command=browse_button)
    select_directory_button.grid(row=0, column=2)

    # Action Buttons Frame
    action_frame = ttk.Frame(window)
    action_frame.pack(pady=20)

    go_button = ttk.Button(action_frame, text="Enhance MP3s", command=process)
    go_button.pack(side=tk.LEFT, padx=10)

    # play_button = ttk.Button(action_frame, text="Play", command=play_music)
    # play_button.pack(side=tk.LEFT, padx=10)

    dark_mode_button = ttk.Button(action_frame, text="Toggle Dark Mode", command=toggle_dark_mode)
    dark_mode_button.pack(side=tk.LEFT, padx=10)

    quit_button = ttk.Button(action_frame, text="Quit", command=window.quit)
    quit_button.pack(side=tk.LEFT, padx=10)

    # Log Frame
    log_frame = ttk.LabelFrame(window, text="Logs", padding=(10, 10))
    log_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

    st = ScrolledText.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=20)
    st.pack(fill=tk.BOTH, expand=True)

    # Attach logger to scrolled text
    text_handler = TextHandler(st)
    logger.addHandler(text_handler)

    window.mainloop()


def toggle_dark_mode():
    global dark_mode, window, title_label, style, dark_mode

    if not dark_mode:
        # Switch to dark mode
        window.configure(bg="#333")
        style.configure("BG.TLabel", background="#333", foreground="#f0f0f0")
        title_label.configure(style="BG.TLabel")
        # ... [configure other widgets for dark mode]
        dark_mode = True
    else:
        # Switch to light mode
        window.configure(bg="#f0f0f0")
        style.configure("BG.TLabel", background="#f0f0f0", foreground="#333")
        title_label.configure(style="BG.TLabel")
        # ... [configure other widgets for light mode]
        dark_mode = False


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state="normal")
            self.text.insert(END, msg + "\n")
            self.text.configure(state="disabled")
            # Autoscroll to the bottom
            self.text.yview(END)

        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)


if __name__ == "__main__":
    # with ETM() as etm:
    # style = Style(theme='superhero')
    create_ui()