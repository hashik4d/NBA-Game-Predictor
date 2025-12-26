"""
Google Gemini API Client for Stock Research.
Uses Gemini to analyze stocks and provide trading insights.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class ResearchResult:
    """Result from AI research."""
    source: str
    symbol: str
    recommendation: str  # 'BUY', 'HOLD', 'SELL', 'AVOID'
    confidence: float  # 0.0 to 1.0
    summary: str
    bull_case: str
    bear_case: str
    key_risks: list
    price_target: Optional[float]
    reasoning: str
    raw_response: str = ""


class GeminiClient:
    """
    Client for Google Gemini API stock research.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = None
        self._initialized = False
        
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                self._initialized = True
            except Exception as e:
                print(f"Failed to initialize Gemini: {e}")
    
    def is_available(self) -> bool:
        """Check if Gemini API is available."""
        return self._initialized and self.model is not None
    
    def research_stock(self, symbol: str, current_price: float,
                       context: Dict[str, Any] = None,
                       custom_prompt: str = None) -> Optional[ResearchResult]:
        """
        Research a stock using Gemini API.
        
        Args:
            symbol: Stock ticker symbol
            current_price: Current stock price
            context: Additional context (technical indicators, news, etc.)
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
            # Set higher token limit for portfolio analysis
            generation_config = None
            if custom_prompt:
                generation_config = {"max_output_tokens": 4000}
                
            response = self.model.generate_content(prompt, generation_config=generation_config)
            response_text = response.text
            
            # If using custom prompt (portfolio analysis), return full text response
            if custom_prompt:
                return ResearchResult(
                    source="gemini",
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
            print(f"Gemini research error for {symbol}: {e}")
            return None
    
    def _build_research_prompt(self, symbol: str, current_price: float,
                                context: Dict[str, Any] = None) -> str:
        """Build a comprehensive research prompt."""
        
        context_str = ""
        if context:
            if 'indicators' in context:
                context_str += f"\nTechnical Indicators: {json.dumps(context['indicators'], indent=2)}"
            if 'signal' in context:
                context_str += f"\nDetected Signal: {context['signal']}"
            if 'company_info' in context:
                context_str += f"\nCompany Info: {json.dumps(context['company_info'], indent=2)}"
        
        prompt = f"""You are an expert financial analyst. Analyze the stock {symbol} currently trading at ${current_price:.2f}.

{context_str}

Provide a comprehensive analysis in the following JSON format:
{{
    "recommendation": "BUY" or "HOLD" or "SELL" or "AVOID",
    "confidence": 0.0 to 1.0 (how confident you are in this recommendation),
    "summary": "2-3 sentence summary of your analysis",
    "bull_case": "The bullish case for this stock",
    "bear_case": "The bearish case and risks",
    "key_risks": ["risk1", "risk2", "risk3"],
    "price_target": null or a number (12-month price target if you have conviction),
    "reasoning": "Detailed 2-3 paragraph reasoning for your recommendation"
}}

Important guidelines:
1. Be conservative - when in doubt, recommend HOLD or AVOID
2. Consider both fundamental and technical factors
3. Account for current market conditions
4. Highlight risks prominently
5. Only give BUY with high confidence if you see strong value and limited downside
6. Consider if the stock is suitable for a beginner investor

Respond ONLY with the JSON, no additional text."""

        return prompt
    
    def _parse_response(self, symbol: str, response_text: str) -> ResearchResult:
        """Parse Gemini response into ResearchResult."""
        
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            data = json.loads(response_text.strip())
            
            return ResearchResult(
                source="gemini",
                symbol=symbol,
                recommendation=data.get('recommendation', 'HOLD').upper(),
                confidence=float(data.get('confidence', 0.5)),
                summary=data.get('summary', ''),
                bull_case=data.get('bull_case', ''),
                bear_case=data.get('bear_case', ''),
                key_risks=data.get('key_risks', []),
                price_target=data.get('price_target'),
                reasoning=data.get('reasoning', ''),
                raw_response=response_text
            )
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return full response as reasoning
            return ResearchResult(
                source="gemini",
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
    
    def get_market_sentiment(self, symbols: list = None) -> Dict[str, Any]:
        """
        Get general market sentiment analysis.
        
        Returns:
            Dict with market sentiment and outlook
        """
        if not self.is_available():
            return {'available': False}
        
        prompt = """Provide a brief market sentiment analysis for today's trading session.

Return JSON format:
{
    "overall_sentiment": "bullish" or "bearish" or "neutral",
    "confidence": 0.0 to 1.0,
    "key_factors": ["factor1", "factor2", "factor3"],
    "sectors_to_watch": ["sector1", "sector2"],
    "risks_today": ["risk1", "risk2"],
    "summary": "2-3 sentence market outlook"
}

Respond ONLY with JSON."""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean JSON
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            return json.loads(response_text.strip())
            
        except Exception as e:
            return {
                'available': True,
                'error': str(e),
                'overall_sentiment': 'neutral',
                'confidence': 0.3
            }
