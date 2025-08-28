import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence
import threading
import os
import sys

# We need to import the main app class to instantiate it.
from main import MusicPlayerApp

class SplashScreen(ctk.CTkToplevel):
    def __init__(self, master, next_app_instance):
        super().__init__(master)
        
        self.next_app_instance = next_app_instance
        self.overrideredirect(True)
        
        # Center the splash screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = 500
        height = 300
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.configure(fg_color="#1E1E1E")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.image_path = "logo_animation.gif"  # Your animated GIF file
        self.frames = []
        self.load_frames()
        self.current_frame_index = 0
        
        self.label = ctk.CTkLabel(self, text="", fg_color="transparent")
        self.label.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Start the animation loop
        self.after(0, self.animate_gif)
        
    def load_frames(self):
        try:
            image_object = Image.open(self.image_path)
            for frame in ImageSequence.Iterator(image_object):
                # Ensure the frame is in RGBA format
                rgba_frame = frame.convert('RGBA')
                # Resize the image for display
                resized_frame = rgba_frame.resize((400, 200), Image.Resampling.LANCZOS)
                # We use the master (main app) to create the CTkImage,
                # ensuring it is not garbage collected.
                self.frames.append(ctk.CTkImage(light_image=resized_frame, size=(400, 200)))
        except FileNotFoundError:
            print(f"Error: Animation file not found at {self.image_path}")
            # Fallback to a static image or message
            self.label.configure(text="Music Player", font=ctk.CTkFont(size=24, weight="bold"))
        except Exception as e:
            print(f"Error loading GIF: {e}")
            self.label.configure(text="Music Player", font=ctk.CTkFont(size=24, weight="bold"))

    def animate_gif(self):
        # Check if we have more frames to show
        if self.current_frame_index < len(self.frames):
            self.label.configure(image=self.frames[self.current_frame_index])
            self.current_frame_index += 1
            self.after(50, self.animate_gif) # Adjust delay for speed (50ms = 20fps)
        else:
            # Animation has completed, launch the main app
            self.start_main_app()

    def start_main_app(self):
        self.destroy()
        # FIX: Add a small delay to prevent a race condition
        self.master.after(10, self.next_app_instance.deiconify)
        
if __name__ == "__main__":
    # 1. Instantiate the main application first. This creates the primary Tkinter root window.
    app = MusicPlayerApp()
    
    # 2. Hide the main application window temporarily.
    app.withdraw()
    
    # 3. Create the splash screen as a Toplevel window of the main application.
    # This ensures it closes automatically when the main window closes.
    splash_screen = SplashScreen(app, app)
    
    # 4. Start the main Tkinter event loop. This is a blocking call.
    app.mainloop()