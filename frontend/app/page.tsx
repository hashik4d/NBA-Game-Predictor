'use client';

import { useState, useEffect } from 'react';
import GameCard from '../components/GameCard';

export default function Home() {
  const [games, setGames] = useState<any[]>([]);
  const [gameDate, setGameDate] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'today' | 'tomorrow'>('today');

  // Keep track of the "Base" today date from the first API call
  const [todayDate, setTodayDate] = useState<string>('');

  async function fetchGames(targetDate?: string) {
    setLoading(true);
    setGames([]); // Clear list while loading
    try {
      const url = targetDate
        ? `http://localhost:8000/games?date=${targetDate}`
        : 'http://localhost:8000/games';

      const res = await fetch(url);
      const data = await res.json();
      setGames(data.games || []);
      setGameDate(data.date || '');

      // If this is the initial load, set Today
      if (!targetDate && !todayDate) {
        setTodayDate(data.date);
      }
    } catch (err) {
      console.error("Failed to fetch games", err);
      // Fallback
      setGames([]);
    } finally {
      setLoading(false);
    }
  }

  // Initial Load
  useEffect(() => {
    fetchGames();
  }, []);

  const handleTabChange = (tab: 'today' | 'tomorrow') => {
    setActiveTab(tab);
    if (tab === 'today') {
      // Fetch base today (or just reload default)
      fetchGames(todayDate);
    } else {
      // Calculate tomorrow
      if (todayDate) {
        const d = new Date(todayDate);
        d.setDate(d.getDate() + 1);
        const tomorrowStr = d.toISOString().split('T')[0];
        fetchGames(tomorrowStr);
      }
    }
  };

  return (
    <main className="container">
      <header>
        <h1>NBA Game Predictor</h1>
        <p className="subtitle">AI-Powered Predictions for {gameDate ? `Games on ${gameDate}` : "Tonight's Action"}</p>

        {/* Date Tabs */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '1rem',
          marginTop: '1.5rem',
          marginBottom: '1rem'
        }}>
          <button
            onClick={() => handleTabChange('today')}
            style={{
              padding: '8px 24px',
              background: activeTab === 'today' ? '#fb923c' : 'rgba(255,255,255,0.05)',
              color: activeTab === 'today' ? '#000' : '#fff',
              border: 'none',
              borderRadius: '20px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Today
          </button>
          <button
            onClick={() => handleTabChange('tomorrow')}
            style={{
              padding: '8px 24px',
              background: activeTab === 'tomorrow' ? '#fb923c' : 'rgba(255,255,255,0.05)',
              color: activeTab === 'tomorrow' ? '#000' : '#fff',
              border: 'none',
              borderRadius: '20px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Tomorrow
          </button>
        </div>
      </header>

      {loading ? (
        <div style={{ textAlign: 'center', marginTop: '4rem', opacity: 0.6 }}>Loading schedule...</div>
      ) : (
        <div className="games-grid">
          {games.length > 0 ? games.map((game) => (
            <GameCard key={game.gameId} game={game} date={gameDate} />
          )) : (
            <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '3rem', opacity: 0.5 }}>
              No games scheduled for this date.
            </div>
          )}
        </div>
      )}
    </main>
  );
}
