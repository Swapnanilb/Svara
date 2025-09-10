import json
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional

class PerformanceLogger:
    def __init__(self, log_file="performance_metrics.log"):
        self.log_file = log_file
        self.session_start = time.time()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metrics = {}
        self._log_startup()
    
    def _log_startup(self):
        """Log application startup"""
        self._write_log({
            "event": "app_startup",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "startup_time": time.time()
        })
    
    def log_playlist_load(self, playlist_id: str, song_count: int, load_time: float, cached_songs: int = 0):
        """Log playlist loading metrics"""
        self._write_log({
            "event": "playlist_load",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "playlist_id": playlist_id,
            "song_count": song_count,
            "load_time_ms": round(load_time * 1000, 2),
            "cached_songs": cached_songs,
            "cache_hit_rate": round((cached_songs / song_count * 100), 2) if song_count > 0 else 0
        })
    
    def log_song_load(self, video_id: str, title: str, load_time: float, from_cache: bool = False):
        """Log individual song loading metrics"""
        self._write_log({
            "event": "song_load",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "video_id": video_id,
            "title": title,
            "load_time_ms": round(load_time * 1000, 2),
            "from_cache": from_cache,
            "source": "cache" if from_cache else "youtube_api"
        })
    
    def log_playlist_refresh(self, playlist_id: str, added: int, removed: int, total_songs: int, refresh_time: float):
        """Log playlist refresh operations"""
        self._write_log({
            "event": "playlist_refresh",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "playlist_id": playlist_id,
            "songs_added": added,
            "songs_removed": removed,
            "total_songs": total_songs,
            "refresh_time_ms": round(refresh_time * 1000, 2),
            "sync_efficiency": round(((total_songs - added - removed) / total_songs * 100), 2) if total_songs > 0 else 0
        })
    
    def log_cache_operation(self, operation: str, video_ids: list, cache_hits: int, cache_misses: int):
        """Log caching operations"""
        total_requests = len(video_ids)
        self._write_log({
            "event": "cache_operation",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "total_requests": total_requests,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "hit_rate": round((cache_hits / total_requests * 100), 2) if total_requests > 0 else 0,
            "video_ids": video_ids[:5]  # Log first 5 IDs only
        })
    
    def log_preload_operation(self, video_ids: list, preload_time: float, success_count: int):
        """Log preloading operations"""
        self._write_log({
            "event": "preload_operation",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "requested_count": len(video_ids),
            "success_count": success_count,
            "preload_time_ms": round(preload_time * 1000, 2),
            "success_rate": round((success_count / len(video_ids) * 100), 2) if video_ids else 0,
            "video_ids": video_ids
        })
    
    def log_api_request(self, endpoint: str, method: str, response_time: float, status_code: int = 200):
        """Log API request metrics"""
        self._write_log({
            "event": "api_request",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "response_time_ms": round(response_time * 1000, 2),
            "status_code": status_code
        })
    
    def log_cache_stats(self):
        """Log current cache statistics"""
        url_cache_size = 0
        metadata_cache_size = 0
        
        try:
            if os.path.exists("song_url_cache.json"):
                with open("song_url_cache.json", 'r') as f:
                    url_cache = json.load(f)
                    url_cache_size = len(url_cache)
            
            if os.path.exists("song_metadata_cache.json"):
                with open("song_metadata_cache.json", 'r') as f:
                    metadata_cache = json.load(f)
                    metadata_cache_size = len(metadata_cache)
        except:
            pass
        
        self._write_log({
            "event": "cache_stats",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "url_cache_size": url_cache_size,
            "metadata_cache_size": metadata_cache_size,
            "total_cached_items": url_cache_size + metadata_cache_size
        })
    
    def log_app_shutdown(self):
        """Log application shutdown"""
        session_duration = time.time() - self.session_start
        self._write_log({
            "event": "app_shutdown",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "session_duration_seconds": round(session_duration, 2),
            "session_duration_minutes": round(session_duration / 60, 2)
        })
    
    def _write_log(self, log_entry: Dict[str, Any]):
        """Write log entry to file in readable format with color indicators"""
        try:
            timestamp = log_entry.get('timestamp', '').replace('T', ' ').split('.')[0]
            event = log_entry.get('event', 'unknown')
            session = log_entry.get('session_id', 'unknown')
            
            # Color indicators for different event types
            color_map = {
                'app_startup': '🟢',
                'app_shutdown': '🔴', 
                'api_request': '🟡',
                'cache_stats': '🔵',
                'playlist_load': '🟣',
                'song_load': '🟠',
                'playlist_refresh': '🔄',
                'cache_operation': '💾',
                'preload_operation': '⚡'
            }
            
            indicator = color_map.get(event, '⚪')
            
            # Format based on event type
            if event == 'app_startup':
                line = f"{indicator} [{timestamp}] SESSION START - {session}"
            elif event == 'app_shutdown':
                duration = log_entry.get('session_duration_minutes', 0)
                line = f"{indicator} [{timestamp}] SESSION END - Duration: {duration:.1f}min"
            elif event == 'api_request':
                endpoint = log_entry.get('endpoint', '')
                method = log_entry.get('method', '')
                response_time = log_entry.get('response_time_ms', 0)
                status = log_entry.get('status_code', 200)
                status_icon = '✅' if status == 200 else '❌'
                line = f"{indicator} [{timestamp}] API {method} {endpoint} - {response_time}ms {status_icon}HTTP {status}"
            elif event == 'cache_stats':
                url_cache = log_entry.get('url_cache_size', 0)
                meta_cache = log_entry.get('metadata_cache_size', 0)
                total = log_entry.get('total_cached_items', 0)
                line = f"{indicator} [{timestamp}] CACHE - URLs: {url_cache}, Metadata: {meta_cache}, Total: {total}"
            elif event == 'playlist_load':
                playlist_id = log_entry.get('playlist_id', '')
                song_count = log_entry.get('song_count', 0)
                load_time = log_entry.get('load_time_ms', 0)
                hit_rate = log_entry.get('cache_hit_rate', 0)
                perf_icon = '🚀' if load_time < 100 else '⏱️' if load_time < 500 else '🐌'
                line = f"{indicator} [{timestamp}] PLAYLIST LOAD - {playlist_id} ({song_count} songs, {load_time}ms, {hit_rate}% cached) {perf_icon}"
            elif event == 'song_load':
                title = log_entry.get('title', 'Unknown')
                load_time = log_entry.get('load_time_ms', 0)
                source = log_entry.get('source', 'unknown')
                source_icon = '💨' if source == 'cache' else '🌐'
                perf_icon = '🚀' if load_time < 1000 else '⏱️' if load_time < 3000 else '🐌'
                line = f"{indicator} [{timestamp}] SONG LOAD - {title} ({load_time}ms from {source}) {source_icon}{perf_icon}"
            elif event == 'playlist_refresh':
                playlist_id = log_entry.get('playlist_id', '')
                added = log_entry.get('songs_added', 0)
                removed = log_entry.get('songs_removed', 0)
                refresh_time = log_entry.get('refresh_time_ms', 0)
                change_icon = '📈' if added > 0 else '📉' if removed > 0 else '➖'
                line = f"{indicator} [{timestamp}] PLAYLIST REFRESH - {playlist_id} (+{added}/-{removed} songs, {refresh_time}ms) {change_icon}"
            elif event == 'cache_operation':
                operation = log_entry.get('operation', '')
                total_requests = log_entry.get('total_requests', 0)
                cache_hits = log_entry.get('cache_hits', 0)
                cache_misses = log_entry.get('cache_misses', 0)
                hit_rate = log_entry.get('hit_rate', 0)
                video_ids = log_entry.get('video_ids', [])
                efficiency_icon = '💎' if hit_rate == 100 else '⚡' if hit_rate > 80 else '🔄'
                line = f"{indicator} [{timestamp}] CACHE_OPERATION - operation: {operation}, total_requests: {total_requests}, cache_hits: {cache_hits}, cache_misses: {cache_misses}, hit_rate: {hit_rate}, video_ids: {video_ids} {efficiency_icon}"
            elif event == 'preload_operation':
                requested_count = log_entry.get('requested_count', 0)
                success_count = log_entry.get('success_count', 0)
                preload_time = log_entry.get('preload_time_ms', 0)
                success_rate = log_entry.get('success_rate', 0)
                video_ids = log_entry.get('video_ids', [])
                success_icon = '✨' if success_rate > 80 else '⚠️' if success_rate > 50 else '❌'
                line = f"{indicator} [{timestamp}] PRELOAD_OPERATION - requested_count: {requested_count}, success_count: {success_count}, preload_time_ms: {preload_time}, success_rate: {success_rate}, video_ids: {video_ids} {success_icon}"
            else:
                # Fallback for other events
                details = ', '.join([f"{k}: {v}" for k, v in log_entry.items() if k not in ['timestamp', 'event', 'session_id']])
                line = f"{indicator} [{timestamp}] {event.upper()} - {details}"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        except Exception as e:
            print(f"Failed to write log: {e}")

# Global logger instance
perf_logger = PerformanceLogger()