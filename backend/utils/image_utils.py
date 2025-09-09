import customtkinter as ctk
from PIL import Image
import urllib.request
import io

class ImageUtils:
    def __init__(self):
        pass

    def get_image_from_path_or_url(self, source, size=(100, 100)):
        """
        Helper function to load an image from a local path or a URL.
        
        Args:
            source: Local file path, URL, or None
            size: Tuple of (width, height) for the output image
            
        Returns:
            CTkImage object
        """
        img = None
        
        if source:
            try:
                if source.startswith(('http://', 'https://')):
                    # Load from URL
                    with urllib.request.urlopen(source) as url:
                        raw_data = url.read()
                    pil_img = Image.open(io.BytesIO(raw_data)).resize(size)
                else:
                    # Load from local path
                    pil_img = Image.open(source).resize(size)
                
                img = ctk.CTkImage(light_image=pil_img, size=size)
                
            except Exception as e:
                print(f"Could not load image from {source}: {e}")
                img = self._create_placeholder_image(size)
        else:
            # No source provided, create placeholder
            img = self._create_placeholder_image(size)
            
        return img

    def _create_placeholder_image(self, size=(100, 100)):
        """Create a placeholder image when loading fails or no source is provided."""
        placeholder_pil = Image.new("RGB", size, color=(64, 64, 64))  # Dark gray
        return ctk.CTkImage(light_image=placeholder_pil, size=size)

    def resize_image(self, image_path, size):
        """
        Resize an image from a file path.
        
        Args:
            image_path: Path to the image file
            size: Tuple of (width, height)
            
        Returns:
            CTkImage object or None if failed
        """
        try:
            pil_img = Image.open(image_path).resize(size)
            return ctk.CTkImage(light_image=pil_img, size=size)
        except Exception as e:
            print(f"Could not resize image {image_path}: {e}")
            return self._create_placeholder_image(size)

    def create_thumbnail(self, source, size=(50, 50)):
        """
        Create a thumbnail image from a source.
        
        Args:
            source: Image source (path or URL)
            size: Thumbnail size tuple
            
        Returns:
            CTkImage object
        """
        return self.get_image_from_path_or_url(source, size)

    def validate_image_file(self, file_path):
        """
        Validate if a file is a valid image.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if valid image, False otherwise
        """
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def get_supported_formats(self):
        """Get list of supported image formats."""
        return [
            ("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg;*.jpeg"),
            ("GIF files", "*.gif"),
            ("BMP files", "*.bmp"),
            ("WebP files", "*.webp"),
            ("All files", "*.*")
        ]