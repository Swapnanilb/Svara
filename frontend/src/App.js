import React, { useState, useEffect } from 'react';
import PlayerControls from './components/PlayerControls';
import PlaylistView from './components/PlaylistView';
import HomeView from './components/HomeView';
import SongsView from './components/SongsView';
import SettingsView from './components/SettingsView';
import { musicAPI } from './services/api';
import './svara-player.css';

function App() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentView, setCurrentView] = useState('home');
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'light';
  });
  const [showRefreshOverlay, setShowRefreshOverlay] = useState(false);

  useEffect(() => {
    updateStatus();
    const interval = setInterval(updateStatus, 500);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    localStorage.setItem('theme', theme);
  }, [theme]);

  const updateStatus = async () => {
    try {
      setStatus(await musicAPI.getStatus());
      setError(null);
    } catch (err) {
      setError('Backend connection failed');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="animated-bg" style={centerStyle}>
        <div className="glass fade-in" style={{ padding: '40px', textAlign: 'center' }}>
          <div className="spinner" style={{ margin: '0 auto 20px' }}></div>
          <h2 style={{ margin: '0 0 10px', fontSize: '24px', fontWeight: '600' }}>Loading Music Player</h2>
          <p style={{ margin: 0, opacity: 0.8 }}>Connecting to backend server...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="animated-bg" style={centerStyle}>
        <div className="glass fade-in" style={{ padding: '40px', textAlign: 'center' }}>
          <h2 style={{ margin: '0 0 15px', fontSize: '24px', fontWeight: '600' }}>Connection Error</h2>
          <p style={{ margin: '0 0 20px', opacity: 0.8 }}>{error}</p>
          <button onClick={updateStatus} className="btn-orange pulse">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={theme === 'dark' ? 'dark-bg' : 'animated-bg'} style={{ height: '100vh', display: 'flex', padding: '20px', gap: '20px' }}>
      {/* Sidebar */}
      <div className={theme === 'dark' ? 'dark-glass' : 'glass'} style={{ width: '200px', padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div 
          onClick={() => setCurrentView('home')}
          style={{ color: currentView === 'home' ? (theme === 'dark' ? '#fff' : '#333') : '#999', fontSize: '16px', marginBottom: '10px', cursor: 'pointer', fontWeight: currentView === 'home' ? '600' : '400' }}
        >
          Home
        </div>
        <div 
          onClick={() => setCurrentView('playlists')}
          style={{ color: currentView === 'playlists' ? (theme === 'dark' ? '#fff' : '#333') : '#999', fontSize: '16px', marginBottom: '10px', cursor: 'pointer', fontWeight: currentView === 'playlists' ? '600' : '400' }}
        >
          Playlists
        </div>
        <div 
          onClick={() => setCurrentView('songs')}
          style={{ color: currentView === 'songs' ? (theme === 'dark' ? '#fff' : '#333') : '#999', fontSize: '16px', marginBottom: '10px', cursor: 'pointer', fontWeight: currentView === 'songs' ? '600' : '400' }}
        >
          Songs
        </div>
        <div 
          onClick={() => setCurrentView('settings')}
          style={{ color: currentView === 'settings' ? (theme === 'dark' ? '#fff' : '#333') : '#999', fontSize: '16px', marginBottom: '40px', cursor: 'pointer', fontWeight: currentView === 'settings' ? '600' : '400' }}
        >
          Settings
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div className={theme === 'dark' ? 'dark-glass' : 'glass'} style={{ flex: 1, overflow: 'auto', borderRadius: '20px', marginBottom: '20px' }}>
          {currentView === 'home' && <HomeView onStatusUpdate={updateStatus} theme={theme} />}
          {currentView === 'playlists' && <PlaylistView onStatusUpdate={updateStatus} theme={theme} onPlaylistSelect={() => setCurrentView('songs')} onShowOverlay={setShowRefreshOverlay} />}
          {currentView === 'songs' && <SongsView status={status} onStatusUpdate={updateStatus} theme={theme} />}
          {currentView === 'settings' && <SettingsView theme={theme} onThemeChange={setTheme} />}
        </div>
        <PlayerControls status={status} onStatusUpdate={updateStatus} theme={theme} />
      </div>
      {showRefreshOverlay && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999
        }}>
          <div className={theme === 'dark' ? 'dark-glass' : 'glass'} style={{ padding: '40px', textAlign: 'center' }}>
            <div className="spinner" style={{ margin: '0 auto 20px', borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.3)', borderTopColor: '#ff6b35' }}></div>
            <h3 style={{ margin: '0 0 10px', fontSize: '20px', fontWeight: '600', color: theme === 'dark' ? '#fff' : '#333' }}>Refreshing Playlist</h3>
            <p style={{ margin: 0, opacity: 0.8, color: theme === 'dark' ? '#ccc' : '#666' }}>Syncing with YouTube changes...</p>
          </div>
        </div>
      )}
    </div>
  );
}

const centerStyle = {
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100vh',
  padding: '20px'
};



export default App;