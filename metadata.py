import logging
import os
import time
import tkinter.scrolledtext as ScrolledText
from concurrent.futures import ProcessPoolExecutor
from tkinter import (
    END,
    Button,
    Label,
    StringVar,
    Tk,
    filedialog
)

from ShazamAPI import Shazam
from mutagen.id3 import APIC, ID3, USLT
from mutagen.mp3 import EasyMP3

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()
# logger = logging.getLogger(__name__)
from threading import Thread


def run_in_thread(fun):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fun, args=args, kwargs=kwargs)
        thread.setDaemon(True)
        thread.start()
        return thread

    return wrapper


# @run_in_thread
def individual_process(mp3file_name, select_directory):
    global x
    x=None
    file_name = mp3file_name
    mp3_file_content_to_recognize = open(file_name, "rb").read()
    tags = EasyMP3(file_name)
    tags.delete()
    tags.save()
    title_ = None
    shazam = Shazam(mp3_file_content_to_recognize)
    try:
        recognize_generator = shazam.recognizeSong()
        # # while True:
        x = next(recognize_generator)
        # plogger.info(x)
        if x[1].get("track") is None:
            logger.info("Cant recognise song")
    except Exception as except__:
        logger.error("cant recognise song", except__)

    try:
        title = x[1].get("track").get("title")
        artist = x[1].get("track").get("subtitle")
        genre = x[1].get("track").get("sections")[0].get("metadata")[1].get("text")
        year = x[1].get("track").get("sections")[0].get("metadata")[2].get("text")
        album = x[1].get("track").get("sections")[0].get("metadata")[0].get("text")
    except Exception as except__:
        logger.info("Exception in extraction ", except__)
        pass

    try:
        tags["date"] = year
        tags["genre"] = genre
        tags["title"] = title
        tags["artist"] = artist
        tags["album"] = album
        tags.save()
    except Exception as except__:
        logger.info("Exception in TAGS ", except__)
        pass

    try:
        logger.info(f"      | Fetching Lyrics   |")
        lyrics = x[1].get("track").get("sections")[1].get("text")
        if lyrics:
            tags = ID3(file_name)
            uslt_output = USLT(encoding=3, lang="eng", desc="desc", text=lyrics)
            tags["USLT::'eng'"] = uslt_output

            tags.save(file_name)
        else:
            pass
    except Exception as except__:
        logger.error("Exception in LYRIC ", except__)
        pass

    try:
        image = x[1].get("track").get("share").get("image")
        if image:
            import requests

            logger.info(f"      | Fetching Image    |")
            img = requests.get(image, stream=True).raw  # Gets album art from url

            audio = EasyMP3(file_name, ID3=ID3)

            audio.tags.add(
                APIC(
                    encoding=3,  # UTF-8
                    mime="image/png",
                    type=3,  # 3 is for album art
                    desc="Cover",
                    data=img.read(),  # Reads and adds album art
                )
            )
            logger.info(f"      | Saving..          |")
            audio.save()
            logger.info(f"{title} | Saved ]")

        else:
            pass
    except Exception as except__:
        logger.info("Exception in ALBUM ART ", except__)
        pass

    try:
        title_ = f"{title} | {artist}.mp3"
        os.rename(f"{file_name}", f"{select_directory}/{title_}")
    except Exception as except__:
        logger.error(f"Exception in RENAMING {except__}")
        return f"Exception in RENAMING {except__}"
    return f"{title_} | Saved"


@run_in_thread
def process():
    select_directory = folder_path.get()
    start = time.perf_counter()
    responses = []
    with ProcessPoolExecutor() as executor:
        for mp3file_name in mp3gen(select_directory):
            responses.append(
                executor.submit(individual_process, mp3file_name, select_directory)
            )
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


# class Application(Tk):

#     def __init__(self):
#         super().__init__()
#         self.title('Media Player')
#         self.style = Style()
#         self.style.theme_use('minty')

if __name__ == "__main__":
    # with ETM() as etm:
    # style = Style(theme='superhero')
    window = Tk()
    window.geometry("900x500")
    window.title("MP3 Album Artwork")

    st = ScrolledText.ScrolledText()
    st.configure(font="TkFixedFont")
    st.pack()
    text_handler = TextHandler(st)
    logger.addHandler(text_handler)
    logger.info("Hey - Select the directory of mp3 files below..")
    select_directory = Button(window, text="Select Directory", command=browse_button)
    select_directory.pack()

    # Label to store chosen directory.
    folder_path = StringVar()
    directory_label = Label(window, textvariable=folder_path, bg="#D3D3D3", width=70)
    directory_label.pack()

    # Button to run main script.
    go_button = Button(window, text="Go", command=process)
    go_button.pack()

    # Button to quit the app.
    quit_button = Button(window, text="Quit", command=window.quit)
    quit_button.pack()

    window.mainloop()
