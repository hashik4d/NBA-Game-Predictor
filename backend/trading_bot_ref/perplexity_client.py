"""
Perplexity AI Client - Uses Perplexity's Sonar models with web search capabilities.

Perplexity provides grounded responses with citations from Bloomberg, Reuters, etc.
"""

import os
from typing import Optional, List
from dataclasses import dataclass

# Reuse the ResearchResult from gemini_client
from .gemini_client import ResearchResult


class PerplexityClient:
    """
    Client for Perplexity AI with web search capabilities.
    Uses sonar-pro model for deep research with citations.
    """
    
    def __init__(self, api_key: str):
        """Initialize with Perplexity API key."""
        self.api_key = api_key
        self.model = "sonar-pro"  # Best for research with citations
        self.base_url = "https://api.perplexity.ai"
        
        # Import OpenAI client for Perplexity (compatible API)
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key,
                base_url=self.base_url
            )
        except ImportError:
            raise ImportError("openai package required for Perplexity. Run: pip install openai")
    
    def research_stock(self, symbol: str, current_price: float, 
                       custom_prompt: str = None) -> Optional[ResearchResult]:
        """
        Research a stock using Perplexity with web search.
        
        Args:
            symbol: Stock ticker
            current_price: Current price
            custom_prompt: Optional custom prompt for portfolio analysis
            
        Returns:
            ResearchResult with web-grounded analysis and citations
        """
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = f"""Analyze {symbol} stock currently trading at ${current_price:.2f}.

Search for the latest news and analyst reports from:
- Bloomberg
- Reuters
- Wall Street Journal
- CNBC
- Seeking Alpha
- Recent SEC filings

Provide:
1. **Recommendation**: BUY, HOLD, or SELL
2. **Confidence**: 0-100%
3. **Price Target**: Based on analyst consensus
4. **Key Catalysts**: 2-3 upcoming events
5. **Key Risks**: 2-3 main risks
6. **Recent News**: 2-3 relevant headlines from the past week
7. **Analyst Sentiment**: Recent upgrades/downgrades

Include citations for each piece of information."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst with access to real-time market data, news, and analyst reports. Always cite your sources."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            if not response.choices:
                return None
            
            content = response.choices[0].message.content
            
            # Extract citations if available
            citations = []
            if hasattr(response, 'citations') and response.citations:
                citations = response.citations
            
            # Parse the response
            recommendation = self._extract_recommendation(content)
            confidence = self._extract_confidence(content)
            price_target = self._extract_price_target(content)
            risks = self._extract_risks(content)
            
            return ResearchResult(
                source="perplexity",
                symbol=symbol,
                recommendation=recommendation,
                confidence=confidence,
                summary=content[:500] if content else "",
                bull_case="",
                bear_case="",
                key_risks=risks,
                price_target=price_target,
                reasoning=content,
                raw_response=content
            )
            
        except Exception as e:
            print(f"   ⚠️  Perplexity error: {e}")
            return None
    
    def search_market_news(self, symbols: List[str]) -> str:
        """
        Search for latest market news on given symbols.
        
        Returns:
            Formatted news summary with citations
        """
        symbols_str = ", ".join(symbols)
        prompt = f"""Search for the latest financial news and market analysis for these stocks: {symbols_str}

Focus on:
1. Bloomberg Terminal reports
2. Reuters financial news
3. Wall Street Journal articles
4. Analyst upgrades/downgrades this week
5. Upcoming earnings dates
6. Recent insider trading activity
7. Institutional buying/selling

Format with clear sections and include source URLs for each piece of information."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial news aggregator. Search for and summarize the latest market news with citations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            if response.choices:
                return response.choices[0].message.content
            return ""
            
        except Exception as e:
            return f"Error fetching news: {e}"
    
    def _extract_recommendation(self, text: str) -> str:
        """Extract recommendation from response."""
        text_upper = text.upper()
        if "STRONG BUY" in text_upper:
            return "BUY"
        elif "BUY" in text_upper and "SELL" not in text_upper[:text_upper.find("BUY")+50]:
            return "BUY"
        elif "SELL" in text_upper:
            return "SELL"
        elif "HOLD" in text_upper:
            return "HOLD"
        return "HOLD"
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence from response."""
        import re
        # Look for percentage patterns
        patterns = [
            r'confidence[:\s]+(\d+)%',
            r'(\d+)%\s*confidence',
            r'confidence[:\s]+(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return min(float(match.group(1)) / 100, 1.0)
        return 0.6  # Default moderate confidence
    
    def _extract_price_target(self, text: str) -> Optional[float]:
        """Extract price target from response."""
        import re
        patterns = [
            r'price target[:\s]+\$?(\d+\.?\d*)',
            r'target[:\s]+\$?(\d+\.?\d*)',
            r'\$(\d+\.?\d*)\s*target',
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1))
        return None
    
    def _extract_risks(self, text: str) -> List[str]:
        """Extract risks from response."""
        risks = []
        lines = text.split('\n')
        in_risks_section = False
        
        for line in lines:
            if 'risk' in line.lower() and ':' in line:
                in_risks_section = True
                continue
            if in_risks_section:
                if line.strip().startswith(('-', '•', '*', '1', '2', '3')):
                    risk = line.strip().lstrip('-•*123456789. ')
                    if risk and len(risk) < 200:
                        risks.append(risk)
                elif line.strip() == '' or any(x in line.lower() for x in ['catalyst', 'news', 'recommend']):
                    in_risks_section = False
        
        return risks[:5]
    
    def _extract_catalysts(self, text: str) -> List[str]:
        """Extract catalysts from response."""
        catalysts = []
        lines = text.split('\n')
        in_catalysts_section = False
        
        for line in lines:
            if 'catalyst' in line.lower() and ':' in line:
                in_catalysts_section = True
                continue
            if in_catalysts_section:
                if line.strip().startswith(('-', '•', '*', '1', '2', '3')):
                    catalyst = line.strip().lstrip('-•*123456789. ')
                    if catalyst and len(catalyst) < 200:
                        catalysts.append(catalyst)
                elif line.strip() == '' or any(x in line.lower() for x in ['risk', 'news', 'recommend']):
                    in_catalysts_section = False
        
        return catalysts[:5]
