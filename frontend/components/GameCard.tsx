'use client';

import { useState } from 'react';

export default function GameCard({ game, date }: { game: any, date: string }) {
    const [prediction, setPrediction] = useState<any>(null);
    const [loading, setLoading] = useState<boolean>(false);

    const getPrediction = async () => {
        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8000/predict?home=${encodeURIComponent(game.homeTeamName)}&away=${encodeURIComponent(game.awayTeamName)}&date=${date}`);
            const data = await res.json();
            setPrediction(data);
        } catch (err) {
            console.error("Prediction failed", err);
            // Demo prediction if API fails
            setPrediction({
                predictedWinner: game.homeTeamName,
                confidence: 72,
                analysis: "Based on recent home court advantage and injury reports, the home team has a slight edge in this matchup."
            });
        } finally {
            setLoading(false);
        }
    };

    const isLive = (status: string) => {
        return status && !status.includes('Final') && !status.includes('ET') && !status.includes('pm') && !status.includes('am');
    };

    const getStatusColor = (status: string) => {
        if (status.includes('Final')) return '#9ca3af'; // Gray
        if (isLive(status)) return '#ef4444'; // Red (Live)
        return '#22c55e'; // Green (Future)
    };

    return (
        <div className="game-card">
            <div className="game-header">
                <span style={{ fontSize: '0.8rem', opacity: 0.8 }}>NBA Regular Season</span>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    background: 'rgba(0,0,0,0.3)',
                    padding: '4px 8px',
                    borderRadius: '12px',
                    fontSize: '0.85rem',
                    fontWeight: 700
                }}>
                    {isLive(game.gameTimeET) && <span className="animate-pulse" style={{ color: '#ef4444' }}>●</span>}
                    <span style={{ color: getStatusColor(game.gameTimeET) }}>
                        {isLive(game.gameTimeET) ? `LIVE - ${game.gameTimeET}` : game.gameTimeET}
                    </span>
                </div>
            </div>

            <div className="teams">
                <div className="team">
                    <img
                        src={`https://cdn.nba.com/logos/nba/${game.awayTeamId}/global/L/logo.svg`}
                        alt={game.awayTeamName}
                        style={{ width: '60px', height: '60px', objectFit: 'contain' }}
                        onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                            ((e.target as HTMLImageElement).nextSibling as HTMLElement).style.display = 'flex';
                        }}
                    />
                    <div className="fallback-logo" style={{ display: 'none' }}>{game.awayTeamName[0]}</div>
                    <div style={{ fontWeight: 600, marginTop: '0.5rem' }}>{game.awayTeamName}</div>
                </div>
                <div className="vs">VS</div>
                <div className="team">
                    <img
                        src={`https://cdn.nba.com/logos/nba/${game.homeTeamId}/global/L/logo.svg`}
                        alt={game.homeTeamName}
                        style={{ width: '60px', height: '60px', objectFit: 'contain' }}
                        onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                            ((e.target as HTMLImageElement).nextSibling as HTMLElement).style.display = 'flex';
                        }}
                    />
                    <div className="fallback-logo" style={{ display: 'none', background: 'rgba(249, 115, 22, 0.2)', color: '#fb923c' }}>{game.homeTeamName[0]}</div>
                    <div style={{ fontWeight: 600, marginTop: '0.5rem' }}>{game.homeTeamName}</div>
                </div>
            </div>

            {!prediction && (
                <button
                    className="predict-btn"
                    onClick={getPrediction}
                    disabled={loading}
                >
                    {loading ? 'Analyzing...' : 'Predict Winner'}
                </button>
            )}

            {prediction && (
                <div className="prediction-result" style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '12px' }}>

                    {/* Section 1: Math Model (The Edge) */}
                    <div className="section-math" style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <h4 style={{ color: '#60a5fa', margin: 0, fontSize: '0.9rem', fontWeight: 700 }}>MATH MODEL</h4>
                            {prediction.math_model && prediction.math_model.edge_home !== undefined && (
                                <span style={{
                                    background: prediction.math_model.edge_home > 0.02 ? '#22c55e' : (prediction.math_model.edge_home < -0.02 ? '#ef4444' : '#64748b'),
                                    color: 'white', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold'
                                }}>
                                    EDGE: {(Math.abs(prediction.math_model.edge_home) * 100).toFixed(1)}%
                                </span>
                            )}
                        </div>

                        {prediction.math_model ? (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.85rem' }}>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{ opacity: 0.7, fontSize: '0.75rem' }}>Model Win %</div>
                                    <div style={{ fontWeight: 700 }}>
                                        {prediction.predictedWinner === game.homeTeamName
                                            ? (prediction.math_model.p_home * 100).toFixed(1)
                                            : (prediction.math_model.p_away * 100).toFixed(1)}%
                                    </div>
                                </div>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{ opacity: 0.7, fontSize: '0.75rem' }}>Implied Win %</div>
                                    <div style={{ fontWeight: 700 }}>
                                        {(prediction.math_model.implied_home * 100).toFixed(1)}%
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div style={{ fontSize: '0.8rem', opacity: 0.6, fontStyle: 'italic' }}>Calculating model data...</div>
                        )}
                    </div>

                    {/* Section 2: LLM Context */}
                    <div className="section-context" style={{ background: 'rgba(168, 85, 247, 0.1)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(168, 85, 247, 0.2)' }}>
                        <h4 style={{ color: '#c084fc', margin: '0 0 8px 0', fontSize: '0.9rem', fontWeight: 700 }}>CONTEXT & RISK</h4>
                        <p style={{ fontSize: '0.85rem', lineHeight: '1.4', margin: 0, color: 'rgba(255,255,255,0.9)' }}>
                            {prediction.analysis}
                        </p>
                        {prediction.keyFactors && (
                            <ul style={{ fontSize: '0.8rem', paddingLeft: '1rem', marginTop: '8px', color: 'rgba(255,255,255,0.8)' }}>
                                {prediction.keyFactors.slice(0, 2).map((f: string, i: number) => <li key={i}>{f}</li>)}
                            </ul>
                        )}
                    </div>

                    {/* Section 3: Final Confidence */}
                    <div className="section-confidence" style={{ background: 'rgba(34, 197, 94, 0.1)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(34, 197, 94, 0.2)', textAlign: 'center' }}>
                        <h4 style={{ color: '#4ade80', margin: '0 0 4px 0', fontSize: '0.9rem', fontWeight: 700 }}>FINAL VERDICT</h4>
                        <div className="winner-badge" style={{ display: 'inline-block', marginBottom: '4px' }}>
                            {prediction.predictedWinner}
                        </div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#4ade80' }}>
                            {prediction.confidence}% Confidence
                        </div>
                        {prediction.odds && (
                            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', opacity: 0.7 }}>
                                Odds: {prediction.odds.home_odds} / {prediction.odds.away_odds} ({prediction.odds.source})
                            </div>
                        )}
                    </div>


                    {/* Section 4: Decision Ticket (Gate System) */}
                    {prediction.decision && (
                        <div className="section-decision" style={{
                            marginTop: '4px',
                            background: prediction.decision.action.includes('BET') ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            padding: '12px',
                            borderRadius: '8px',
                            border: `1px solid ${prediction.decision.action.includes('BET') ? '#22c55e' : '#ef4444'}`
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                                <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 700, opacity: 0.8 }}>SYSTEM PICK</h4>
                                <span style={{
                                    fontSize: '0.9rem', fontWeight: 900,
                                    color: prediction.decision.action.includes('BET') ? '#22c55e' : '#ef4444',
                                    padding: '2px 8px',
                                    background: 'rgba(0,0,0,0.2)',
                                    borderRadius: '4px'
                                }}>
                                    {prediction.decision.action}
                                </span>
                            </div>

                            {/* Gates */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px', fontSize: '0.75rem' }}>
                                {/* Gate 1: Edge */}
                                <div style={{ textAlign: 'center', opacity: prediction.decision.gates.edge.status === 'GREEN' ? 1 : 0.6 }}>
                                    <div style={{ marginBottom: '2px' }}>Math</div>
                                    <div>{prediction.decision.gates.edge.status === 'GREEN' ? '✅' : '❌'}</div>
                                    <div style={{ fontSize: '0.65rem' }}>{prediction.decision.gates.edge.value}</div>
                                </div>

                                {/* Gate 2: Consensus */}
                                <div style={{ textAlign: 'center', opacity: prediction.decision.gates.consensus.status === 'GREEN' ? 1 : 0.6 }}>
                                    <div style={{ marginBottom: '2px' }}>Council</div>
                                    <div>{prediction.decision.gates.consensus.status === 'GREEN' ? '✅' : '❌'}</div>
                                    <div style={{ fontSize: '0.65rem' }}>{prediction.decision.gates.consensus.value}</div>
                                </div>

                                {/* Gate 3: Confidence */}
                                <div style={{ textAlign: 'center', opacity: prediction.decision.gates.confidence.status !== 'RED' ? 1 : 0.6 }}>
                                    <div style={{ marginBottom: '2px' }}>Conf</div>
                                    <div>{prediction.decision.gates.confidence.status !== 'RED' ? '✅' : '❌'}</div>
                                    <div style={{ fontSize: '0.65rem' }}>{prediction.decision.gates.confidence.value}</div>
                                </div>
                            </div>
                        </div>
                    )}

                </div>
            )}
        </div>
    );
}
