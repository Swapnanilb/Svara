import re

class TextUtils:
    def clean_song_title(self, title: str) -> str:
        """Return a simplified song title (remove artist/extra text)."""
        if not title:
            return ""
        
        # Remove common patterns like "- Artist", "(Official Video)", etc.
        cleaned = re.sub(r'\s*-\s*.*$', '', title)
        cleaned = re.sub(r'\s*\(.*?\)', '', cleaned)
        cleaned = re.sub(r'\s*\[.*?\]', '', cleaned)
        
        return cleaned.strip()