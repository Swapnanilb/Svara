import React, { useState, useEffect, useRef } from 'react';
import { musicAPI, ProgressWebSocket } from '../services/api';

const HomeView = ({ onStatusUpdate, theme, globalLoading, globalLoadingMessage, progressData, onGlobalLoading, onGlobalLoadingMessage, onProgressData }) => {
  const [newUrl, setNewUrl] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [showPlaylistDialog, setShowPlaylistDialog] = useState(false);

  const [playlists, setPlaylists] = useState([]);
  const [newPlaylistName, setNewPlaylistName] = useState('');
  const [message, setMessage] = useState('');
  const [selectedPlaylistId, setSelectedPlaylistId] = useState(null);
  const [showPopup, setShowPopup] = useState(false);
  const [popupMessage, setPopupMessage] = useState('');
  const wsRef = useRef(null);

  useEffect(() => {
    loadPlaylists();
  }, []);

  const loadPlaylists = async () => {
    try {
      const data = await musicAPI.getPlaylists();
      setPlaylists(Object.entries(data.playlists || {}).map(([id, info]) => ({ id, ...info })));
    } catch (error) {
      console.error('Error loading playlists:', error);
    }
  };

  const addContent = async () => {
    if (!newUrl.trim() || isAdding) return;
    setIsAdding(true);
    onGlobalLoading(true);
    onGlobalLoadingMessage('Getting playlist info...');
    setMessage('');
    
    try {
      if (newUrl.includes('list=')) {
        // Setup WebSocket for progress tracking
        wsRef.current = new ProgressWebSocket();
        wsRef.current.connect(
          (progress) => {
            onProgressData(progress);
          },
          (complete) => {
            onProgressData(null);
            onGlobalLoading(false);
            setIsAdding(false);
            setMessage(complete.message);
            loadPlaylists();
            wsRef.current.disconnect();
          }
        );
        
        const response = await musicAPI.addPlaylist(newUrl);
        if (response.exists) {
          setPopupMessage('Playlist already exists!');
          setShowPopup(true);
          onGlobalLoading(false);
          setIsAdding(false);
          wsRef.current.disconnect();
        }
        setNewUrl('');
      } else {
        // Validate YouTube URL
        const videoIdMatch = newUrl.match(/(?:v=|\/)([a-zA-Z0-9_-]{11})/);
        if (!videoIdMatch) {
          setMessage('Invalid YouTube URL. Please enter a valid YouTube video link.');
          onGlobalLoading(false);
          setTimeout(() => setIsAdding(false), 2000);
          return;
        }
        
        await loadPlaylists();
        onGlobalLoading(false);
        setShowPlaylistDialog(true);
      }
    } catch (error) {
      setMessage('Error adding content. Please try again.');
      console.error('Error adding content:', error);
      onGlobalLoading(false);
      setIsAdding(false);
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    }
  };

  const addToPlaylist = async () => {
    if (!selectedPlaylistId) return;
    onGlobalLoading(true);
    onGlobalLoadingMessage('Adding song to playlist...');
    try {
      console.log('Checking song existence...');
      const checkResponse = await musicAPI.checkSong(newUrl, selectedPlaylistId);
      console.log('Check response:', checkResponse);
      
      if (checkResponse.exists) {
        setPopupMessage('Song already exists in playlist!');
        setShowPopup(true);
        setNewUrl('');
        setShowPlaylistDialog(false);
        setSelectedPlaylistId(null);
      } else {
        console.log('Adding song to playlist...');
        const response = await musicAPI.addSong(newUrl, selectedPlaylistId);
        console.log('Add response:', response);
        setMessage('Song added to playlist!');
        setNewUrl('');
        setShowPlaylistDialog(false);
        setSelectedPlaylistId(null);
      }
    } catch (error) {
      setMessage(`Error adding song: ${error.response?.data?.detail || error.message}`);
      console.error('Error adding song:', error);
    }
    onGlobalLoading(false);
  };

  const createNewPlaylist = async () => {
    if (!newPlaylistName.trim()) return;
    onGlobalLoading(true);
    onGlobalLoadingMessage('Creating new playlist...');
    try {
      console.log('Creating new playlist with song...');
      const response = await musicAPI.addSong(newUrl, null, newPlaylistName);
      console.log('Create response:', response);
      setMessage('New playlist created with song!');
      setNewUrl('');
      setNewPlaylistName('');
      setShowPlaylistDialog(false);
      await loadPlaylists(); // Refresh playlists
    } catch (error) {
      setMessage(`Error creating playlist: ${error.response?.data?.detail || error.message}`);
      console.error('Error creating playlist:', error);
    }
    onGlobalLoading(false);
  };

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      height: '100%', 
      padding: '40px' 
    }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <img src="./svara_logo.png" alt="SVARA" style={{ height: '200px', marginBottom: '10px' }} />
        <p style={{ fontSize: '16px', color: theme === 'dark' ? '#ccc' : '#999', marginBottom: '0' }}>
          Add your favorite playlists and songs
        </p>
      </div>

      <div style={{ width: '100%', maxWidth: '500px' }}>
        <div style={{ display: 'flex', gap: '15px', marginBottom: '20px' }}>
          <input
            type="text"
            placeholder="Enter YouTube playlist or song URL"
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            style={{
              flex: 1,
              padding: '15px 20px',
              border: theme === 'dark' ? '2px solid #555' : '2px solid #e0e0e0',
              borderRadius: '15px',
              background: theme === 'dark' ? '#444' : '#ffffff',
              color: theme === 'dark' ? '#ffffff' : '#000000',
              fontSize: '16px',
              outline: 'none',
              transition: 'border-color 0.3s ease',
              WebkitTextFillColor: theme === 'dark' ? '#ffffff' : '#000000'
            }}
            onFocus={(e) => e.target.style.borderColor = '#ff6b35'}
            onBlur={(e) => e.target.style.borderColor = theme === 'dark' ? '#555' : '#e0e0e0'}
          />
          <button 
            onClick={addContent} 
            className="btn-orange"
            disabled={isAdding}
            style={{ 
              minWidth: '120px',
              padding: '15px 25px',
              fontSize: '16px'
            }}
          >
            {isAdding ? 'Adding...' : 'Add'}
          </button>
        </div>
        
        <div style={{ textAlign: 'center', color: theme === 'dark' ? '#ccc' : '#999', fontSize: '14px' }}>
          Supports YouTube playlists and individual songs
        </div>
        
        {message && (
          <div style={{
            marginTop: '15px', padding: '10px', borderRadius: '8px',
            background: (message.includes('Error') || message.includes('Invalid')) ? '#ffebee' : '#e8f5e8',
            color: (message.includes('Error') || message.includes('Invalid')) ? '#c62828' : '#2e7d32',
            textAlign: 'center', fontSize: '14px'
          }}>
            {message}
          </div>
        )}
      </div>

      {showPlaylistDialog && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div style={{
            background: 'white', padding: '30px', borderRadius: '15px',
            maxWidth: '400px', width: '90%', maxHeight: '80vh', overflow: 'auto'
          }}>
            <h3 style={{ margin: '0 0 20px 0', color: '#333' }}>Add Song to Playlist</h3>
            
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#666' }}>Local Playlists:</h4>
              {playlists.filter(playlist => !playlist.source_url).map(playlist => (
                <button
                  key={playlist.id}
                  onClick={() => setSelectedPlaylistId(playlist.id)}
                  style={{
                    display: 'block', width: '100%', padding: '10px',
                    margin: '5px 0', border: selectedPlaylistId === playlist.id ? '2px solid #ff6b35' : '1px solid #ddd',
                    borderRadius: '8px', background: selectedPlaylistId === playlist.id ? '#fff3f0' : 'white',
                    textAlign: 'left', cursor: 'pointer'
                  }}
                >
                  {playlist.name}
                </button>
              ))}
              {playlists.filter(playlist => !playlist.source_url).length === 0 && (
                <p style={{ color: '#999', fontStyle: 'italic', margin: '10px 0' }}>
                  No local playlists available. Create a new one below.
                </p>
              )}
              
              {selectedPlaylistId && (
                <button
                  onClick={addToPlaylist}
                  className="btn-orange"
                  style={{ width: '100%', marginTop: '10px', padding: '12px' }}
                >
                  Add to Selected Playlist
                </button>
              )}
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#666' }}>Create New Playlist:</h4>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input
                  type="text"
                  placeholder="Playlist name"
                  value={newPlaylistName}
                  onChange={(e) => setNewPlaylistName(e.target.value)}
                  style={{
                    flex: 1, padding: '10px', border: '1px solid #ddd',
                    borderRadius: '8px', outline: 'none'
                  }}
                />
                <button
                  onClick={createNewPlaylist}
                  className="btn-orange"
                  style={{ padding: '10px 20px' }}
                >
                  Create
                </button>
              </div>
            </div>
            
            <button
              onClick={() => {
                setShowPlaylistDialog(false);
                setSelectedPlaylistId(null);
              }}
              style={{
                width: '100%', padding: '10px', border: '1px solid #ddd',
                borderRadius: '8px', background: '#f5f5f5', cursor: 'pointer'
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      
      {globalLoading && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 1000
        }}>
          <div style={{
            background: theme === 'dark' ? '#2a2a2a' : '#ffffff',
            padding: '40px',
            borderRadius: '15px',
            textAlign: 'center',
            minWidth: '300px',
            color: theme === 'dark' ? '#fff' : '#333',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
            border: theme === 'dark' ? '1px solid #404040' : '1px solid #e0e0e0'
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              border: theme === 'dark' ? '4px solid #555' : '4px solid #f3f3f3',
              borderTop: '4px solid #ff6b35',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 20px'
            }}></div>
            
            {progressData ? (
              <div>
                <h3 style={{ margin: '0 0 15px', fontSize: '20px', fontWeight: '600' }}>
                  {progressData.message}
                </h3>
                <div style={{
                  width: '100%',
                  height: '8px',
                  background: theme === 'dark' ? '#404040' : '#f0f0f0',
                  borderRadius: '4px',
                  overflow: 'hidden',
                  marginBottom: '10px'
                }}>
                  <div style={{
                    width: `${(progressData.current / progressData.total) * 100}%`,
                    height: '100%',
                    background: '#ff6b35',
                    transition: 'width 0.3s ease'
                  }}></div>
                </div>
                <p style={{ margin: 0, opacity: 0.8, color: theme === 'dark' ? '#ccc' : '#666' }}>
                  {progressData.current}/{progressData.total} songs
                  {progressData.song_title && (
                    <span style={{ display: 'block', marginTop: '5px', fontStyle: 'italic' }}>
                      {progressData.song_title}
                    </span>
                  )}
                </p>
              </div>
            ) : (
              <div>
                <h3 style={{ margin: '0 0 10px', fontSize: '20px', fontWeight: '600' }}>Processing</h3>
                <p style={{ margin: 0, opacity: 0.8, color: theme === 'dark' ? '#ccc' : '#666' }}>
                  {globalLoadingMessage || 'Getting playlist info...'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {showPopup && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1001
        }}>
          <div style={{
            background: 'white', padding: '30px', borderRadius: '15px',
            textAlign: 'center', minWidth: '300px'
          }}>
            <div style={{ fontSize: '18px', color: '#333', marginBottom: '20px' }}>
              {popupMessage}
            </div>
            <button
              onClick={() => setShowPopup(false)}
              className="btn-orange"
              style={{ padding: '10px 30px' }}
            >
              OK
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomeView;