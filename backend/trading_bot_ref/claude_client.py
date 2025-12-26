"""
Anthropic Claude API Client for Stock Research.
Uses Claude to analyze stocks with a focus on risk assessment.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import json

# Import shared ResearchResult
from .gemini_client import ResearchResult


class ClaudeClient:
    """
    Client for Anthropic Claude API stock research.
    Claude is configured to be more conservative and risk-focused.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self._initialized = False
        
        if api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=api_key)
                self._initialized = True
            except Exception as e:
                print(f"Failed to initialize Claude: {e}")
    
    def is_available(self) -> bool:
        """Check if Claude API is available."""
        return self._initialized and self.client is not None
    
    def research_stock(self, symbol: str, current_price: float,
                       context: Dict[str, Any] = None,
                       custom_prompt: str = None) -> Optional[ResearchResult]:
        """
        Research a stock using Claude API.
        Claude is configured to be extra conservative and highlight risks.
        
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
            # Use higher max_tokens for portfolio analysis
            max_tokens = 4000 if custom_prompt else 1500
            
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # If using custom prompt (portfolio analysis), return full text response
            if custom_prompt:
                return ResearchResult(
                    source="claude",
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
            print(f"Claude research error for {symbol}: {e}")
            return None
    
    def _build_research_prompt(self, symbol: str, current_price: float,
                                context: Dict[str, Any] = None) -> str:
        """Build a risk-focused research prompt for Claude."""
        
        context_str = ""
        if context:
            if 'indicators' in context:
                context_str += f"\nTechnical Indicators: {json.dumps(context['indicators'], indent=2)}"
            if 'signal' in context:
                context_str += f"\nDetected Signal: {context['signal']}"
            if 'company_info' in context:
                context_str += f"\nCompany Info: {json.dumps(context['company_info'], indent=2)}"
        
        prompt = f"""You are a conservative financial analyst focused on RISK MANAGEMENT and CAPITAL PRESERVATION.

Analyze the stock {symbol} currently trading at ${current_price:.2f}.

{context_str}

Your analysis should be CONSERVATIVE - protecting capital is the priority. A beginner investor is relying on your advice.

Provide your analysis in this exact JSON format:
{{
    "recommendation": "BUY" or "HOLD" or "SELL" or "AVOID",
    "confidence": 0.0 to 1.0,
    "summary": "2-3 sentence conservative summary",
    "bull_case": "The bullish case (be skeptical)",
    "bear_case": "The bearish case and downside risks (be thorough)",
    "key_risks": ["risk1", "risk2", "risk3", "risk4", "risk5"],
    "price_target": null or a number,
    "max_downside": "What's the worst case scenario and potential loss",
    "suitable_for_beginners": true or false,
    "reasoning": "Detailed 2-3 paragraph conservative analysis"
}}

IMPORTANT GUIDELINES:
1. Err on the side of CAUTION - if unclear, recommend AVOID
2. Only recommend BUY if risk/reward is clearly favorable
3. Always assume things can get worse than expected
4. Highlight AT LEAST 5 specific risks
5. Consider: Is this appropriate for someone who can't afford to lose money?
6. Be honest about uncertainty - markets are unpredictable

Respond ONLY with the JSON, no additional text."""

        return prompt
    
    def _parse_response(self, symbol: str, response_text: str) -> ResearchResult:
        """Parse Claude response into ResearchResult."""
        
        try:
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            data = json.loads(response_text.strip())
            
            # Claude's conservative nature - adjust confidence down if not suitable for beginners
            confidence = float(data.get('confidence', 0.5))
            if not data.get('suitable_for_beginners', True):
                confidence *= 0.8  # Reduce confidence for risky stocks
            
            summary = data.get('summary', '')
            if data.get('max_downside'):
                summary += f" Max downside: {data['max_downside']}"
            
            return ResearchResult(
                source="claude",
                symbol=symbol,
                recommendation=data.get('recommendation', 'HOLD').upper(),
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
                source="claude",
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
    
    def analyze_risk(self, symbol: str, entry_price: float, 
                     position_size: float) -> Dict[str, Any]:
        """
        Get detailed risk analysis for a potential trade.
        
        Returns:
            Dict with risk assessment details
        """
        if not self.is_available():
            return {'available': False}
        
        prompt = f"""Analyze the risk of buying {symbol} at ${entry_price:.2f} with a position size of ${position_size:.2f}.

Provide a risk assessment in JSON format:
{{
    "risk_level": "LOW" or "MEDIUM" or "HIGH" or "EXTREME",
    "risk_score": 1-10 (10 being highest risk),
    "max_recommended_position": percentage of portfolio (be conservative),
    "suggested_stop_loss_percent": recommended stop loss percentage,
    "key_concerns": ["concern1", "concern2", "concern3"],
    "worst_case_loss": estimated dollar loss in bad scenario,
    "recommendation": "Proceed with caution" or "Consider smaller size" or "Avoid",
    "reasoning": "Brief explanation"
}}

Be CONSERVATIVE. Protect capital.
Respond ONLY with JSON."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            return json.loads(response_text.strip())
            
        except Exception as e:
            return {
                'available': True,
                'error': str(e),
                'risk_level': 'HIGH',
                'recommendation': 'Unable to assess - proceed with caution'
            }
