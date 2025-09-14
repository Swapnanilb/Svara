import React, { useState, useEffect } from 'react';
import { musicAPI } from '../services/api';

const PlaylistDropdown = ({ playlistId, playlist, onRefresh, onDelete, refreshing, theme }) => {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleClickOutside = () => setIsOpen(false);
    if (isOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [isOpen]);

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        style={{
          background: 'rgba(0, 0, 0, 0.7)',
          border: 'none',
          borderRadius: '50%',
          width: '32px',
          height: '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          color: 'white'
        }}
      >
        ⋮
      </button>
      {isOpen && (
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            position: 'absolute',
            top: '100%',
            right: 0,
            background: theme === 'dark' ? '#2a2a2a' : '#ffffff',
            border: `1px solid ${theme === 'dark' ? '#404040' : '#e8e9ea'}`,
            borderRadius: '8px',
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.2)',
            zIndex: 1000,
            minWidth: '120px',
            overflow: 'hidden'
          }}
        >
          {playlist.source_url && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsOpen(false);
                onRefresh();
              }}
              disabled={refreshing}
              style={{
                width: '100%',
                padding: '10px 15px',
                border: 'none',
                background: 'transparent',
                color: theme === 'dark' ? '#fff' : '#333',
                cursor: refreshing ? 'not-allowed' : 'pointer',
                textAlign: 'left',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
              onMouseEnter={(e) => !refreshing && (e.target.style.background = theme === 'dark' ? '#404040' : '#f5f5f5')}
              onMouseLeave={(e) => !refreshing && (e.target.style.background = 'transparent')}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }}>
                <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
              </svg>
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsOpen(false);
              onDelete();
            }}
            style={{
              width: '100%',
              padding: '10px 15px',
              border: 'none',
              background: 'transparent',
              color: '#ff4444',
              cursor: 'pointer',
              textAlign: 'left',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
            onMouseEnter={(e) => e.target.style.background = theme === 'dark' ? '#404040' : '#f5f5f5'}
            onMouseLeave={(e) => e.target.style.background = 'transparent'}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
            </svg>
            Delete
          </button>
        </div>
      )}
    </div>
  );
};

const PlaylistView = ({ onStatusUpdate, theme, onPlaylistSelect, onShowOverlay }) => {
  const [playlists, setPlaylists] = useState({});
  const [selectedPlaylist, setSelectedPlaylist] = useState(null);

  const [refreshingPlaylist, setRefreshingPlaylist] = useState(null);
  const [refreshingAll, setRefreshingAll] = useState(false);

  const [refreshMessage, setRefreshMessage] = useState(null);


  useEffect(() => {
    loadPlaylists();
  }, []);

  const loadPlaylists = async () => { 
    const response = await musicAPI.getPlaylists(); 
    setPlaylists(response.playlists); 
  };
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
      // Preload playlist in background before playing
      musicAPI.preloadPlaylist(playlistId).catch(console.error);
      await musicAPI.play(playlistId, 0);
      onStatusUpdate();
    } catch (error) {
      console.log('Play request sent, checking status...');
    }
  };

  const refreshPlaylist = async (playlistId) => {
    const playlist = playlists[playlistId];
    if (!playlist?.source_url) return;
    
    setRefreshingPlaylist(playlistId);
    onShowOverlay(true);
    try {
      const refreshResult = await musicAPI.refreshPlaylist(playlistId);
      
      const response = await musicAPI.getPlaylists();
      setPlaylists({...response.playlists});
      
      // Show refresh statistics popup
      const added = refreshResult.added ?? 0;
      const removed = refreshResult.removed ?? 0;
      const message = `Playlist refreshed: ${added} songs added, ${removed} songs removed`;
      setRefreshMessage(message);
      setTimeout(() => setRefreshMessage(null), 4000);
      
      onShowOverlay(false);
      setTimeout(() => setRefreshingPlaylist(null), 500);
    } catch (error) {
      console.log('Error refreshing playlist:', error);
      setRefreshingPlaylist(null);
      onShowOverlay(false);
    }
  };

  const deletePlaylist = async (playlistId) => {
    if (!window.confirm('Are you sure you want to delete this playlist?')) return;
    
    try {
      await musicAPI.deletePlaylist(playlistId);
      await loadPlaylists();
    } catch (error) {
      console.log('Error deleting playlist:', error);
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



  return (
    <>
      {refreshMessage && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          background: theme === 'dark' ? '#2a2a2a' : '#ffffff',
          color: theme === 'dark' ? '#fff' : '#333',
          padding: '15px 20px',
          borderRadius: '12px',
          boxShadow: '0 4px 15px rgba(0, 0, 0, 0.2)',
          border: '2px solid #ff6b35',
          zIndex: 1000,
          fontSize: '14px',
          fontWeight: '600'
        }}>
          {refreshMessage}
        </div>
      )}
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
                  <PlaylistDropdown
                    playlistId={id}
                    playlist={playlist}
                    onRefresh={() => refreshPlaylist(id)}
                    onDelete={() => deletePlaylist(id)}
                    refreshing={refreshingPlaylist === id}
                    theme={theme}
                  />
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



export default PlaylistView;