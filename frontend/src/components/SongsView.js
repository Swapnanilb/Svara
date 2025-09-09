import React, { useState, useEffect } from 'react';
import { musicAPI } from '../services/api';

const SongsView = ({ status, onStatusUpdate, theme }) => {
  const [songs, setSongs] = useState([]);
  const [playlistName, setPlaylistName] = useState('');

  useEffect(() => {
    loadCurrentPlaylist();
  }, [status?.current_playlist_id]);

  const loadCurrentPlaylist = async () => {
    if (status?.current_playlist_id) {
      try {
        const response = await musicAPI.getPlaylistSongs(status.current_playlist_id);
        setSongs(response.songs);
        
        const playlists = await musicAPI.getPlaylists();
        const playlist = playlists.playlists[status.current_playlist_id];
        setPlaylistName(playlist?.name || 'Unknown Playlist');
      } catch (error) {
        console.error('Error loading playlist:', error);
      }
    }
  };

  const playSong = async (songIndex) => {
    if (!status?.current_playlist_id) return;
    try {
      await musicAPI.play(status.current_playlist_id, songIndex);
      onStatusUpdate();
    } catch (error) {
      console.error('Error playing song:', error);
    }
  };

  if (!status?.current_playlist_id) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100%', 
        textAlign: 'center' 
      }}>
        <div style={{ fontSize: '48px', marginBottom: '20px', color: '#ff6b35' }}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
          </svg>
        </div>
        <h3 style={{ color: theme === 'dark' ? '#fff' : '#333', marginBottom: '10px' }}>No Playlist Selected</h3>
        <p style={{ color: theme === 'dark' ? '#ccc' : '#999' }}>Select a playlist to view songs</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '30px' }}>
      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '700', color: theme === 'dark' ? '#fff' : '#333', marginBottom: '5px' }}>
          Now Playing
        </h2>
        <p style={{ fontSize: '16px', color: theme === 'dark' ? '#ccc' : '#999', marginBottom: '20px' }}>
          {playlistName}
        </p>
        
        {status?.current_song && (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '15px', 
            padding: '20px', 
            background: 'rgba(255, 107, 53, 0.1)', 
            borderRadius: '15px',
            border: '2px solid rgba(255, 107, 53, 0.2)'
          }}>
            {status.current_song.thumbnail_url && (
              <img 
                src={status.current_song.thumbnail_url} 
                alt="Current song"
                style={{ 
                  width: '60px', 
                  height: '60px', 
                  borderRadius: '10px', 
                  objectFit: 'cover' 
                }}
              />
            )}
            <div>
              <div style={{ fontSize: '16px', fontWeight: '600', color: theme === 'dark' ? '#fff' : '#333', marginBottom: '5px' }}>
                {status.current_song.title}
              </div>
              <div style={{ fontSize: '14px', color: theme === 'dark' ? '#ccc' : '#999' }}>
                {status.is_playing && !status.is_paused ? 'Playing' : 'Paused'}
              </div>
            </div>
          </div>
        )}
      </div>

      <div>
        <h3 style={{ fontSize: '20px', fontWeight: '600', color: theme === 'dark' ? '#fff' : '#333', marginBottom: '20px' }}>
          Tracklist ({songs.length} songs)
        </h3>
        
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {songs.map((song, index) => (
            <div
              key={index}
              onClick={() => playSong(index)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '15px',
                padding: '15px',
                borderRadius: '12px',
                cursor: 'pointer',
                marginBottom: '10px',
                background: status?.current_song_index === index ? 'rgba(255, 107, 53, 0.1)' : (theme === 'dark' ? '#444' : 'white'),
                border: status?.current_song_index === index ? '2px solid rgba(255, 107, 53, 0.3)' : (theme === 'dark' ? '1px solid #555' : '1px solid #e0e0e0'),
                transition: 'all 0.2s ease'
              }}
              className="card-hover"
            >
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '8px',
                background: status?.current_song_index === index ? 'linear-gradient(45deg, #ff6b35, #ff8c42)' : '#f0f2f5',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '14px',
                fontWeight: 'bold',
                color: status?.current_song_index === index ? 'white' : '#999'
              }}>
                {index + 1}
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{ 
                  fontSize: '15px', 
                  fontWeight: '600', 
                  color: theme === 'dark' ? '#fff' : '#333', 
                  marginBottom: '4px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {song.title}
                </div>
                <div style={{ fontSize: '12px', color: theme === 'dark' ? '#ccc' : '#999' }}>
                  {song.duration ? `${Math.floor(song.duration / 60)}:${(song.duration % 60).toString().padStart(2, '0')}` : 'Unknown duration'}
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  playSong(index);
                }}
                className="btn-orange"
                style={{ 
                  padding: '8px 12px', 
                  fontSize: '12px',
                  minWidth: 'auto',
                  borderRadius: '8px'
                }}
              >
                ▶
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SongsView;