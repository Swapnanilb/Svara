import customtkinter as ctk
from PIL import Image
import os

class IconLoader:
    def __init__(self):
        self.icons = {}
        self.placeholder_img = None
        self.load_icons()

    def load_icons(self):
        """Load all icon images from the icons directory."""
        icon_paths = {
            'play': 'icons/play.png',
            'pause': 'icons/pause.png',
            'next': 'icons/next.png',
            'prev': 'icons/prev.png',
            'fast_fwd': 'icons/fast_fwd.png',
            'fast_rew': 'icons/fast_rew.png',
            'shuffle_off': 'icons/shuffle_off.png',
            'shuffle_on': 'icons/shuffle_on.png',
            'repeat_off': 'icons/repeat_off.png',
            'repeat_on': 'icons/repeat_on.png',
            'volume': 'icons/volume.png',
            'volume_mute': 'icons/volume_mute.png'
        }

        try:
            # Load main control icons
            for icon_name, path in icon_paths.items():
                if os.path.exists(path):
                    if icon_name in ['play', 'pause']:
                        size = (30, 30)
                    else:
                        size = (25, 25)
                    
                    self.icons[icon_name] = ctk.CTkImage(
                        light_image=Image.open(path), 
                        size=size
                    )
                else:
                    print(f"Warning: Icon file not found: {path}")
                    self.icons[icon_name] = None

            # Create placeholder image
            self.placeholder_img = ctk.CTkImage(
                light_image=Image.new("RGB", (50, 50), "gray"), 
                size=(50, 50)
            )

        except Exception as e:
            print(f"Error loading icons: {e}")
            self._create_fallback_icons()

    def _create_fallback_icons(self):
        """Create fallback icons if files are not found."""
        print("Warning: Icon files not found. Using fallback icons.")
        
        # Create simple colored rectangles as fallback
        fallback_color = (100, 100, 100)
        
        for icon_name in self.icons.keys():
            if icon_name in ['play', 'pause']:
                size = (30, 30)
            else:
                size = (25, 25)
                
            fallback_img = Image.new("RGB", size, fallback_color)
            self.icons[icon_name] = ctk.CTkImage(
                light_image=fallback_img, 
                size=size
            )

        # Placeholder image
        self.placeholder_img = ctk.CTkImage(
            light_image=Image.new("RGB", (50, 50), "gray"), 
            size=(50, 50)
        )

    def get_icon(self, icon_name):
        """Get a specific icon by name."""
        return self.icons.get(icon_name)

    def get_all_icons(self):
        """Get all loaded icons as a dictionary."""
        return self.icons.copy()

    def get_placeholder_img(self):
        """Get the placeholder image for thumbnails."""
        return self.placeholder_img

    def icon_exists(self, icon_name):
        """Check if an icon exists and is loaded."""
        return icon_name in self.icons and self.icons[icon_name] is not None