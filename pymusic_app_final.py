import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
from tkinter.font import Font as tkFont
import pandas as pd
import vlc
import yt_dlp
import requests
import os
import threading

# --- Helper functions (remain unchanged) ---
def get_youtube_stream(query, is_url=False):
    ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'default_search': 'ytsearch', 'quiet': True, 'no_warnings': True}
    search_term = query if is_url else f"ytsearch:{query}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(search_term, download=False)
            video_info = info['entries'][0] if '_type' in info and info['_type'] == 'playlist' else info
            return {'title': video_info.get('title', 'Unknown Title'), 'stream_url': video_info.get('url'), 'original_url': video_info.get('webpage_url', query), 'duration': video_info.get('duration', 0)}
        except Exception as e:
            print(f"yt-dlp error: {e}")
            return None

def format_time(milliseconds):
    if not isinstance(milliseconds, (int, float)) or milliseconds < 0: return "0:00"
    seconds = int(milliseconds / 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"

# --- Main Application Class ---
class MusicPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title('PyMu6 (Spotify Black Edition)')
        self.root.geometry('1280x720')
        self.root.minsize(960, 640)

        # --- Color and Font Definitions ---
        self.BG_COLOR = "#191414"
        self.FRAME_COLOR = "#191414"
        self.TEXT_COLOR = "#FFFFFF"
        self.SUB_TEXT_COLOR = "#b3b3b3"
        self.ACCENT_COLOR = "#1DB954"
        self.WIDGET_BG_COLOR = "#282828"
        self.LISTBOX_BG_COLOR = "#191414" # Changed to match the main background
        
        self.title_font = tkFont(family='Segoe UI', size=14, weight='bold')
        self.widget_font = tkFont(family='Segoe UI', size=10)
        self.small_font = tkFont(family='Segoe UI', size=9)

        self.root.configure(bg=self.BG_COLOR)
        self.root.columnconfigure(0, weight=3); self.root.columnconfigure(1, weight=1); self.root.rowconfigure(0, weight=1)

        try:
            asset_dir = os.path.join(os.path.dirname(__file__), 'assets')
            self.pymus_img = PhotoImage(file=os.path.join(asset_dir, 'PyMu6.png'))
            self.like_img = PhotoImage(file=os.path.join(asset_dir, 'heart (1).png'))
            self.liked_songs_img = PhotoImage(file=os.path.join(asset_dir, 'Liked Songs.png'))
            self.volume_img = PhotoImage(file=os.path.join(asset_dir, 'smolmic.png'))
        except tk.TclError:
            messagebox.showerror("Asset Error", "Could not find 'assets' folder or image files.")
            self.root.destroy()
            return
        
        self.vlc_instance = vlc.Instance("--no-xlib")
        self.player = self.vlc_instance.media_player_new()
        self.player.audio_set_volume(80)
        self.current_media_title = None; self.current_original_url = None; self.is_seeking = False; self.title_animation_job = None
        
        self.liked_songs_file = 'LikedSongs1.csv'
        self.initialize_csv()
        self.create_styles()
        self.create_widgets()
        self.load_liked_songs()
        self.update_progress()
        self.check_internet()

    def create_styles(self):
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        self.style.configure("green.Horizontal.TScale", background=self.FRAME_COLOR, troughcolor="#404040", sliderrelief='flat', troughrelief='flat', borderwidth=0)
        self.style.map("green.Horizontal.TScale", background=[('active', self.ACCENT_COLOR), ('!active', self.SUB_TEXT_COLOR)])
        
    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg=self.FRAME_COLOR)
        main_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        header_frame = tk.Frame(main_frame, bg=self.FRAME_COLOR)
        header_frame.grid(row=0, column=0, pady=(10, 20), sticky='w')
        tk.Label(header_frame, image=self.pymus_img, bg=self.FRAME_COLOR).pack(side='left')

        search_frame = tk.Frame(main_frame, bg=self.FRAME_COLOR)
        search_frame.grid(row=1, column=0, pady=10, sticky='ew')
        search_frame.columnconfigure(0, weight=1)
        self.search_entry = tk.Entry(search_frame, borderwidth=0, relief='flat', insertbackground=self.TEXT_COLOR, bg=self.WIDGET_BG_COLOR, fg=self.TEXT_COLOR, font=('Segoe UI', 12))
        self.search_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10), ipady=6)
        self.search_entry.bind("<Return>", self.search_and_play_threaded)
        search_button = tk.Button(search_frame, text='Search', bg=self.ACCENT_COLOR, fg='black', font=('Segoe UI', 10, 'bold'), relief='flat', command=self.search_and_play_threaded)
        search_button.grid(row=0, column=1, ipady=4, ipadx=15)

        self.now_playing_canvas = tk.Canvas(main_frame, bg=self.FRAME_COLOR, highlightthickness=0)
        self.now_playing_canvas.grid(row=2, column=0, sticky='nsew')
        self.now_playing_text_item = self.now_playing_canvas.create_text(0, 0, text="Welcome to PyMu6", font=self.title_font, fill=self.TEXT_COLOR, anchor='center')
        self.now_playing_canvas.bind("<Configure>", lambda e: self.center_now_playing_text())

        playback_frame = tk.Frame(main_frame, bg=self.FRAME_COLOR)
        playback_frame.grid(row=3, column=0, sticky='ew')
        playback_frame.columnconfigure(0, weight=1)

        progress_frame = tk.Frame(playback_frame, bg=self.FRAME_COLOR)
        progress_frame.grid(row=0, column=0, sticky='ew', pady=(5,0))
        progress_frame.columnconfigure(1, weight=1)
        self.current_time_var = tk.StringVar(value="0:00")
        self.total_time_var = tk.StringVar(value="0:00")
        tk.Label(progress_frame, textvariable=self.current_time_var, bg=self.FRAME_COLOR, fg=self.SUB_TEXT_COLOR, font=self.small_font).grid(row=0, column=0, padx=(0,10))
        self.progress_bar = ttk.Scale(progress_frame, from_=0, to=100, orient='horizontal', style="green.Horizontal.TScale", command=self.on_seek_drag)
        self.progress_bar.bind("<ButtonPress-1>", lambda e: self.set_seeking(True))
        self.progress_bar.bind("<ButtonRelease-1>", lambda e: self.on_seek_release(e))
        self.progress_bar.grid(row=0, column=1, sticky='ew')
        tk.Label(progress_frame, textvariable=self.total_time_var, bg=self.FRAME_COLOR, fg=self.SUB_TEXT_COLOR, font=self.small_font).grid(row=0, column=2, padx=(10,0))
        
        controls_frame = tk.Frame(playback_frame, bg=self.FRAME_COLOR)
        controls_frame.grid(row=1, column=0, sticky='ew', pady=(5, 20))
        controls_frame.columnconfigure(0, weight=1); controls_frame.columnconfigure(1, weight=0); controls_frame.columnconfigure(2, weight=1)
        like_btn = tk.Button(controls_frame, image=self.like_img, bg=self.FRAME_COLOR, relief='flat', bd=0, activebackground=self.FRAME_COLOR, command=self.add_to_liked)
        like_btn.grid(row=0, column=0, sticky='w', padx=20)
        center_buttons_frame = tk.Frame(controls_frame, bg=self.FRAME_COLOR)
        center_buttons_frame.grid(row=0, column=1)
        play_pause_button = tk.Button(center_buttons_frame, text='▶  ❚❚', bg=self.ACCENT_COLOR, fg='black', width=10, font=('Segoe UI', 12, 'bold'), relief='flat', command=self.pause_music)
        play_pause_button.pack(side='left', padx=10)
        stop_button = tk.Button(center_buttons_frame, text='■', fg=self.TEXT_COLOR, bg=self.WIDGET_BG_COLOR, width=5, font=('Segoe UI', 12, 'bold'), relief='flat', command=self.stop_music)
        stop_button.pack(side='left', padx=10)
        volume_frame = tk.Frame(controls_frame, bg=self.FRAME_COLOR)
        volume_frame.grid(row=0, column=2, sticky='e', padx=20)
        tk.Label(volume_frame, image=self.volume_img, bg=self.FRAME_COLOR).pack(side='left')
        self.volume_slider = ttk.Scale(volume_frame, from_=0, to=100, orient='horizontal', style="green.Horizontal.TScale", command=self.on_volume_change)
        self.volume_slider.set(80)
        self.volume_slider.pack(side='left')

        sidebar_frame = tk.Frame(self.root, bg=self.FRAME_COLOR)
        sidebar_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 20), pady=10)
        sidebar_frame.rowconfigure(1, weight=1); sidebar_frame.columnconfigure(0, weight=1)
        tk.Label(sidebar_frame, image=self.liked_songs_img, bg=self.FRAME_COLOR).grid(row=0, column=0, pady=(10, 5), sticky='w')
        self.liked_songs_listbox = tk.Listbox(sidebar_frame, bg=self.LISTBOX_BG_COLOR, fg=self.SUB_TEXT_COLOR, selectbackground=self.WIDGET_BG_COLOR, relief='flat', borderwidth=0, highlightthickness=0, font=self.widget_font, selectborderwidth=0)
        self.liked_songs_listbox.grid(row=1, column=0, sticky='nsew', pady=5)
        self.liked_songs_listbox.bind("<Double-Button-1>", self.play_liked_song_threaded)
        
    def initialize_csv(self):
        if not os.path.exists(self.liked_songs_file): pd.DataFrame(columns=['Title', 'URL']).to_csv(self.liked_songs_file, index=False)
    def on_volume_change(self, value): self.player.audio_set_volume(int(float(value)))
    def search_and_play_threaded(self, event=None):
        query = self.search_entry.get()
        if not query: return
        threading.Thread(target=self._search_and_play_task, args=(query,), daemon=True).start()
    def _search_and_play_task(self, query):
        self.root.after(0, self.setup_title_display, f"Searching for '{query}'...")
        song_data = get_youtube_stream(query)
        if song_data and song_data['stream_url']: self.root.after(0, self.play_media, song_data)
        else: self.root.after(0, self.show_search_error, query)
    def play_liked_song_threaded(self, event=None):
        selected_indices = self.liked_songs_listbox.curselection()
        if not selected_indices: return
        threading.Thread(target=self._play_liked_song_task, args=(selected_indices[0],), daemon=True).start()
    def _play_liked_song_task(self, selected_index):
        try:
            song_url = self.liked_songs_df.iloc[selected_index]['URL']
            self.root.after(0, self.setup_title_display, "Loading liked song...")
            song_data = get_youtube_stream(song_url, is_url=True)
            if song_data and song_data['stream_url']: self.root.after(0, self.play_media, song_data)
        except Exception as e: self.root.after(0, messagebox.showerror, "Error", f"Could not play liked song.\n{e}")
    def check_internet(self): threading.Thread(target=self._check_internet_task, daemon=True).start()
    def _check_internet_task(self):
        try: requests.get("https://www.google.com", timeout=5)
        except requests.ConnectionError: self.root.after(0, messagebox.showwarning, "No Internet", "You are not connected to the internet.")
    def show_search_error(self, query):
        self.stop_title_animation()
        messagebox.showerror("Error", f"Could not find any results for '{query}'.")
    def play_media(self, song_data):
        self.setup_title_display(song_data['title'])
        self.current_media_title = song_data['title']
        self.current_original_url = song_data['original_url']
        media = self.vlc_instance.media_new(song_data['stream_url'])
        self.player.set_media(media)
        self.player.play()
        self.total_time_var.set(format_time(song_data['duration'] * 1000))
        self.progress_bar.config(to=song_data['duration'])
    def center_now_playing_text(self):
        if not self.title_animation_job: self.now_playing_canvas.coords(self.now_playing_text_item, self.now_playing_canvas.winfo_width() / 2, self.now_playing_canvas.winfo_height() / 2)
    def setup_title_display(self, title):
        if self.title_animation_job: self.root.after_cancel(self.title_animation_job); self.title_animation_job = None
        canvas_width = self.now_playing_canvas.winfo_width(); canvas_height = self.now_playing_canvas.winfo_height(); text_width = self.title_font.measure(title)
        self.now_playing_canvas.delete(self.now_playing_text_item)
        if text_width > canvas_width:
            self.now_playing_text_item = self.now_playing_canvas.create_text(canvas_width, canvas_height / 2, text=f"    {title}    ", font=self.title_font, fill=self.TEXT_COLOR, anchor='w')
            self.animate_title()
        else:
            self.now_playing_text_item = self.now_playing_canvas.create_text(canvas_width / 2, canvas_height / 2, text=title, font=self.title_font, fill=self.TEXT_COLOR, anchor='center')
    def animate_title(self):
        x1, _, x2, _ = self.now_playing_canvas.bbox(self.now_playing_text_item)
        if x2 < 0: self.now_playing_canvas.coords(self.now_playing_text_item, self.now_playing_canvas.winfo_width(), self.now_playing_canvas.winfo_height() / 2)
        else: self.now_playing_canvas.move(self.now_playing_text_item, -1, 0)
        self.title_animation_job = self.root.after(25, self.animate_title)
    def stop_title_animation(self):
        if self.title_animation_job: self.root.after_cancel(self.title_animation_job); self.title_animation_job = None
        self.setup_title_display("Nothing is playing")
    def stop_music(self):
        if self.player.get_media(): self.player.stop()
        self.stop_title_animation()
        self.current_time_var.set("0:00"); self.total_time_var.set("0:00"); self.progress_bar.set(0)
        self.current_media_title = None; self.current_original_url = None
    def pause_music(self):
        if self.player.get_media(): self.player.pause()
    def update_progress(self):
        if self.player.is_playing() and not self.is_seeking:
            current_time_ms = self.player.get_time()
            self.progress_bar.set(current_time_ms / 1000)
            self.current_time_var.set(format_time(current_time_ms))
        self.root.after(500, self.update_progress)
    def add_to_liked(self):
        if not self.current_original_url or not self.current_media_title: messagebox.showinfo("Nothing to Like", "Play a song first."); return
        try:
            df = pd.read_csv(self.liked_songs_file)
            if self.current_original_url in df['URL'].values: messagebox.showinfo("Already Liked", "This song is already in your liked list."); return
            new_song = pd.DataFrame([{'Title': self.current_media_title, 'URL': self.current_original_url}])
            df = pd.concat([df, new_song], ignore_index=True)
            df.to_csv(self.liked_songs_file, index=False)
            messagebox.showinfo("Success", "Added to liked songs!")
            self.load_liked_songs()
        except Exception as e: messagebox.showerror("CSV Error", f"Could not save liked song.\n{e}")
    def load_liked_songs(self):
        self.liked_songs_listbox.delete(0, tk.END)
        try:
            self.liked_songs_df = pd.read_csv(self.liked_songs_file)
            for _, row in self.liked_songs_df.iterrows(): self.liked_songs_listbox.insert(tk.END, row['Title'])
        except (FileNotFoundError, pd.errors.EmptyDataError): pass
    def set_seeking(self, seeking): self.is_seeking = seeking
    def on_seek_drag(self, value):
        if self.player.get_media() and self.is_seeking: self.current_time_var.set(format_time(float(value) * 1000))
    def on_seek_release(self, event):
        if self.player.get_media(): self.player.set_time(int(self.progress_bar.get() * 1000))
        self.set_seeking(False)

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayerApp(root)
    root.mainloop()
