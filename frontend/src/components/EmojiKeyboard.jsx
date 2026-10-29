import React, { useState } from 'react';
import { Search } from 'lucide-react';

const EMOJI_CATEGORIES = {
  gestures: {
    label: '🖐️ Hands',
    emojis: ['🤙', '👋', '✌️', '🤞', '👍', '👊', '👌', '🤝', '🙌', '🙏', '💪', '💅', '👈', '👉', '👆', '👇', '🤟', '🤘']
  },
  streaks: {
    label: '🔥 Streaks',
    emojis: ['🔥', '⚡', '✨', '🌟', '💥', '🚀', '💯', '🎯', '🔮', '🏆', '🥇', '👑', '💣', '⭐', '💫', '☀️', '🌋', '🚨']
  },
  hearts: {
    label: '❤️ Hearts',
    emojis: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '💖', '💗', '💓', '💞', '💘', '💌', '💕', '😻', '💋', '🌹']
  },
  smileys: {
    label: '😀 Faces',
    emojis: ['😎', '🤩', '🥳', '😇', '🤠', '😈', '👻', '🤖', '🎉', '🎊', '🎁', '😜', '😋', '🤓', '😴', '🤪', '🤤', '🤫']
  },
  aesthetic: {
    label: '🌸 Aesthetic',
    emojis: ['🌸', '🌺', '🌻', '🍀', '🍕', '🍔', '🍟', '🍿', '🍩', '🥤', '☕', '🎵', '📸', '💎', '🌈', '🥑', '🧁', '🍦']
  }
};

export default function EmojiKeyboard({ selectedEmoji, onSelectEmoji }) {
  const [activeCategory, setActiveCategory] = useState('gestures');
  const [search, setSearch] = useState('');

  const currentCategory = EMOJI_CATEGORIES[activeCategory] || EMOJI_CATEGORIES.gestures;

  const filteredEmojis = search.trim()
    ? Object.values(EMOJI_CATEGORIES)
        .flatMap((cat) => cat.emojis)
        .filter((emoji) => emoji.includes(search.trim()))
    : currentCategory.emojis;

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearch(val);
    // If user directly pastes or types an emoji into the search bar, automatically select it!
    if (val.trim()) {
      const emojiMatch = val.trim().match(/(\p{Emoji_Presentation}|\p{Extended_Pictographic})/u);
      if (emojiMatch) {
        onSelectEmoji(emojiMatch[0]);
      }
    }
  };

  return (
    <div style={{
      background: '#ffffff',
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      padding: '10px 12px',
      boxShadow: '0 2px 10px rgba(0,0,0,0.04)'
    }}>
      {/* Category Pills */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '5px',
        marginBottom: '10px'
      }}>
        {Object.entries(EMOJI_CATEGORIES).map(([key, cat]) => {
          const isActive = activeCategory === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => {
                setActiveCategory(key);
                setSearch('');
              }}
              style={{
                padding: '4px 10px',
                fontSize: '0.74rem',
                fontWeight: 600,
                borderRadius: '14px',
                border: isActive ? '1.5px solid #0284c7' : '1px solid #e2e8f0',
                background: isActive ? '#e0f2fe' : '#f8fafc',
                color: isActive ? '#0369a1' : '#64748b',
                cursor: 'pointer',
                transition: 'all 0.12s ease'
              }}
            >
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Clean Single Search Input (no confusing paste/use forms!) */}
      <div style={{ position: 'relative', marginBottom: '10px' }}>
        <Search size={14} style={{ position: 'absolute', left: '10px', top: '8px', color: '#94a3b8' }} />
        <input
          type="text"
          placeholder="Search emoji or paste emoji here..."
          value={search}
          onChange={handleSearchChange}
          style={{
            width: '100%',
            padding: '6px 10px 6px 30px',
            fontSize: '0.8rem',
            borderRadius: '8px',
            border: '1px solid #cbd5e1',
            outline: 'none',
            background: '#f8fafc'
          }}
        />
      </div>

      {/* Emoji Grid (Click any emoji to select) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(8, 1fr)',
        gap: '5px',
        maxHeight: '130px',
        overflowY: 'auto',
        padding: '2px'
      }}>
        {filteredEmojis.map((emoji, idx) => {
          const isSelected = selectedEmoji === emoji;
          return (
            <button
              key={`${emoji}-${idx}`}
              type="button"
              onClick={() => onSelectEmoji(emoji)}
              style={{
                fontSize: '1.3rem',
                height: '36px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '8px',
                border: isSelected ? '2px solid #0284c7' : '1px solid #f1f5f9',
                background: isSelected ? '#e0f2fe' : '#ffffff',
                cursor: 'pointer',
                transition: 'transform 0.1s ease, background 0.12s ease',
                boxShadow: isSelected ? '0 0 0 2px rgba(2, 132, 199, 0.25)' : 'none'
              }}
              onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.15)')}
              onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1.0)')}
              title={`Click to pick ${emoji}`}
            >
              {emoji}
            </button>
          );
        })}
      </div>

      {/* Footer Selected Preview */}
      <div style={{
        marginTop: '8px',
        paddingTop: '6px',
        borderTop: '1px solid #f1f5f9',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.78rem',
        color: '#64748b'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>Selected Emoji:</span>
          <span style={{
            fontSize: '1.3rem',
            background: '#e0f2fe',
            border: '1px solid #bae6fd',
            borderRadius: '6px',
            padding: '2px 8px',
            lineHeight: 1
          }}>
            {selectedEmoji || 'None'}
          </span>
        </div>
        <span style={{ fontSize: '0.70rem', color: '#94a3b8' }}>Click any emoji above</span>
      </div>
    </div>
  );
}
