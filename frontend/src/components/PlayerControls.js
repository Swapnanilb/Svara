import React from 'react';
import { musicAPI } from '../services/api';

const PlayerControls = ({ status, onStatusUpdate, theme }) => {
  const [localPosition, setLocalPosition] = React.useState(0);
  const [isDragging, setIsDragging] = React.useState(false);
  const [localVolume, setLocalVolume] = React.useState(null);
  const [isRepeat, setIsRepeat] = React.useState(false);
  const [isShuffle, setIsShuffle] = React.useState(false);

  const handlePlayPause = async () => { try { await musicAPI.togglePause(); } catch {} onStatusUpdate(); };
  const handleNext = async () => { try { await musicAPI.nextSong(); } catch {} onStatusUpdate(); };
  const handlePrevious = async () => { try { await musicAPI.previousSong(); } catch {} onStatusUpdate(); };
  const handleForward = async () => { try { await musicAPI.seek((status?.position / 1000 || 0) + 10); } catch {} onStatusUpdate(); };
  const handleBackward = async () => { try { await musicAPI.seek(Math.max(0, (status?.position / 1000 || 0) - 10)); } catch {} onStatusUpdate(); };
  const handleRepeat = async () => { 
    try { 
      const response = await musicAPI.toggleRepeat(); 
      setIsRepeat(response.is_repeated);
      setIsShuffle(response.is_shuffled);

    } catch {} 
  };
  const handleShuffle = async () => { 
    try { 
      const response = await musicAPI.toggleShuffle(); 
      setIsShuffle(response.is_shuffled);
      setIsRepeat(response.is_repeated);

    } catch {} 
  };
  const handleVolumeChange = async (e) => {
    const volume = parseFloat(e.target.value);
    setLocalVolume(volume);
    try { 
      await musicAPI.setVolume(volume); 
    } catch {}
  };
  const handleMuteToggle = async () => {
    try { 
      await musicAPI.toggleMute();
      onStatusUpdate();
    } catch {}
  };
  const handleSeek = (e) => {
    const value = parseFloat(e.target.value);
    setLocalPosition(value);
  };
  
  const handleMouseDown = () => {
    setIsDragging(true);
    setLocalPosition(status?.position / 1000 || 0);
  };
  
  const handleMouseUp = async () => {
    try { await musicAPI.seek(localPosition); } catch {}
    // Delay before allowing status updates to override position
    setTimeout(() => setIsDragging(false), 1000);
  };
  
  // Update local states when not changing
  React.useEffect(() => {
    if (!isDragging) {
      setLocalPosition(status?.position / 1000 || 0);
    }
    if (localVolume === null) {
      setLocalVolume(status?.volume ?? 0.5);
    }
    // Sync shuffle/repeat states with backend
    if (status?.is_shuffled !== undefined) {
      setIsShuffle(status.is_shuffled);
    }
    if (status?.is_repeated !== undefined) {
      setIsRepeat(status.is_repeated);
    }

  }, [status?.position, status?.volume, status?.is_shuffled, status?.is_repeated, isDragging, localVolume]);

  const formatTime = (s) => `${Math.floor(s/60)}:${Math.floor(s%60).toString().padStart(2,'0')}`;

  return (
    <div style={{...playerStyle, background: theme === 'dark' ? '#333' : 'white', color: theme === 'dark' ? '#fff' : '#333'}} className={theme === 'dark' ? 'dark-glass' : 'glass'}>
      {/* Left: Now Playing */}
      <div style={leftSection}>
        {status?.current_song?.thumbnail_url ? (
          <img 
            src={status.current_song.thumbnail_url} 
            alt="Album" 
            style={{
              ...albumArtStyle,
              transform: status?.is_playing && !status?.is_paused ? 'scale(1.05)' : 'scale(1)'
            }} 
            className="card-hover"
          />
        ) : (
          <div style={{
            ...albumArtStyle,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '24px',
            color: '#ff6b35'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
            </svg>
          </div>
        )}
        <div style={songInfoStyle}>
          <div style={{...songTitleStyle, color: theme === 'dark' ? '#fff' : '#333'}}>{status?.current_song?.title || 'No song playing'}</div>
          <div style={{...artistStyle, color: theme === 'dark' ? '#ccc' : '#999'}}>Unknown Artist</div>
        </div>
      </div>

      {/* Center: Controls & Progress */}
      <div style={centerSection}>
        <div style={controlsStyle}>
          <button onClick={handleShuffle} style={{...buttonStyle, opacity: isShuffle ? 1 : 0.5}} title={isShuffle ? 'Shuffle On' : 'Shuffle Off'}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5" stroke={isShuffle ? '#ff6b35' : '#999'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" filter={isShuffle ? 'drop-shadow(0 0 4px #ff6b35)' : 'none'}/>
            </svg>
          </button>
          <button onClick={handleBackward} style={buttonStyle}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M11 19l-7-7 7-7m8 14l-7-7 7-7" stroke="#999" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          <button onClick={handlePrevious} style={buttonStyle}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M19 20L9 12l10-8v16zM5 19V5" stroke="#999" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          <button 
            onClick={handlePlayPause} 
            style={playButtonStyle}
            className={status?.is_playing && !status?.is_paused ? 'pulse' : ''}
          >
            {status?.is_playing && !status?.is_paused ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <rect x="6" y="4" width="4" height="16" fill="white"/>
                <rect x="14" y="4" width="4" height="16" fill="white"/>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <polygon points="5,3 19,12 5,21" fill="white"/>
              </svg>
            )}
          </button>
          <button onClick={handleNext} style={buttonStyle}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M5 4l10 8-10 8V4zM19 5v14" stroke="#999" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          <button onClick={handleForward} style={buttonStyle}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M13 5l7 7-7 7M6 5l7 7-7 7" stroke="#999" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          <button onClick={handleRepeat} style={{...buttonStyle, opacity: isRepeat ? 1 : 0.5}} title={isRepeat ? 'Repeat On' : 'Repeat Off'}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M17 1l4 4-4 4M3 11V9a4 4 0 0 1 4-4h14M7 23l-4-4 4-4M21 13v2a4 4 0 0 1-4 4H3" stroke={isRepeat ? '#ff6b35' : '#999'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" filter={isRepeat ? 'drop-shadow(0 0 4px #ff6b35)' : 'none'}/>
            </svg>
          </button>
        </div>
        <div style={progressStyle}>
          <span style={{...timeStyle, color: theme === 'dark' ? '#ccc' : '#999'}}>{formatTime(status?.position / 1000 || 0)}</span>
          <input
            type="range"
            min="0"
            max={Math.max(status?.duration / 1000 || 100, 1)}
            value={isDragging ? localPosition : (status?.position / 1000 || 0)}
            onChange={handleSeek}
            onMouseDown={handleMouseDown}
            onMouseUp={handleMouseUp}
            style={{
              ...sliderStyle,
              '--progress': `${((isDragging ? localPosition : (status?.position / 1000 || 0)) / Math.max(status?.duration / 1000 || 100, 1)) * 100}%`,
              background: `linear-gradient(to right, #ff6b35 0%, #ff6b35 ${((isDragging ? localPosition : (status?.position / 1000 || 0)) / Math.max(status?.duration / 1000 || 100, 1)) * 100}%, ${theme === 'dark' ? '#555' : '#e0e0e0'} ${((isDragging ? localPosition : (status?.position / 1000 || 0)) / Math.max(status?.duration / 1000 || 100, 1)) * 100}%, ${theme === 'dark' ? '#555' : '#e0e0e0'} 100%)`
            }}
          />
          <span style={{...timeStyle, color: theme === 'dark' ? '#ccc' : '#999'}}>{formatTime(status?.duration / 1000 || 0)}</span>
        </div>
      </div>

      {/* Right: Volume */}
      <div style={rightSection}>
        <button onClick={handleMuteToggle} style={{...buttonStyle, padding: '4px'}}>
          {status?.is_muted ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M11 5L6 9H2v6h4l5 4V5z" stroke="#999" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <line x1="23" y1="9" x2="17" y2="15" stroke="#999" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <line x1="17" y1="9" x2="23" y2="15" stroke="#999" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M11 5L6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 0 1 0 7.07M19.07 4.93a10 10 0 0 1 0 14.14" stroke="#999" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </button>
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={localVolume ?? (status?.volume ?? 0.5)}
          onChange={handleVolumeChange}
          style={{
            ...volumeSliderStyle,
            background: `linear-gradient(to right, #ff6b35 0%, #ff6b35 ${(localVolume ?? (status?.volume ?? 0.5)) * 100}%, ${theme === 'dark' ? '#555' : '#e0e0e0'} ${(localVolume ?? (status?.volume ?? 0.5)) * 100}%, ${theme === 'dark' ? '#555' : '#e0e0e0'} 100%)`
          }}
        />
      </div>
    </div>
  );
};

const playerStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '20px',
  background: 'white',
  borderRadius: '20px',
  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
  color: '#333',
  height: '80px'
};

const leftSection = {
  display: 'flex',
  alignItems: 'center',
  gap: '15px',
  width: '30%'
};

const albumArtStyle = {
  width: '50px',
  height: '50px',
  borderRadius: '8px',
  objectFit: 'cover',
  backgroundColor: '#f0f2f5'
};

const songInfoStyle = {
  overflow: 'hidden',
  flex: 1
};

const songTitleStyle = {
  fontSize: '14px',
  fontWeight: '600',
  color: '#333',
  marginBottom: '2px',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
  maxWidth: '200px'
};

const artistStyle = {
  fontSize: '12px',
  color: '#999'
};

const centerSection = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  width: '45%'
};

const controlsStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '15px',
  marginBottom: '10px'
};

const buttonStyle = {
  backgroundColor: 'transparent',
  border: 'none',
  color: '#999',
  cursor: 'pointer',
  fontSize: '16px',
  padding: '8px',
  borderRadius: '50%',
  width: '40px',
  height: '40px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  transition: 'color 0.2s ease'
};

const playButtonStyle = {
  background: 'linear-gradient(45deg, #ff6b35, #ff8c42)',
  border: 'none',
  color: 'white',
  cursor: 'pointer',
  fontSize: '18px',
  width: '50px',
  height: '50px',
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  boxShadow: '0 2px 10px rgba(255, 107, 53, 0.2)'
};

const progressStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  width: '100%'
};

const timeStyle = {
  fontSize: '12px',
  color: '#999',
  minWidth: '35px'
};

const sliderStyle = {
  flex: 1,
  height: '6px',
  borderRadius: '3px',
  outline: 'none',
  cursor: 'pointer',
  WebkitAppearance: 'none',
  background: 'linear-gradient(to right, #ff6b35 0%, #ff6b35 var(--progress, 0%), #e0e0e0 var(--progress, 0%), #e0e0e0 100%)'
};

const rightSection = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  width: '25%',
  justifyContent: 'flex-end'
};

const volumeSliderStyle = {
  width: '80px',
  height: '6px',
  borderRadius: '3px',
  outline: 'none',
  cursor: 'pointer',
  WebkitAppearance: 'none',
  background: 'linear-gradient(to right, #ff6b35 0%, #ff6b35 var(--volume, 50%), #e0e0e0 var(--volume, 50%), #e0e0e0 100%)'
};



export default PlayerControls;