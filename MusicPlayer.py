import os
import sys
import json
import spotipy
import webbrowser
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
from json.decoder import JSONDecodeError
import certifi, os
import os
from dotenv import load_dotenv

load_dotenv()
os.environ['SSL_CERT_FILE'] = certifi.where()







auth_manager = SpotifyOAuth(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI', 'https://example.com/callback'),
    scope="user-read-private user-read-playback-state user-modify-playback-state",
    cache_path=f".cache",
    show_dialog=True
)

print("Opening browser for authentication...")
try:
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("Authentication successful!")
except Exception as e:
    print("Authentication failed")


# GUI CODE!!!! ------------------------------------------------------------------------------

import os
import tkinter
import customtkinter
import tkinter.font as tkfont
from PIL import Image, ImageTk
from threading import Thread, Event
import time
import io
import urllib.request

# Color

customtkinter.set_appearance_mode("light")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("cute_theme.json")

# outside the GUI \/
root = customtkinter.CTk()
root.title('Music Player')
# root.iconbitmap('Icon/test.png')
root.geometry ('450x205+0+0')
root.resizable(False, False) 


# Remove title bar (place this AFTER geometry setup)
root.overrideredirect(True)

# create the album cover and name placeholders
cover_label = tkinter.Label(root, borderwidth=3, background="#d4a373")
cover_label.place(relx=.05, rely=0.25)



song_name_label = tkinter.Label(root, bg='#fefae0', fg='#d4a373',
                                bd=0, font=("Microsoft PhagsPa", 16, "bold"))
song_name_label.place(relx=0.7, rely=0.3, anchor=tkinter.CENTER)

song_artist_label = tkinter.Label(root, bg='#fefae0', fg='#d4a373',
                                  bd=0, font=("Microsoft PhagsPa", 12))
song_artist_label.place(relx=0.7, rely=0.45, anchor=tkinter.CENTER)


# always on  top
root.attributes('-topmost', True)

# Create a simple title bar with close button
title_bar = customtkinter.CTkFrame(root, height=30, fg_color='#faedcd')
title_bar.pack(fill='x', side='top')

# Close button in title bar
close_button = customtkinter.CTkButton(title_bar, text="×", width=15, height=15, 
                                      command=root.quit, fg_color="#d44f4f", 
                                      hover_color="#a32b2b", font=("Arial", 16), text_color="white")
close_button.pack(side='right', padx=5, pady=2)

# Drag
def start_move(e):
    # Store the initial mouse position and window position
    title_bar.start_x = e.x_root
    title_bar.start_y = e.y_root
    title_bar.start_win_x = root.winfo_x()
    title_bar.start_win_y = root.winfo_y()

def stop_move(e):
    # Clean up the stored positions
    if hasattr(title_bar, 'start_x'):
        del title_bar.start_x
        del title_bar.start_y
        del title_bar.start_win_x
        del title_bar.start_win_y

def move_app(e):
    # Only move if we have the initial positions stored
    if hasattr(title_bar, 'start_x'):
        # Calculate how much the mouse has moved
        delta_x = e.x_root - title_bar.start_x
        delta_y = e.y_root - title_bar.start_y
        
        # Calculate new window position
        new_x = title_bar.start_win_x + delta_x
        new_y = title_bar.start_win_y + delta_y
        
        # Move the window to the new position
        root.geometry(f'+{new_x}+{new_y}')

# Bind the events
title_bar.bind('<Button-1>', start_move)  # Mouse click down
title_bar.bind('<ButtonRelease-1>', stop_move)  # Mouse release
title_bar.bind('<B1-Motion>', move_app)  # Mouse drag


# Font size -------------------------------------------------------------------------------
def fit_text(label, text, family, max_width, max_size, min_size, weight="normal"):
    """Shrink the font until the text fits in max_width pixels.
    If it still doesn't fit at min_size, truncate with an ellipsis."""
    size = max_size
    f = tkfont.Font(family=family, size=size, weight=weight)

    while size > min_size and f.measure(text) > max_width:
        size -= 1
        f.configure(size=size)

    if f.measure(text) > max_width:
        while len(text) > 1 and f.measure(text + "…") > max_width:
            text = text[:-1]
        text = text.rstrip() + "…"

    label.config(text=text, font=f)
    label.font_ref = f  # keep a reference so it isn't garbage collected



# SONG CODE!! -----------------------------------------------------------------------------

def get_current_track_info():
    """Get info about currently playing track"""
    try:
        playback = sp.current_playback()
        
        if playback and playback['item']:
            track = playback['item']
            return {
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'is_playing': playback.get('is_playing', False),
                'progress': playback.get('progress_ms', 0),
                'cover': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'duration_ms': track.get('duration_ms', 0),
                'item': track
            }
        return None
    except Exception as e:
        print("error getting track", repr(e))
        return None


n = 0
pause = False
stop_progress_thread = Event()
current_device_id = None

# Get spotify devicce
def get_active_device():
    global current_device_id
    try:
        devices = sp.devices()
        if devices and devices['devices']:
            for device in devices['devices']:
                if device['is_active']:
                     current_device_id = device['id']
                     return current_device_id
            current_device_id = devices['devices'][0]['id']
            return current_device_id
    except Exception as e:
        print("error with device", repr(e))
        current_device_id = None
        return None


# ------------ Threading -----------

def get_album_cover():
    track_info = get_current_track_info()

    # Update album cover
    cover_url = track_info['cover']
    with urllib.request.urlopen(cover_url) as u:
        raw_data = u.read()

    pil_image = Image.open(io.BytesIO(raw_data)).resize((125,125))
    tk_image = ImageTk.PhotoImage(pil_image)

    cover_label.config(image=tk_image)
    cover_label.image = tk_image  # keep reference

    # Update text labels
    song_name_label.config(text=track_info['name'])
    song_artist_label.config(text=track_info['artist'])
    fit_text(song_name_label, track_info['name'],
         "Microsoft PhagsPa", max_width=250, max_size=16, min_size=9, weight="bold")

    fit_text(song_artist_label, track_info['artist'],
         "Microsoft PhagsPa", max_width=250, max_size=12, min_size=8)


# self explainatory TO-DO
def update_progress_thread():
    # Calculate progress as a fraction (0..1) of the song length and set the progress bar
    try: 
        while not stop_progress_thread.is_set():
            # Get current track info using spotipy
            track_info = get_current_track_info()

            get_album_cover()
            
            if track_info and track_info.get('is_playing', False):
                # Calculate progress as a fraction (0..1)
                pos_ms = track_info['progress']
                duration_ms = track_info['duration_ms']
                
                if duration_ms > 0:
                    frac = pos_ms / duration_ms
                    # Update progress bar on main thread
                    root.after(0, lambda: progress_bar.set(min(max(frac, 0.0), 1.0)))
            
            time.sleep(1)  # Update every second
    except Exception as e:
        print("error")



def threading():
    t1 = Thread(target=update_progress_thread, daemon=True)
    t1.start()


# ------------ Buttons Functions ------------

def play_music():
    global pause
    threading()
    # unpause
    sp.start_playback(device_id=current_device_id)
    get_album_cover()
    # replace button
    play_button.place_forget()
    pause_button.place(relx=0.7, rely=0.7, anchor=tkinter.CENTER)


def skip_music():
    sp.next_track(device_id=None)
#  -----------------------------------------------------------
# self explainatory TO-DO
def back_music():

    track_info = get_current_track_info()
    
    # test for if the songs in the beginning (or two seconds in)
    if track_info['progress'] > 2000:
        sp.seek_track(0)
        print('Go back to beginning')
    else:
        # go to previous track if it was less than two seconds in
        sp.previous_track()
        print('Go back a track')

#  -----------------------------------------------------------
# self explainatory TO-DO
def vol_slider(value):
    perecent = int(float(value))
    sp.volume(volume_percent=perecent, device_id=current_device_id)


# pause music, and replace with play
def play_pause_music():
    global pause
    pause = True
    sp.pause_playback(device_id=current_device_id)
    pause_button.place_forget()
    play_button.place(relx=0.7, rely=0.7, anchor=tkinter.CENTER)
        

# ------------ GUI components ------------
#           buttons

# Play
play_button = customtkinter.CTkButton(master=root, text='▷', font=("Arial", 44), command=play_music, width=40, height=40)


# Pause
pause_button = customtkinter.CTkButton(master=root, text='‖', font=("Arial", 44), command=play_pause_music, width=40, height=40)
pause_button.place(relx=0.7, rely=0.7, anchor=tkinter.CENTER)

# Skip
skip_button = customtkinter.CTkButton(master=root, text='⇨', font=("Arial", 44), command=skip_music, width=60, height=50)
skip_button.place(relx=0.9, rely=0.7, anchor=tkinter.CENTER)

# Go Back
back_button = customtkinter.CTkButton(master=root, text='⇦', font=("Arial", 44), command=back_music, width=60, height=50)
back_button.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)

# Volume
vol_slider = customtkinter.CTkSlider(master=root, from_=0, to=100, command=vol_slider, width=210)
vol_slider.place(relx=0.7, rely=0.95, anchor=tkinter.CENTER)

# Progress Bar OPTIONAL
progress_bar = customtkinter.CTkProgressBar(master=root, width=150, height=3)
progress_bar.place(relx=0.2, rely=0.92, anchor=tkinter.CENTER)

image_path = "Volume.jpg"
volume_img = Image.open(image_path)


volumePhoto = ImageTk.PhotoImage(volume_img)
volume_text = tkinter.Label(root, image=volumePhoto, borderwidth=0)
volume_text.place(relx=0.5, rely=0.94, anchor=tkinter.CENTER)
volume_text.image = volume_img




def periodic_updates():
    """Update song info periodically"""
    root.after(1000, periodic_updates)  # Update every 1 seconds

# Start periodic updates after authentication
get_active_device()

get_album_cover()

root.after(2000, periodic_updates)  # Start after 2 seconds

# main loop
root.mainloop()