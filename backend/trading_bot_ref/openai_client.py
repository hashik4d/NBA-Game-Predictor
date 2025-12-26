"""
OpenAI API Client for Stock Research.
Uses GPT-4 to analyze stocks with focus on market context and valuation.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import json

# Import shared ResearchResult
from .gemini_client import ResearchResult


class OpenAIClient:
    """
    Client for OpenAI GPT API stock research.
    Focuses on market context, competitive analysis, and valuation.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self._initialized = False
        
        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self._initialized = True
            except Exception as e:
                print(f"Failed to initialize OpenAI: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        return self._initialized and self.client is not None
    
    def research_stock(self, symbol: str, current_price: float,
                       context: Dict[str, Any] = None,
                       custom_prompt: str = None) -> Optional[ResearchResult]:
        """
        Research a stock using OpenAI API.
        Focuses on market context and competitive positioning.
        
        Args:
            symbol: Stock ticker symbol
            current_price: Current stock price
            context: Additional context
            custom_prompt: Optional custom prompt to use instead of building one
            
        Returns:
            ResearchResult with analysis
        """
        if not self.is_available():
            return None
        
        # Use custom prompt if provided, otherwise build one
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self._build_research_prompt(symbol, current_price, context)
        
        try:
            # Use higher max_tokens for portfolio analysis
            max_tokens = 4000 if custom_prompt else 1500
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional financial analyst. Provide conservative, well-reasoned stock analysis focused on protecting capital for beginner investors."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            # If using custom prompt (portfolio analysis), return full text response
            if custom_prompt:
                return ResearchResult(
                    source="openai",
                    symbol=symbol,
                    recommendation="HOLD",
                    confidence=0.7,
                    summary="Portfolio analysis completed",
                    bull_case="",
                    bear_case="",
                    key_risks=[],
                    price_target=None,
                    reasoning=response_text,  # Full response
                    raw_response=response_text
                )
            
            return self._parse_response(symbol, response_text)
            
        except Exception as e:
            print(f"OpenAI research error for {symbol}: {e}")
            return None
    
    def _build_research_prompt(self, symbol: str, current_price: float,
                                context: Dict[str, Any] = None) -> str:
        """Build a context-focused research prompt."""
        
        context_str = ""
        if context:
            if 'indicators' in context:
                context_str += f"\nTechnical Indicators: {json.dumps(context['indicators'], indent=2)}"
            if 'signal' in context:
                context_str += f"\nDetected Signal: {context['signal']}"
            if 'company_info' in context:
                context_str += f"\nCompany Info: {json.dumps(context['company_info'], indent=2)}"
        
        prompt = f"""Analyze the stock {symbol} currently trading at ${current_price:.2f}.

{context_str}

Provide comprehensive analysis focusing on:
1. Market context and macro environment
2. Competitive positioning
3. Valuation (is it overvalued/undervalued?)
4. Near-term catalysts (positive and negative)
5. Entry timing

Return your analysis in this exact JSON format:
{{
    "recommendation": "BUY" or "HOLD" or "SELL" or "AVOID",
    "confidence": 0.0 to 1.0,
    "summary": "2-3 sentence summary",
    "bull_case": "The bullish thesis",
    "bear_case": "The bearish thesis and risks",
    "key_risks": ["risk1", "risk2", "risk3"],
    "valuation_assessment": "overvalued" or "fairly_valued" or "undervalued",
    "price_target": null or number (12-month target),
    "near_term_catalysts": ["catalyst1", "catalyst2"],
    "entry_timing": "now" or "wait_for_pullback" or "avoid",
    "reasoning": "Detailed 2-3 paragraph analysis"
}}

Guidelines:
- Be balanced but err on the side of caution
- Consider current market environment
- Only recommend BUY if valuation and timing are favorable
- Account for the fact this advice is for a beginner investor

Respond ONLY with the JSON."""

        return prompt
    
    def _parse_response(self, symbol: str, response_text: str) -> ResearchResult:
        """Parse OpenAI response into ResearchResult."""
        
        try:
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            data = json.loads(response_text.strip())
            
            # Adjust recommendation based on valuation and timing
            recommendation = data.get('recommendation', 'HOLD').upper()
            confidence = float(data.get('confidence', 0.5))
            
            # Reduce confidence if overvalued or timing is bad
            if data.get('valuation_assessment') == 'overvalued':
                confidence *= 0.8
                if recommendation == 'BUY':
                    recommendation = 'HOLD'
            
            if data.get('entry_timing') == 'avoid':
                confidence *= 0.7
                if recommendation == 'BUY':
                    recommendation = 'AVOID'
            
            summary = data.get('summary', '')
            if data.get('valuation_assessment'):
                summary += f" Valuation: {data.get('valuation_assessment')}."
            if data.get('entry_timing'):
                summary += f" Timing: {data.get('entry_timing')}."
            
            return ResearchResult(
                source="openai",
                symbol=symbol,
                recommendation=recommendation,
                confidence=confidence,
                summary=summary,
                bull_case=data.get('bull_case', ''),
                bear_case=data.get('bear_case', ''),
                key_risks=data.get('key_risks', []),
                price_target=data.get('price_target'),
                reasoning=data.get('reasoning', ''),
                raw_response=response_text
            )
            
        except json.JSONDecodeError:
            # Return full response if JSON parsing fails
            return ResearchResult(
                source="openai",
                symbol=symbol,
                recommendation="HOLD",
                confidence=0.3,
                summary="Analysis completed (raw format)",
                bull_case="",
                bear_case="",
                key_risks=[],
                price_target=None,
                reasoning=response_text,  # Full response, not truncated
                raw_response=response_text
            )
    
    def get_market_analysis(self) -> Dict[str, Any]:
        """
        Get broad market analysis and outlook.
        
        Returns:
            Dict with market analysis
        """
        if not self.is_available():
            return {'available': False}
        
        prompt = """Provide a brief analysis of current market conditions for stock trading.

Return JSON format:
{
    "market_phase": "bull_market" or "bear_market" or "consolidation" or "correction",
    "risk_appetite": "risk_on" or "risk_off" or "neutral",
    "key_themes": ["theme1", "theme2", "theme3"],
    "sectors_favored": ["sector1", "sector2"],
    "sectors_to_avoid": ["sector1", "sector2"],
    "volatility_outlook": "low" or "moderate" or "high",
    "recommendation_for_beginners": "Stay cautious and focus on quality stocks",
    "summary": "2-3 sentence market outlook"
}

Respond ONLY with JSON."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a market analyst providing insights for beginner investors."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            return json.loads(response_text.strip())
            
        except Exception as e:
            return {
                'available': True,
                'error': str(e),
                'market_phase': 'unknown',
                'recommendation_for_beginners': 'Stay cautious until market clarity improves'
            }
