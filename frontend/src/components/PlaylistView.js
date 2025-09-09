import React, { useState, useEffect } from 'react';
import { musicAPI } from '../services/api';

const PlaylistView = ({ onStatusUpdate, theme, onPlaylistSelect, onShowOverlay }) => {
  const [playlists, setPlaylists] = useState({});
  const [selectedPlaylist, setSelectedPlaylist] = useState(null);
  const [songs, setSongs] = useState([]);
  const [refreshingPlaylist, setRefreshingPlaylist] = useState(null);
  const [refreshingAll, setRefreshingAll] = useState(false);
  const [showRefreshOverlay, setShowRefreshOverlay] = useState(false);


  useEffect(() => {
    loadPlaylists();
  }, []);

  const loadPlaylists = async () => { const response = await musicAPI.getPlaylists(); setPlaylists(response.playlists); };
  const selectPlaylist = async (playlistId) => {
    try {
      await musicAPI.loadPlaylist(playlistId);
      setSelectedPlaylist(playlistId);
      onStatusUpdate();
      if (onPlaylistSelect) {
        onPlaylistSelect();
      }
    } catch (error) {
      console.log('Error loading playlist:', error);
    }
  };

  const playPlaylist = async (playlistId, e) => {
    e.stopPropagation();
    try {
      await musicAPI.play(playlistId, 0);
      onStatusUpdate();
    } catch (error) {
      console.log('Play request sent, checking status...');
    }
  };

  const refreshPlaylist = async (playlistId, e) => {
    e.stopPropagation();
    const playlist = playlists[playlistId];
    if (!playlist?.source_url) return;
    
    setRefreshingPlaylist(playlistId);
    onShowOverlay(true);
    try {
      await musicAPI.refreshPlaylist(playlistId, playlist.source_url);
      // Wait a bit for backend processing
      await new Promise(resolve => setTimeout(resolve, 2000));
      await loadPlaylists();
      onShowOverlay(false);
      setTimeout(() => setRefreshingPlaylist(null), 1000);
    } catch (error) {
      console.log('Error refreshing playlist:', error);
      setRefreshingPlaylist(null);
      onShowOverlay(false);
    }
  };

  const refreshAllPlaylists = async () => {
    setRefreshingAll(true);
    try {
      await loadPlaylists();
      // Show success feedback briefly
      setTimeout(() => setRefreshingAll(false), 1000);
    } catch (error) {
      console.log('Error refreshing playlists:', error);
      setRefreshingAll(false);
    }
  };
  const playSong = async (songIndex) => { 
    if (!selectedPlaylist) return; 
    try {
      await musicAPI.play(selectedPlaylist, songIndex); 
    } catch (error) {
      console.log('Play request sent, checking status...'); 
    }
    onStatusUpdate(); 
  };


  return (
    <>
      <div style={{ padding: '30px' }}>
      {/* Playlists List */}
      <div style={{ marginBottom: '40px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '25px' }}>
          <h3 style={{ margin: 0, fontSize: '24px', fontWeight: '700', color: theme === 'dark' ? '#fff' : '#333' }}>Your Playlists</h3>
          <button
            onClick={refreshAllPlaylists}
            disabled={refreshingAll}
            style={{
              background: refreshingAll ? '#ccc' : 'linear-gradient(45deg, #ff6b35, #f7931e)',
              border: 'none',
              borderRadius: '12px',
              padding: '10px 16px',
              color: 'white',
              fontSize: '14px',
              fontWeight: '600',
              cursor: refreshingAll ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => !refreshingAll && (e.target.style.transform = 'scale(1.05)')}
            onMouseLeave={(e) => !refreshingAll && (e.target.style.transform = 'scale(1)')}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ animation: refreshingAll ? 'spin 1s linear infinite' : 'none' }}>
              <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
            </svg>
            {refreshingAll ? 'Refreshing...' : 'Refresh All'}
          </button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
          {Object.entries(playlists).map(([id, playlist]) => (
            <div
              key={id}
              onClick={() => selectPlaylist(id)}
              className="card-hover"
              style={{
                ...playlistCardStyle,
                background: selectedPlaylist === id 
                  ? (theme === 'dark' ? 'linear-gradient(135deg, rgba(255, 107, 53, 0.2), rgba(247, 147, 30, 0.1))' : 'linear-gradient(135deg, rgba(255, 107, 53, 0.1), rgba(247, 147, 30, 0.05))')
                  : (theme === 'dark' ? 'linear-gradient(135deg, #2a2a2a, #1f1f1f)' : 'linear-gradient(135deg, #ffffff, #f8f9fa)'),
                border: selectedPlaylist === id 
                  ? '2px solid #ff6b35' 
                  : (theme === 'dark' ? '1px solid #404040' : '1px solid #e8e9ea'),
                color: theme === 'dark' ? '#fff' : '#333',
                boxShadow: selectedPlaylist === id 
                  ? '0 8px 25px rgba(255, 107, 53, 0.3)'
                  : (theme === 'dark' ? '0 4px 15px rgba(0, 0, 0, 0.3)' : '0 4px 15px rgba(0, 0, 0, 0.1)')
              }}
            >
              <div style={{ 
                width: '100%', 
                height: '120px', 
                borderRadius: '12px', 
                background: playlist.thumbnail 
                  ? `url(${playlist.thumbnail})` 
                  : 'linear-gradient(45deg, #ff6b35, #f7931e)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                marginBottom: '15px',
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {!playlist.thumbnail && (
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="white" style={{ opacity: 0.8 }}>
                    <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
                  </svg>
                )}
                <div style={{ position: 'absolute', bottom: '10px', right: '10px', display: 'flex', gap: '8px' }}>
                  {playlist.source_url && (
                    <button
                      onClick={(e) => refreshPlaylist(id, e)}
                      disabled={refreshingPlaylist === id}
                      style={{
                        background: refreshingPlaylist === id ? 'rgba(76, 175, 80, 0.8)' : 'rgba(0, 0, 0, 0.7)',
                        border: 'none',
                        borderRadius: '50%',
                        width: '32px',
                        height: '32px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: refreshingPlaylist === id ? 'not-allowed' : 'pointer',
                        transition: 'all 0.3s ease',
                        color: 'white',
                        fontSize: '12px'
                      }}
                      onMouseEnter={(e) => refreshingPlaylist !== id && (e.target.style.transform = 'scale(1.1)')}
                      onMouseLeave={(e) => refreshingPlaylist !== id && (e.target.style.transform = 'scale(1)')}
                      title={refreshingPlaylist === id ? 'Refreshing...' : 'Refresh from YouTube'}
                    >
                      {refreshingPlaylist === id ? (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
                        </svg>
                      ) : (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style={{ animation: refreshingPlaylist === id ? 'spin 1s linear infinite' : 'none' }}>
                          <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
                        </svg>
                      )}
                    </button>
                  )}
                  <button
                    onClick={(e) => playPlaylist(id, e)}
                    style={{
                      background: 'rgba(255, 107, 53, 0.9)',
                      border: 'none',
                      borderRadius: '50%',
                      width: '40px',
                      height: '40px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                      color: 'white',
                      fontSize: '16px'
                    }}
                    onMouseEnter={(e) => e.target.style.transform = 'scale(1.1)'}
                    onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
                  >
                    ▶
                  </button>
                </div>
              </div>
              <div>
                <h4 style={{ margin: '0 0 8px', fontSize: '18px', fontWeight: '600', lineHeight: '1.3' }}>{playlist.name}</h4>
                <p style={{ margin: 0, fontSize: '14px', opacity: 0.7, fontWeight: '500' }}>
                  {playlist.songs?.length || 0} {playlist.songs?.length === 1 ? 'song' : 'songs'}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>


      </div>
    </>
  );
};

const playlistCardStyle = {
  padding: '20px',
  borderRadius: '18px',
  cursor: 'pointer',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  position: 'relative',
  overflow: 'hidden',
  backdropFilter: 'blur(10px)'
};

const songItemStyle = {
  display: 'flex',
  alignItems: 'center',
  padding: '18px',
  borderRadius: '16px',
  cursor: 'pointer',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  backdropFilter: 'blur(10px)'
};

export default PlaylistView;