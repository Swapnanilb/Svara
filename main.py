from music_player_ui import MusicPlayerUI
from music_player_logic import MusicPlayerLogic
import customtkinter as ctk
from PIL import Image, ImageSequence


class SplashScreen(ctk.CTkToplevel):
    def __init__(self, master, gif_path="logo_animation.gif", delay=4000, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.delay = delay
        self.frames = []
        self.animation_job = None
        self.fade_job = None
        self.master = master

        # Load GIF frames
        gif = Image.open(gif_path)
        for frame in ImageSequence.Iterator(gif):
            frame = frame.copy().convert("RGBA")
            ctk_img = ctk.CTkImage(light_image=frame, dark_image=frame, size=gif.size)
            self.frames.append(ctk_img)

        self.label = ctk.CTkLabel(self, text="")
        self.label.pack(fill="both", expand=True)

        # Window setup
        self.overrideredirect(True)
        self.configure(fg_color="black")

        # Center window
        self.update_idletasks()
        w, h = gif.size
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Start animation
        self.play_animation()
        self.after(self.delay, self.start_fade_out)

    def play_animation(self, ind=0):
        if not self.winfo_exists():
            return
        frame = self.frames[ind]
        self.label.configure(image=frame)
        ind = (ind + 1) % len(self.frames)
        self.animation_job = self.after(50, self.play_animation, ind)

    def start_fade_out(self, alpha=1.0):
        if alpha <= 0:
            self.close_splash()
            return
        self.attributes("-alpha", alpha)
        self.fade_job = self.after(50, self.start_fade_out, alpha - 0.1)

    def close_splash(self):
        # cancel jobs
        for job in (self.animation_job, self.fade_job):
            if job:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
        if self.winfo_exists():
            self.destroy()
        # Show main window now
        self.master.deiconify()


class MusicPlayerApp:
    def __init__(self):
        # Create the UI component (this is your CTk root)
        self.ui = MusicPlayerUI()

        # Create the logic component
        self.logic = MusicPlayerLogic(self.ui)

        # Connect UI and logic
        self.ui.set_logic(self.logic)

        # Set up close handler
        self.ui.protocol("WM_DELETE_WINDOW", self.ui.on_close)

    def mainloop(self):
        self.ui.mainloop()


if __name__ == "__main__":
    # Create the app (this makes one CTk root)
    app = MusicPlayerApp()

    # Hide it until splash is done
    app.ui.withdraw()

    # Show splash attached to this root
    splash = SplashScreen(app.ui, "logo_animation.gif", delay=4000)

    # Run mainloop once (only one root!)
    app.mainloop()
