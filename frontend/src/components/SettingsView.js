import React from 'react';

const SettingsView = ({ theme, onThemeChange }) => {
  return (
    <div style={{ 
      padding: '40px',
      color: theme === 'dark' ? '#fff' : '#333'
    }}>
      <h2 style={{ 
        fontSize: '28px', 
        fontWeight: '700', 
        marginBottom: '30px',
        color: theme === 'dark' ? '#fff' : '#333'
      }}>
        Settings
      </h2>
      
      <div style={{ marginBottom: '30px' }}>
        <h3 style={{ 
          fontSize: '18px', 
          fontWeight: '600', 
          marginBottom: '15px',
          color: theme === 'dark' ? '#fff' : '#333'
        }}>
          Appearance
        </h3>
        
        <div style={{ display: 'flex', gap: '15px' }}>
          <button
            onClick={() => onThemeChange('light')}
            style={{
              padding: '10px 20px',
              border: theme === 'light' ? '2px solid #ff6b35' : '1px solid #ddd',
              borderRadius: '8px',
              background: theme === 'light' ? '#fff3f0' : (theme === 'dark' ? '#333' : 'white'),
              color: theme === 'dark' ? '#fff' : '#333',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Light Theme
          </button>
          
          <button
            onClick={() => onThemeChange('dark')}
            style={{
              padding: '10px 20px',
              border: theme === 'dark' ? '2px solid #ff6b35' : '1px solid #ddd',
              borderRadius: '8px',
              background: theme === 'dark' ? '#444' : 'white',
              color: theme === 'dark' ? '#fff' : '#333',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Dark Theme
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsView;