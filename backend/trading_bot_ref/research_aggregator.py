"""
Research Aggregator - Combines research from multiple AI sources.
Generates consensus recommendations and flags disagreements.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import statistics

from .gemini_client import GeminiClient, ResearchResult
from .claude_client import ClaudeClient
from .openai_client import OpenAIClient


@dataclass
class AggregatedResearch:
    """Combined research from all AI sources."""
    symbol: str
    timestamp: datetime
    
    # Individual results
    gemini_result: Optional[ResearchResult] = None
    claude_result: Optional[ResearchResult] = None
    openai_result: Optional[ResearchResult] = None
    
    # Aggregated recommendation
    consensus_recommendation: str = "HOLD"
    consensus_confidence: float = 0.5
    agreement_level: str = "none"  # "full", "partial", "none"
    
    # Combined analysis
    combined_summary: str = ""
    all_risks: List[str] = field(default_factory=list)
    average_price_target: Optional[float] = None
    
    # Flags
    has_disagreement: bool = False
    disagreement_details: str = ""
    sources_used: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'consensus_recommendation': self.consensus_recommendation,
            'consensus_confidence': self.consensus_confidence,
            'agreement_level': self.agreement_level,
            'combined_summary': self.combined_summary,
            'all_risks': self.all_risks,
            'average_price_target': self.average_price_target,
            'has_disagreement': self.has_disagreement,
            'disagreement_details': self.disagreement_details,
            'sources_used': self.sources_used,
            'individual_results': {
                'gemini': self.gemini_result.recommendation if self.gemini_result else None,
                'claude': self.claude_result.recommendation if self.claude_result else None,
                'openai': self.openai_result.recommendation if self.openai_result else None
            }
        }


class ResearchAggregator:
    """
    Aggregates research from multiple AI sources and generates
    consensus recommendations.
    """
    
    # Recommendation weights for voting
    RECOMMENDATION_SCORES = {
        'BUY': 3,
        'HOLD': 2,
        'SELL': 1,
        'AVOID': 0
    }
    
    SCORE_TO_RECOMMENDATION = {
        3: 'BUY',
        2: 'HOLD',
        1: 'SELL',
        0: 'AVOID'
    }
    
    def __init__(self, gemini_key: str = "", claude_key: str = "", openai_key: str = ""):
        """
        Initialize with API keys for each service.
        """
        self.gemini_client = GeminiClient(gemini_key) if gemini_key else None
        self.claude_client = ClaudeClient(claude_key) if claude_key else None
        self.openai_client = OpenAIClient(openai_key) if openai_key else None
        
        self.available_sources = []
        if self.gemini_client and self.gemini_client.is_available():
            self.available_sources.append('gemini')
        if self.claude_client and self.claude_client.is_available():
            self.available_sources.append('claude')
        if self.openai_client and self.openai_client.is_available():
            self.available_sources.append('openai')
    
    def get_available_sources(self) -> List[str]:
        """Return list of available AI sources."""
        return self.available_sources.copy()
    
    def research_stock(self, symbol: str, current_price: float,
                       context: Dict[str, Any] = None,
                       min_sources: int = 1) -> Optional[AggregatedResearch]:
        """
        Research a stock using all available AI sources.
        
        Args:
            symbol: Stock ticker
            current_price: Current price
            context: Additional context for research
            min_sources: Minimum sources required for valid result
            
        Returns:
            AggregatedResearch with consensus recommendation
        """
        if len(self.available_sources) < min_sources:
            print(f"Not enough AI sources available. Need {min_sources}, have {len(self.available_sources)}")
            return None
        
        results = []
        
        # Get research from each available source
        gemini_result = None
        claude_result = None
        openai_result = None
        
        if 'gemini' in self.available_sources:
            gemini_result = self.gemini_client.research_stock(symbol, current_price, context)
            if gemini_result:
                results.append(gemini_result)
        
        if 'claude' in self.available_sources:
            claude_result = self.claude_client.research_stock(symbol, current_price, context)
            if claude_result:
                results.append(claude_result)
        
        if 'openai' in self.available_sources:
            openai_result = self.openai_client.research_stock(symbol, current_price, context)
            if openai_result:
                results.append(openai_result)
        
        if len(results) < min_sources:
            print(f"Only {len(results)} sources returned results, need {min_sources}")
            return None
        
        # Aggregate results
        return self._aggregate_results(
            symbol=symbol,
            gemini_result=gemini_result,
            claude_result=claude_result,
            openai_result=openai_result,
            results=results
        )
    
    def _aggregate_results(self, symbol: str,
                           gemini_result: Optional[ResearchResult],
                           claude_result: Optional[ResearchResult],
                           openai_result: Optional[ResearchResult],
                           results: List[ResearchResult]) -> AggregatedResearch:
        """
        Aggregate individual results into consensus.
        """
        aggregated = AggregatedResearch(
            symbol=symbol,
            timestamp=datetime.now(),
            gemini_result=gemini_result,
            claude_result=claude_result,
            openai_result=openai_result,
            sources_used=len(results)
        )
        
        if not results:
            return aggregated
        
        # Get all recommendations
        recommendations = [r.recommendation for r in results]
        confidences = [r.confidence for r in results]
        
        # Check for agreement
        unique_recs = set(recommendations)
        if len(unique_recs) == 1:
            aggregated.agreement_level = "full"
            aggregated.consensus_recommendation = recommendations[0]
            aggregated.consensus_confidence = statistics.mean(confidences)
        elif len(unique_recs) == 2:
            aggregated.agreement_level = "partial"
            aggregated.has_disagreement = True
            
            # Use weighted voting
            aggregated.consensus_recommendation = self._weighted_vote(results)
            aggregated.consensus_confidence = statistics.mean(confidences) * 0.8  # Reduce confidence
            
            # Document disagreement
            aggregated.disagreement_details = f"Sources disagree: {', '.join([f'{r.source}={r.recommendation}' for r in results])}"
        else:
            aggregated.agreement_level = "none"
            aggregated.has_disagreement = True
            
            # All sources disagree - default to most conservative
            aggregated.consensus_recommendation = self._most_conservative(recommendations)
            aggregated.consensus_confidence = min(confidences) * 0.6  # Significantly reduce confidence
            aggregated.disagreement_details = f"Major disagreement: {', '.join([f'{r.source}={r.recommendation}' for r in results])}. Defaulting to conservative recommendation."
        
        # Combine summaries
        summaries = [r.summary for r in results if r.summary]
        aggregated.combined_summary = " | ".join(summaries) if summaries else ""
        
        # Collect all risks (deduplicated)
        all_risks = []
        seen_risks = set()
        for result in results:
            for risk in result.key_risks:
                risk_lower = risk.lower()
                if risk_lower not in seen_risks:
                    all_risks.append(risk)
                    seen_risks.add(risk_lower)
        aggregated.all_risks = all_risks
        
        # Average price targets
        price_targets = [r.price_target for r in results if r.price_target is not None]
        if price_targets:
            aggregated.average_price_target = statistics.mean(price_targets)
        
        return aggregated
    
    def _weighted_vote(self, results: List[ResearchResult]) -> str:
        """
        Perform weighted voting based on confidence.
        """
        scores = {}
        for result in results:
            rec = result.recommendation
            if rec not in scores:
                scores[rec] = 0
            scores[rec] += result.confidence
        
        # Return recommendation with highest weighted score
        return max(scores, key=scores.get)
    
    def _most_conservative(self, recommendations: List[str]) -> str:
        """
        Return the most conservative recommendation.
        Order: AVOID > SELL > HOLD > BUY
        """
        priority = ['AVOID', 'SELL', 'HOLD', 'BUY']
        for rec in priority:
            if rec in recommendations:
                return rec
        return 'HOLD'
    
    def get_research_report(self, aggregated: AggregatedResearch) -> str:
        """
        Generate a formatted research report.
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"📊 RESEARCH REPORT: {aggregated.symbol}")
        lines.append("=" * 60)
        lines.append("")
        
        # Consensus
        rec_emoji = {
            'BUY': '🟢',
            'HOLD': '🟡',
            'SELL': '🔴',
            'AVOID': '⛔'
        }
        emoji = rec_emoji.get(aggregated.consensus_recommendation, '❓')
        
        lines.append(f"📌 CONSENSUS: {emoji} {aggregated.consensus_recommendation}")
        lines.append(f"📈 Confidence: {aggregated.consensus_confidence:.0%}")
        lines.append(f"🤝 Agreement: {aggregated.agreement_level}")
        lines.append("")
        
        # Disagreement warning
        if aggregated.has_disagreement:
            lines.append("⚠️  WARNING: AI sources disagree!")
            lines.append(f"   {aggregated.disagreement_details}")
            lines.append("")
        
        # Individual source results
        lines.append("📋 Individual Analysis:")
        lines.append("-" * 40)
        
        if aggregated.gemini_result:
            g = aggregated.gemini_result
            lines.append(f"  Gemini: {g.recommendation} ({g.confidence:.0%})")
            lines.append(f"    {g.summary[:100]}...")
        
        if aggregated.claude_result:
            c = aggregated.claude_result
            lines.append(f"  Claude: {c.recommendation} ({c.confidence:.0%})")
            lines.append(f"    {c.summary[:100]}...")
        
        if aggregated.openai_result:
            o = aggregated.openai_result
            lines.append(f"  OpenAI: {o.recommendation} ({o.confidence:.0%})")
            lines.append(f"    {o.summary[:100]}...")
        
        lines.append("")
        
        # Price target
        if aggregated.average_price_target:
            lines.append(f"🎯 Average Price Target: ${aggregated.average_price_target:.2f}")
            lines.append("")
        
        # Risks
        if aggregated.all_risks:
            lines.append("⚠️  KEY RISKS:")
            for i, risk in enumerate(aggregated.all_risks[:7], 1):
                lines.append(f"   {i}. {risk}")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def should_trade(self, aggregated: AggregatedResearch,
                     min_confidence: float = 0.7,
                     require_agreement: bool = True) -> tuple[bool, str]:
        """
        Determine if we should proceed with a trade based on research.
        
        Returns:
            Tuple of (should_trade, reason)
        """
        # Must have consensus BUY recommendation
        if aggregated.consensus_recommendation != 'BUY':
            return False, f"Recommendation is {aggregated.consensus_recommendation}, not BUY"
        
        # Check confidence threshold
        if aggregated.consensus_confidence < min_confidence:
            return False, f"Confidence {aggregated.consensus_confidence:.0%} below threshold {min_confidence:.0%}"
        
        # Check for agreement if required
        if require_agreement and aggregated.agreement_level == "none":
            return False, "AI sources have major disagreement"
        
        # All checks passed
        return True, "Research supports trade"
