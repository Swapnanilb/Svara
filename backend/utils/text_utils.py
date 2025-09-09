import re

class TextUtils:
    def __init__(self):
        pass

    def clean_song_title(self, title: str) -> str:
        """
        Return a cleaned song title with minimal processing.
        
        Args:
            title: Original song title from YouTube
            
        Returns:
            Cleaned title string
        """
        if not title:
            return "Unknown Title"
            
        # Remove text inside () or [] like (Official Video), [Lyric]
        cleaned = re.sub(r"[\(\[].*?[\)\]]", "", title)
        
        # Split by common separators
        parts = re.split(r"[|\-–—]", cleaned)
        
        # Find the best part (usually song name comes before artist)
        best_part = parts[0].strip()
        
        # If first part looks like an artist name (short, single word), try next part
        if len(parts) > 1 and (len(best_part.split()) <= 2 or len(best_part) < 10):
            second_part = parts[1].strip()
            if len(second_part) > len(best_part):
                best_part = second_part
        
        cleaned = best_part
        
        # Remove common keywords
        keywords = ["official", "video", "lyrics", "lyrical", "audio", "full song"]
        pattern = r"\s*\b(" + "|".join(keywords) + r")\b\s*"
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        
        # Truncate if too long
        if len(cleaned) > 50:
            cleaned = cleaned[:47] + "..."
        
        return cleaned if cleaned else "Unknown Title"

    def truncate_text(self, text: str, max_length: int, ellipsis: str = "...") -> str:
        """
        Truncate text to specified length with ellipsis.
        
        Args:
            text: Text to truncate
            max_length: Maximum length including ellipsis
            ellipsis: String to append when truncating
            
        Returns:
            Truncated text string
        """
        if not text or len(text) <= max_length:
            return text
            
        return text[:max_length - len(ellipsis)] + ellipsis

    def format_duration(self, seconds: int) -> str:
        """
        Format duration in seconds to MM:SS format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string (MM:SS)
        """
        if seconds < 0:
            return "0:00"
            
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def format_duration_long(self, seconds: int) -> str:
        """
        Format duration in seconds to H:MM:SS format for long durations.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string (H:MM:SS or MM:SS)
        """
        if seconds < 0:
            return "0:00"
            
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename string
        """
        # Remove or replace invalid characters for filenames
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', filename)
        
        # Remove extra whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Limit length
        max_length = 255
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rsplit(' ', 1)[0]
            
        return sanitized if sanitized else "unnamed"

    def extract_video_id_from_url(self, url: str) -> str:
        """
        Extract video ID from various YouTube URL formats.
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID string or empty string if not found
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
                
        return ""

    def extract_playlist_id_from_url(self, url: str) -> str:
        """
        Extract playlist ID from YouTube URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Playlist ID string or empty string if not found
        """
        pattern = r'[&?]list=([^&\n?#]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else ""

    def is_youtube_url(self, url: str) -> bool:
        """
        Check if URL is a valid YouTube URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if valid YouTube URL, False otherwise
        """
        youtube_patterns = [
            r'(?:youtube\.com|youtu\.be)',
            r'youtube\.com/watch',
            r'youtube\.com/playlist'
        ]
        
        return any(re.search(pattern, url) for pattern in youtube_patterns)

    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text (remove extra spaces, tabs, newlines).
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text string
        """
        if not text:
            return ""
            
        # Replace multiple whitespace characters with single space
        normalized = re.sub(r'\s+', ' ', text)
        
        # Strip leading and trailing whitespace
        return normalized.strip()