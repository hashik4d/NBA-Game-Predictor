"""
Portfolio Analyzer - Deep AI analysis of current portfolio positions.

Uses OpenAI, Claude, Gemini, and Perplexity (with web search) to analyze 
all positions and provide recommendations based on current market conditions.

Now with 4 AI sources and 3/4 consensus voting!
"""

import os
import webbrowser
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class PositionAnalysis:
    """Analysis result for a single position."""
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    
    # AI recommendations
    gemini_recommendation: str = ""
    gemini_reasoning: str = ""
    claude_recommendation: str = ""
    claude_reasoning: str = ""
    openai_recommendation: str = ""
    openai_reasoning: str = ""
    perplexity_recommendation: str = ""
    perplexity_reasoning: str = ""
    
    # Consensus
    consensus_recommendation: str = ""
    confidence_score: float = 0.0
    key_risks: List[str] = field(default_factory=list)
    key_catalysts: List[str] = field(default_factory=list)


@dataclass
class PortfolioAnalysisResult:
    """Complete portfolio analysis result."""
    timestamp: datetime
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    positions: List[PositionAnalysis]
    
    # Portfolio-level insights
    portfolio_health: str = ""  # HEALTHY, MODERATE_RISK, HIGH_RISK
    diversification_score: str = ""
    sector_exposure: Dict[str, float] = field(default_factory=dict)
    overall_recommendation: str = ""
    market_outlook: str = ""
    
    # Per-source analysis
    gemini_portfolio_analysis: str = ""
    claude_portfolio_analysis: str = ""
    openai_portfolio_analysis: str = ""
    perplexity_portfolio_analysis: str = ""
    
    # Web search data from Perplexity
    market_news: str = ""
    sources_cited: List[str] = field(default_factory=list)
    
    # Consensus (3 out of 4)
    consensus_count: int = 0
    consensus_reached: bool = False


class PortfolioAnalyzer:
    """
    Analyzes portfolio positions using multiple AI models.
    Now with Perplexity for web search and 3/4 consensus voting.
    """
    
    def __init__(self, gemini_key: str = "", claude_key: str = "", 
                 openai_key: str = "", perplexity_key: str = ""):
        """Initialize with API keys."""
        self.gemini_key = gemini_key
        self.claude_key = claude_key
        self.openai_key = openai_key
        self.perplexity_key = perplexity_key
        
        # Initialize clients
        self.gemini_client = None
        self.claude_client = None
        self.openai_client = None
        self.perplexity_client = None
        
        if gemini_key:
            try:
                from .gemini_client import GeminiClient
                self.gemini_client = GeminiClient(gemini_key)
            except Exception as e:
                print(f"⚠️  Gemini initialization failed: {e}")
        
        if claude_key:
            try:
                from .claude_client import ClaudeClient
                self.claude_client = ClaudeClient(claude_key)
            except Exception as e:
                print(f"⚠️  Claude initialization failed: {e}")
        
        if openai_key:
            try:
                from .openai_client import OpenAIClient
                self.openai_client = OpenAIClient(openai_key)
            except Exception as e:
                print(f"⚠️  OpenAI initialization failed: {e}")
        
        if perplexity_key:
            try:
                from .perplexity_client import PerplexityClient
                self.perplexity_client = PerplexityClient(perplexity_key)
            except Exception as e:
                print(f"⚠️  Perplexity initialization failed: {e}")
    
    def get_available_sources(self) -> List[str]:
        """Return list of available AI sources."""
        sources = []
        if self.gemini_client:
            sources.append("gemini")
        if self.claude_client:
            sources.append("claude")
        if self.openai_client:
            sources.append("openai")
        if self.perplexity_client:
            sources.append("perplexity")
        return sources
    
    def _build_portfolio_prompt(self, positions: List[Dict], total_value: float) -> str:
        """Build a comprehensive prompt for portfolio analysis."""
        
        # Build position details
        position_details = []
        for pos in positions:
            pnl_pct = pos.get('pnl_pct', 0)
            emoji = "🟢" if pnl_pct >= 0 else "🔴"
            position_details.append(
                f"- {pos['symbol']}: {pos['quantity']:.2f} shares\n"
                f"  Avg Cost: ${pos['avg_cost']:.2f} | Current: ${pos['current_price']:.2f}\n"
                f"  Value: ${pos['market_value']:.2f} | P/L: {emoji} {pnl_pct:+.2f}%"
            )
        
        positions_text = "\n".join(position_details)
        
        prompt = f"""You are a professional Wall Street portfolio analyst. Analyze this portfolio and provide actionable recommendations.

PORTFOLIO SUMMARY:
- Total Value: ${total_value:,.2f}
- Number of Positions: {len(positions)}
- Date: {datetime.now().strftime('%Y-%m-%d')}

CURRENT POSITIONS:
{positions_text}

Please provide:

1. **PER-POSITION ANALYSIS** - For each stock, give:
   - Recommendation: BUY MORE / HOLD / TRIM / SELL
   - Key reasoning (2-3 sentences)
   - Current risk level (LOW/MEDIUM/HIGH)

2. **PORTFOLIO-LEVEL INSIGHTS**:
   - Overall portfolio health assessment
   - Diversification analysis
   - Sector concentration risks
   - Suggestions for rebalancing

3. **MARKET CONTEXT**:
   - How current market conditions affect this portfolio
   - Key macroeconomic factors to watch
   - Upcoming events that could impact these holdings

4. **TOP 3 ACTION ITEMS**:
   - Most urgent actions to take with this portfolio

Be specific, data-driven, and consider current Wall Street sentiment and market conditions as of December 2024.
"""
        return prompt
    
    def _build_perplexity_prompt(self, positions: List[Dict], total_value: float) -> str:
        """Build prompt specifically for Perplexity with web search."""
        symbols = [pos['symbol'] for pos in positions]
        symbols_str = ", ".join(symbols)
        
        prompt = f"""Search the web for the latest financial news and analyst reports for this portfolio.

PORTFOLIO: {symbols_str}
Total Value: ${total_value:,.2f}

Search for and include:
1. **Latest News** (past 7 days) - From Bloomberg, Reuters, CNBC, WSJ
2. **Analyst Ratings** - Recent upgrades/downgrades for each stock
3. **Price Targets** - Current analyst consensus price targets
4. **Earnings Dates** - Upcoming earnings for these stocks
5. **Insider Activity** - Recent insider buying/selling
6. **Institutional Holdings** - Major fund positions changes

For each stock, provide:
- Recommendation: BUY MORE / HOLD / TRIM / SELL
- Key reasoning based on the news you found
- Sources (include URLs when possible)

End with a summary of the most important market-moving information.

IMPORTANT: Cite your sources with [Source Name] for each piece of information."""
        
        return prompt
    
    def analyze_portfolio(self, positions: List[Dict], total_value: float) -> PortfolioAnalysisResult:
        """
        Analyze the full portfolio using all available AI models (4 sources).
        
        Args:
            positions: List of position dictionaries
            total_value: Total portfolio value
            
        Returns:
            PortfolioAnalysisResult with comprehensive analysis
        """
        print("\n🔬 Analyzing portfolio with AI...")
        print(f"   Positions: {len(positions)}")
        print(f"   Total Value: ${total_value:,.2f}")
        print(f"   AI Sources: {self.get_available_sources()}")
        print(f"   Consensus Required: 3 out of {len(self.get_available_sources())}")
        
        # Calculate totals
        total_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions)
        total_pnl_pct = (total_pnl / (total_value - total_pnl)) * 100 if total_value > total_pnl else 0
        
        # Build prompts
        prompt = self._build_portfolio_prompt(positions, total_value)
        perplexity_prompt = self._build_perplexity_prompt(positions, total_value)
        
        # Get analysis from each AI
        gemini_analysis = ""
        claude_analysis = ""
        openai_analysis = ""
        perplexity_analysis = ""
        market_news = ""
        
        if self.gemini_client:
            print("   📡 Consulting Gemini...")
            try:
                result = self.gemini_client.research_stock("PORTFOLIO", 0, custom_prompt=prompt)
                if result:
                    gemini_analysis = result.reasoning
            except Exception as e:
                print(f"   ⚠️  Gemini error: {e}")
        
        if self.claude_client:
            print("   📡 Consulting Claude...")
            try:
                result = self.claude_client.research_stock("PORTFOLIO", 0, custom_prompt=prompt)
                if result:
                    claude_analysis = result.reasoning
            except Exception as e:
                print(f"   ⚠️  Claude error: {e}")
        
        if self.openai_client:
            print("   📡 Consulting OpenAI...")
            try:
                result = self.openai_client.research_stock("PORTFOLIO", 0, custom_prompt=prompt)
                if result:
                    openai_analysis = result.reasoning
            except Exception as e:
                print(f"   ⚠️  OpenAI error: {e}")
        
        if self.perplexity_client:
            print("   🌐 Consulting Perplexity (with web search)...")
            try:
                result = self.perplexity_client.research_stock("PORTFOLIO", 0, custom_prompt=perplexity_prompt)
                if result:
                    perplexity_analysis = result.reasoning
                # Also get market news
                symbols = [pos['symbol'] for pos in positions]
                market_news = self.perplexity_client.search_market_news(symbols)
            except Exception as e:
                print(f"   ⚠️  Perplexity error: {e}")
        
        # Build position analyses
        position_analyses = []
        for pos in positions:
            pa = PositionAnalysis(
                symbol=pos['symbol'],
                quantity=pos['quantity'],
                avg_cost=pos['avg_cost'],
                current_price=pos['current_price'],
                market_value=pos['market_value'],
                unrealized_pnl=pos.get('unrealized_pnl', 0),
                unrealized_pnl_pct=pos.get('pnl_pct', 0)
            )
            position_analyses.append(pa)
        
        # Count successful responses for consensus
        responses = [gemini_analysis, claude_analysis, openai_analysis, perplexity_analysis]
        consensus_count = sum(1 for r in responses if r)
        consensus_reached = consensus_count >= 3
        
        # Create result
        result = PortfolioAnalysisResult(
            timestamp=datetime.now(),
            total_value=total_value,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            positions=position_analyses,
            gemini_portfolio_analysis=gemini_analysis,
            claude_portfolio_analysis=claude_analysis,
            openai_portfolio_analysis=openai_analysis,
            perplexity_portfolio_analysis=perplexity_analysis,
            market_news=market_news,
            consensus_count=consensus_count,
            consensus_reached=consensus_reached
        )
        
        return result
    
    def get_analysis_report(self, result: PortfolioAnalysisResult) -> str:
        """Generate a formatted analysis report."""
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("📊 AI PORTFOLIO ANALYSIS REPORT")
        lines.append("=" * 70)
        
        # Summary
        lines.append(f"\n📅 Analysis Date: {result.timestamp.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"💰 Total Portfolio Value: ${result.total_value:,.2f}")
        pnl_emoji = "🟢" if result.total_pnl >= 0 else "🔴"
        lines.append(f"📈 Unrealized P/L: {pnl_emoji} ${result.total_pnl:+,.2f} ({result.total_pnl_pct:+.2f}%)")
        lines.append(f"📦 Positions: {len(result.positions)}")
        
        # Consensus status
        consensus_emoji = "✅" if result.consensus_reached else "⚠️"
        lines.append(f"\n{consensus_emoji} AI Consensus: {result.consensus_count}/4 sources responded")
        if result.consensus_reached:
            lines.append("   ✓ 3/4 consensus reached - recommendations are reliable")
        else:
            lines.append("   ⚠ Less than 3 sources - consider with caution")
        
        # Current Holdings
        lines.append("\n" + "-" * 70)
        lines.append("📋 CURRENT HOLDINGS")
        lines.append("-" * 70)
        
        for pos in result.positions:
            emoji = "🟢" if pos.unrealized_pnl_pct >= 0 else "🔴"
            lines.append(f"\n{pos.symbol}: {pos.quantity:.2f} shares")
            lines.append(f"   Entry: ${pos.avg_cost:.2f} → Current: ${pos.current_price:.2f}")
            lines.append(f"   Value: ${pos.market_value:.2f} | {emoji} P/L: {pos.unrealized_pnl_pct:+.2f}%")
        
        # Perplexity Analysis (with web search)
        if result.perplexity_portfolio_analysis:
            lines.append("\n" + "=" * 70)
            lines.append("🌐 PERPLEXITY ANALYSIS (Web Search + Citations)")
            lines.append("=" * 70)
            lines.append(result.perplexity_portfolio_analysis)
        
        # Gemini Analysis
        if result.gemini_portfolio_analysis:
            lines.append("\n" + "=" * 70)
            lines.append("🔵 GEMINI ANALYSIS")
            lines.append("=" * 70)
            lines.append(result.gemini_portfolio_analysis)
        
        # Claude Analysis
        if result.claude_portfolio_analysis:
            lines.append("\n" + "=" * 70)
            lines.append("🟣 CLAUDE ANALYSIS")
            lines.append("=" * 70)
            lines.append(result.claude_portfolio_analysis)
        
        # OpenAI Analysis
        if result.openai_portfolio_analysis:
            lines.append("\n" + "=" * 70)
            lines.append("🟢 OPENAI ANALYSIS")
            lines.append("=" * 70)
            lines.append(result.openai_portfolio_analysis)
        
        # Market News from Perplexity (at the end)
        if result.market_news:
            lines.append("\n" + "=" * 70)
            lines.append("📰 LATEST MARKET NEWS (from Bloomberg, Reuters, etc.)")
            lines.append("=" * 70)
            lines.append(result.market_news)
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
    
    def _extract_stock_recommendation(self, analysis_text: str, symbol: str) -> str:
        """Extract recommendation for a specific stock from AI analysis text."""
        import re
        
        if not analysis_text:
            return "N/A"
        
        text_upper = analysis_text.upper()
        symbol_upper = symbol.upper()
        
        # Common recommendation patterns to look for near the symbol
        patterns = [
            # Pattern: "AAPL: HOLD" or "AAPL - HOLD" or "**AAPL** - HOLD"
            rf'\*?\*?{symbol_upper}\*?\*?\s*[:\-–]\s*(BUY\s*MORE|STRONG\s*BUY|BUY|HOLD|SELL|TRIM|AVOID)',
            # Pattern: "AAPL (Apple) - HOLD"
            rf'{symbol_upper}\s*\([^)]+\)\s*[:\-–]\s*(BUY\s*MORE|STRONG\s*BUY|BUY|HOLD|SELL|TRIM|AVOID)',
            # Pattern: "Recommendation: HOLD" near symbol mention
            rf'{symbol_upper}[^.]*?RECOMMENDATION[:\s]+(BUY\s*MORE|STRONG\s*BUY|BUY|HOLD|SELL|TRIM|AVOID)',
            # Pattern: "For AAPL... HOLD"
            rf'FOR\s+{symbol_upper}[^.]*?(BUY\s*MORE|STRONG\s*BUY|BUY|HOLD|SELL|TRIM|AVOID)',
            # Pattern: "AAPL ... ** HOLD **"
            rf'{symbol_upper}[^.]*?\*\*(BUY\s*MORE|STRONG\s*BUY|BUY|HOLD|SELL|TRIM|AVOID)\*\*',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_upper)
            if match:
                rec = match.group(1).strip()
                # Normalize recommendations
                if 'BUY MORE' in rec or 'STRONG BUY' in rec:
                    return 'BUY MORE'
                elif 'BUY' in rec:
                    return 'BUY'
                elif 'TRIM' in rec:
                    return 'TRIM'
                elif 'SELL' in rec:
                    return 'SELL'
                elif 'AVOID' in rec:
                    return 'AVOID'
                elif 'HOLD' in rec:
                    return 'HOLD'
        
        # Fallback: Look for the symbol and scan nearby text
        symbol_pos = text_upper.find(symbol_upper)
        if symbol_pos != -1:
            # Get text around the symbol (500 chars after)
            context = text_upper[symbol_pos:symbol_pos + 500]
            
            # Look for recommendation keywords in order of priority
            if 'BUY MORE' in context or 'STRONG BUY' in context:
                return 'BUY MORE'
            elif 'TRIM' in context:
                return 'TRIM'
            elif 'SELL' in context:
                return 'SELL'
            elif 'AVOID' in context:
                return 'AVOID'
            elif 'BUY' in context and 'HOLD' not in context[:context.find('BUY') if 'BUY' in context else 0]:
                return 'BUY'
            elif 'HOLD' in context:
                return 'HOLD'
        
        return "N/A"
    
    def _get_majority_recommendation(self, recommendations: List[str]) -> str:
        """Calculate majority recommendation from list of recommendations."""
        from collections import Counter
        
        # Filter out N/A
        valid_recs = [r for r in recommendations if r != "N/A"]
        if not valid_recs:
            return "N/A"
        
        # Normalize similar recommendations
        normalized = []
        for r in valid_recs:
            if r in ['BUY MORE', 'STRONG BUY', 'BUY']:
                normalized.append('BUY')
            elif r in ['TRIM', 'SELL', 'AVOID']:
                normalized.append('SELL')
            else:
                normalized.append('HOLD')
        
        counts = Counter(normalized)
        majority = counts.most_common(1)[0]
        
        # Return with count info
        return f"{majority[0]} ({majority[1]}/{len(valid_recs)})"
    
    def _extract_stock_analysis(self, analysis_text: str, symbol: str) -> str:
        """Extract the complete analysis section for a specific stock from AI text."""
        import re
        
        if not analysis_text:
            return ""
        
        symbol_upper = symbol.upper()
        
        # List of common stock symbols that might appear in the text
        # We'll use these to find section boundaries
        stock_pattern = r'(?:^|\n)(?:#{1,4}\s*)?\**([A-Z]{2,5})\**(?:\s*[\(\:\-–]|\s+\()'
        
        # SPECIAL CASE: Tables (often used by Gemini)
        # If we find a row containing the symbol, extract the header and that row
        lines = analysis_text.split('\n')
        for i, line in enumerate(lines):
            if f"| {symbol_upper} |" in line or f"|{symbol_upper}|" in line or re.search(fr'\|\s*{symbol_upper}\s*\|', line):
                # Found the row! Now find the table start (header)
                header_idx = -1
                for j in range(i - 1, -1, -1):
                    if '|' not in lines[j]:
                        break
                    # Look for the separator row (e.g. |---|---|)
                    if '---' in lines[j] and j > 0 and '|' in lines[j-1]:
                        header_idx = j - 1
                        break
                
                if header_idx != -1:
                    table_extract = [lines[header_idx], lines[header_idx + 1], line]
                    return '\n'.join(table_extract)
        
        # Find all stock mentions and their positions
        stock_mentions = list(re.finditer(stock_pattern, analysis_text, re.MULTILINE))
        
        # Find where our target symbol is mentioned
        target_start = None
        target_end = None
        
        for i, match in enumerate(stock_mentions):
            if match.group(1).upper() == symbol_upper:
                target_start = match.start()
                # End at the next stock mention, or end of text
                if i + 1 < len(stock_mentions):
                    target_end = stock_mentions[i + 1].start()
                else:
                    target_end = len(analysis_text)
                break
        
        if target_start is not None:
            extracted = analysis_text[target_start:target_end].strip()
            # Clean up - remove leading newlines
            extracted = extracted.lstrip('\n')
            if len(extracted) > 30:
                return extracted
        
        # Fallback: Look for the symbol in bold or with specific patterns
        patterns = [
            # **AAPL** or **AAPL (Apple)**: followed by content until next **SYMBOL**
            rf'\*\*{symbol_upper}[^*]*\*\*[:\s\-–]*([^*]+?)(?=\*\*[A-Z]{{2,5}}|\Z)',
            # AAPL: or AAPL - followed by content until next SYMBOL:
            rf'(?:^|\n){symbol_upper}[:\s\-–]+(.+?)(?=\n[A-Z]{{2,5}}[:\s\-–]|\Z)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE | re.DOTALL)
            if match:
                # Include the symbol header
                full_match = analysis_text[match.start():match.end()].strip()
                if len(full_match) > 30:
                    return full_match
        
        # Last resort: Find symbol and get the paragraph containing it
        text_upper = analysis_text.upper()
        pos = text_upper.find(symbol_upper)
        if pos != -1:
            # Find paragraph boundaries
            start = analysis_text.rfind('\n\n', 0, pos)
            start = start + 2 if start != -1 else 0
            
            end = analysis_text.find('\n\n', pos)
            end = end if end != -1 else len(analysis_text)
            
            # Limit to reasonable length (increased from 500 to 5000)
            extracted = analysis_text[start:min(end, start + 5000)].strip()
            if len(extracted) > 30:
                return extracted
        
        return ""
    
    def _get_robinhood_news(self, symbol: str, limit: int = 5) -> List[Dict]:
        """Fetch news articles from Robinhood for a given stock symbol."""
        try:
            import robin_stocks.robinhood as rh
            
            # Get news from Robinhood
            news_list = rh.stocks.get_news(symbol)
            
            if not news_list:
                return []
            
            # Format and limit the news articles
            formatted_news = []
            for article in news_list[:limit]:
                formatted_news.append({
                    'title': article.get('title', 'No title'),
                    'source': article.get('source', 'Unknown'),
                    'url': article.get('url', ''),
                    'published_at': article.get('published_at', ''),
                    'preview': article.get('preview_text', article.get('summary', ''))[:300]
                })
            
            return formatted_news
            
        except ImportError:
            print("   ⚠️ robin-stocks not installed, skipping Robinhood news")
            return []
        except Exception as e:
            print(f"   ⚠️ Error fetching Robinhood news for {symbol}: {e}")
            return []
    
    def generate_html_report(self, result: PortfolioAnalysisResult) -> str:
        """Generate an HTML report and return the file path."""
        
        # Helper function to get CSS class for recommendation
        def get_rec_class(rec: str) -> str:
            """Get CSS class for recommendation."""
            rec_upper = rec.upper()
            if 'BUY' in rec_upper:
                return 'rec-buy'
            elif 'HOLD' in rec_upper:
                return 'rec-hold'
            elif any(x in rec_upper for x in ['SELL', 'TRIM', 'AVOID']):
                return 'rec-sell'
            else:
                return 'rec-na'
        
        def format_markdown_to_html(text: str) -> str:
            """Convert markdown text to HTML with clickable URLs."""
            import re
            if not text:
                return ""
            
            # Escape HTML characters first
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # Support Markdown tables
            def render_table(match):
                table_text = match.group(0).strip()
                rows = [r.strip() for r in table_text.split('\n')]
                if len(rows) < 2: return table_text
                
                html_table = ['<table class="analysis-table" style="width:100%; border-collapse:collapse; margin:1rem 0; border:1px solid #30363d; font-size:0.9rem;">']
                
                for i, row in enumerate(rows):
                    # Skip separator row (---)
                    if i == 1 and '---' in row: continue
                    
                    # Remove leading/trailing pipes and split
                    clean_row = row.strip()
                    if clean_row.startswith('|'): clean_row = clean_row[1:]
                    if clean_row.endswith('|'): clean_row = clean_row[:-1]
                    
                    cells = [c.strip() for c in clean_row.split('|')]
                    tag = 'th' if (i == 0 and '---' in rows[min(1, len(rows)-1)]) else 'td'
                    
                    bg_color = '#1a1f35' if tag == 'th' else '#161b22'
                    html_row = f'  <tr style="background-color: {bg_color};">'
                    for cell in cells:
                        html_row += f'<{tag} style="border:1px solid #30363d; padding:10px; text-align:left;">{cell}</{tag}>'
                    html_row += '</tr>'
                    html_table.append(html_row)
                
                html_table.append('</table>')
                return '\n'.join(html_table)

            # Table regex: matches blocks of lines containing pipes
            table_pattern = r'((?:\|[^\n]+\|\n?)+)'
            text = re.sub(table_pattern, render_table, text)
            
            # Convert URLs to clickable links
            # Match URLs (http, https)
            url_pattern = r'(https?://[^\s\)\]]+)'
            text = re.sub(url_pattern, r'<a href="\1" target="_blank" class="source-link">\1</a>', text)
            
            # Convert markdown bold **text** to <strong>
            text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
            
            # Convert markdown headers
            text = re.sub(r'^### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
            text = re.sub(r'^## (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
            text = re.sub(r'^# (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
            
            # Convert bullet points
            text = re.sub(r'^[\-\*] (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
            # Wrap consecutive <li> items in <ul>
            text = re.sub(r'((?:<li>.*?</li>\n?)+)', r'<ul>\1</ul>', text)
            
            # Convert numbered lists
            text = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
            
            # Convert paragraphs (double newlines)
            paragraphs = text.split('\n\n')
            formatted = []
            for p in paragraphs:
                p = p.strip()
                if p and not p.startswith('<h') and not p.startswith('<ul') and not p.startswith('<li'):
                    formatted.append(f'<p>{p}</p>')
                else:
                    formatted.append(p)
            text = '\n'.join(formatted)
            
            # Convert single newlines to <br> within paragraphs
            text = re.sub(r'(?<!</p>)\n(?!<)', '<br>\n', text)
            
            return text
        
        # Prepare position cards HTML with AI recommendations
        position_cards = ""
        position_detail_pages = {}  # Store detail page HTML for each symbol
        
        for pos in result.positions:
            pnl_class = "positive" if pos.unrealized_pnl_pct >= 0 else "negative"
            pnl_sign = "+" if pos.unrealized_pnl_pct >= 0 else ""
            
            # Extract recommendations from each AI
            perp_rec = self._extract_stock_recommendation(result.perplexity_portfolio_analysis, pos.symbol)
            gemini_rec = self._extract_stock_recommendation(result.gemini_portfolio_analysis, pos.symbol)
            claude_rec = self._extract_stock_recommendation(result.claude_portfolio_analysis, pos.symbol)
            openai_rec = self._extract_stock_recommendation(result.openai_portfolio_analysis, pos.symbol)
            
            # Extract detailed analysis for each AI
            perp_analysis = self._extract_stock_analysis(result.perplexity_portfolio_analysis, pos.symbol)
            gemini_analysis = self._extract_stock_analysis(result.gemini_portfolio_analysis, pos.symbol)
            claude_analysis = self._extract_stock_analysis(result.claude_portfolio_analysis, pos.symbol)
            openai_analysis = self._extract_stock_analysis(result.openai_portfolio_analysis, pos.symbol)
            news_analysis = self._extract_stock_analysis(result.market_news, pos.symbol) if result.market_news else ""
            
            # Calculate majority
            all_recs = [perp_rec, gemini_rec, claude_rec, openai_rec]
            majority = self._get_majority_recommendation(all_recs)
            
            # Create detail page filename
            detail_filename = f"position_{pos.symbol}_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.html"
            
            # Fetch Robinhood news for this stock
            robinhood_news = self._get_robinhood_news(pos.symbol, limit=5)
            
            # Store position for detail page generation
            position_detail_pages[pos.symbol] = {
                'filename': detail_filename,
                'pos': pos,
                'pnl_class': pnl_class,
                'pnl_sign': pnl_sign,
                'perp_rec': perp_rec,
                'gemini_rec': gemini_rec,
                'claude_rec': claude_rec,
                'openai_rec': openai_rec,
                'perp_analysis': perp_analysis,
                'gemini_analysis': gemini_analysis,
                'claude_analysis': claude_analysis,
                'openai_analysis': openai_analysis,
                'news_analysis': news_analysis,
                'robinhood_news': robinhood_news,
                'majority': majority,
            }
            
            # Determine majority class for card styling
            majority_class = 'buy' if 'BUY' in majority.upper() else 'sell' if 'SELL' in majority.upper() else 'hold'
            
            # Make position card clickable
            position_cards += f"""
            <a href="{detail_filename}" class="position-card-link">
                <div class="position-card">
                    <div class="position-header">
                        <span class="symbol">{pos.symbol}</span>
                        <span class="pnl {pnl_class}">{pnl_sign}{pos.unrealized_pnl_pct:.2f}%</span>
                    </div>
                    <div class="position-details">
                        <p><strong>{pos.quantity:.2f}</strong> shares @ ${pos.avg_cost:.2f}</p>
                        <p>Current: <strong>${pos.current_price:.2f}</strong> | Value: <strong>${pos.market_value:,.2f}</strong></p>
                    </div>
                    <div class="overall-rec {majority_class}">
                        <span class="rec-label">⚖️ AI Consensus</span>
                        <span class="rec-value">{majority}</span>
                    </div>
                    <div class="ai-recs-grid">
                        <div class="ai-rec-block {get_rec_class(perp_rec)}">
                            <span class="ai-name">🌐 Perplexity</span>
                            <span class="ai-verdict">{perp_rec}</span>
                        </div>
                        <div class="ai-rec-block {get_rec_class(gemini_rec)}">
                            <span class="ai-name">🔵 Gemini</span>
                            <span class="ai-verdict">{gemini_rec}</span>
                        </div>
                        <div class="ai-rec-block {get_rec_class(claude_rec)}">
                            <span class="ai-name">🟣 Claude</span>
                            <span class="ai-verdict">{claude_rec}</span>
                        </div>
                        <div class="ai-rec-block {get_rec_class(openai_rec)}">
                            <span class="ai-name">🟢 OpenAI</span>
                            <span class="ai-verdict">{openai_rec}</span>
                        </div>
                    </div>
                    <div class="click-hint">Click for detailed analysis →</div>
                </div>
            </a>
            """
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Analysis Report - {result.timestamp.strftime('%Y-%m-%d')}</title>
    <style>
        :root {{
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-purple: #a371f7;
            --accent-orange: #f0883e;
            --border: #30363d;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }}
        
        .container {{ max-width: 1200px; margin: 0 auto; }}
        
        header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: linear-gradient(135deg, #1a1f35 0%, #0d1117 100%);
            border-radius: 12px;
            border: 1px solid var(--border);
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .timestamp {{ color: var(--text-secondary); font-size: 0.9rem; }}
        
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .summary-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }}
        
        .summary-card .value {{
            font-size: 1.8rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}
        
        .summary-card .label {{ color: var(--text-secondary); }}
        
        .positive {{ color: var(--accent-green); }}
        .negative {{ color: var(--accent-red); }}
        
        .consensus {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .consensus.reached {{ border-color: var(--accent-green); }}
        .consensus.not-reached {{ border-color: var(--accent-orange); }}
        
        .positions-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}
        
        .position-card-link {{
            text-decoration: none;
            color: inherit;
            display: block;
        }}
        
        .position-card-link:hover .position-card {{
            border-color: var(--accent-blue);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(88, 166, 255, 0.15);
        }}
        
        .position-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.2s ease;
            cursor: pointer;
        }}
        
        .overall-rec {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin: 0.75rem 0;
        }}
        
        .overall-rec.buy {{
            background: rgba(63, 185, 80, 0.15);
            border: 1px solid rgba(63, 185, 80, 0.4);
        }}
        
        .overall-rec.hold {{
            background: rgba(240, 136, 62, 0.15);
            border: 1px solid rgba(240, 136, 62, 0.4);
        }}
        
        .overall-rec.sell {{
            background: rgba(248, 81, 73, 0.15);
            border: 1px solid rgba(248, 81, 73, 0.4);
        }}
        
        .rec-label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        .rec-value {{
            font-size: 1rem;
            font-weight: 700;
        }}
        
        .overall-rec.buy .rec-value {{ color: var(--accent-green); }}
        .overall-rec.hold .rec-value {{ color: var(--accent-orange); }}
        .overall-rec.sell .rec-value {{ color: var(--accent-red); }}
        
        .click-hint {{
            text-align: center;
            margin-top: 0.75rem;
            padding-top: 0.5rem;
            border-top: 1px dashed var(--border);
            font-size: 0.75rem;
            color: var(--text-secondary);
            opacity: 0.6;
            transition: opacity 0.2s;
        }}
        
        .position-card-link:hover .click-hint {{
            opacity: 1;
            color: var(--accent-blue);
        }}
        
        .position-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}
        
        .symbol {{
            font-size: 1.3rem;
            font-weight: bold;
            color: var(--accent-blue);
        }}
        
        .pnl {{
            font-size: 1.1rem;
            font-weight: bold;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
        }}
        
        .pnl.positive {{ background: rgba(63, 185, 80, 0.2); }}
        .pnl.negative {{ background: rgba(248, 81, 73, 0.2); }}
        
        .position-details {{ color: var(--text-secondary); font-size: 0.9rem; }}
        .position-details p {{ margin: 0.25rem 0; }}
        
        /* AI Recommendations Grid in Cards */
        .ai-recs-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
            margin-top: 0.75rem;
            padding-top: 0.75rem;
            border-top: 1px solid var(--border);
        }}
        
        .ai-rec-block {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 0.5rem;
            border-radius: 8px;
            text-align: center;
        }}
        
        .ai-rec-block.rec-buy {{
            background: rgba(63, 185, 80, 0.15);
            border: 1px solid rgba(63, 185, 80, 0.4);
        }}
        
        .ai-rec-block.rec-hold {{
            background: rgba(240, 136, 62, 0.15);
            border: 1px solid rgba(240, 136, 62, 0.4);
        }}
        
        .ai-rec-block.rec-sell {{
            background: rgba(248, 81, 73, 0.15);
            border: 1px solid rgba(248, 81, 73, 0.4);
        }}
        
        .ai-rec-block.rec-na {{
            background: rgba(139, 148, 158, 0.1);
            border: 1px solid rgba(139, 148, 158, 0.3);
        }}
        
        .ai-name {{
            font-size: 0.7rem;
            color: var(--text-secondary);
            margin-bottom: 0.2rem;
        }}
        
        .ai-verdict {{
            font-size: 0.75rem;
            font-weight: 600;
        }}
        
        .ai-rec-block.rec-buy .ai-verdict {{ color: var(--accent-green); }}
        .ai-rec-block.rec-hold .ai-verdict {{ color: var(--accent-orange); }}
        .ai-rec-block.rec-sell .ai-verdict {{ color: var(--accent-red); }}
        .ai-rec-block.rec-na .ai-verdict {{ color: var(--text-secondary); }}
        .analysis-section {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 2rem;
            overflow: hidden;
        }}
        
        .analysis-header {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .analysis-header.perplexity {{ background: linear-gradient(90deg, #1e3a5f 0%, var(--bg-card) 100%); }}
        .analysis-header.gemini {{ background: linear-gradient(90deg, #1a365d 0%, var(--bg-card) 100%); }}
        .analysis-header.claude {{ background: linear-gradient(90deg, #3d1a5d 0%, var(--bg-card) 100%); }}
        .analysis-header.openai {{ background: linear-gradient(90deg, #1a4d3d 0%, var(--bg-card) 100%); }}
        .analysis-header.news {{ background: linear-gradient(90deg, #4d3d1a 0%, var(--bg-card) 100%); }}
        
        .analysis-header h2 {{ font-size: 1.2rem; }}
        
        .analysis-content {{
            padding: 1.5rem;
            font-size: 0.95rem;
            max-height: 600px;
            overflow-y: auto;
            line-height: 1.7;
        }}
        
        .analysis-content p {{
            margin-bottom: 1rem;
        }}
        
        .analysis-content h2 {{
            font-size: 1.3rem;
            margin: 1.5rem 0 0.75rem 0;
            color: var(--accent-blue);
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.5rem;
        }}
        
        .analysis-content h3 {{
            font-size: 1.1rem;
            margin: 1.25rem 0 0.5rem 0;
            color: var(--text-primary);
        }}
        
        .analysis-content h4 {{
            font-size: 1rem;
            margin: 1rem 0 0.5rem 0;
            color: var(--text-secondary);
        }}
        
        .analysis-content ul, .analysis-content ol {{
            margin: 0.75rem 0 0.75rem 1.5rem;
            padding: 0;
        }}
        
        .analysis-content li {{
            margin: 0.4rem 0;
        }}
        
        .analysis-content strong {{
            color: var(--text-primary);
        }}
        
        .source-link {{
            color: var(--accent-blue);
            text-decoration: none;
            word-break: break-all;
            transition: color 0.2s;
        }}
        
        .source-link:hover {{
            color: var(--accent-purple);
            text-decoration: underline;
        }}
        
        .icon {{ font-size: 1.5rem; }}
        
        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            border-top: 1px solid var(--border);
        }}
        
        .source-tag {{
            display: inline-block;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 0.2rem 0.5rem;
            font-size: 0.8rem;
            margin: 0.2rem;
            color: var(--accent-blue);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Portfolio Analysis Report</h1>
            <p class="timestamp">Generated on {result.timestamp.strftime('%B %d, %Y at %I:%M %p')}</p>
        </header>
        
        <div class="summary-cards">
            <div class="summary-card">
                <div class="value">${result.total_value:,.2f}</div>
                <div class="label">Total Value</div>
            </div>
            <div class="summary-card">
                <div class="value {'positive' if result.total_pnl >= 0 else 'negative'}">${result.total_pnl:+,.2f}</div>
                <div class="label">Unrealized P/L</div>
            </div>
            <div class="summary-card">
                <div class="value {'positive' if result.total_pnl_pct >= 0 else 'negative'}">{'+' if result.total_pnl_pct >= 0 else ''}{result.total_pnl_pct:.2f}%</div>
                <div class="label">Return</div>
            </div>
            <div class="summary-card">
                <div class="value">{len(result.positions)}</div>
                <div class="label">Positions</div>
            </div>
        </div>
        
        <div class="consensus {'reached' if result.consensus_reached else 'not-reached'}">
            <span class="icon">{'✅' if result.consensus_reached else '⚠️'}</span>
            <div>
                <strong>AI Consensus: {result.consensus_count}/4 sources</strong>
                <p style="color: var(--text-secondary); margin: 0;">
                    {'3/4 consensus reached - recommendations are reliable' if result.consensus_reached else 'Less than 3 sources responded - consider with caution'}
                </p>
            </div>
        </div>
        
        <h2 style="margin-bottom: 1rem;">📋 Current Holdings</h2>
        <div class="positions-grid">
            {position_cards}
        </div>
        
        {'<div class="analysis-section"><div class="analysis-header perplexity"><span class="icon">🌐</span><h2>Perplexity Analysis (Web Search + Citations)</h2></div><div class="analysis-content">' + format_markdown_to_html(result.perplexity_portfolio_analysis) + '</div></div>' if result.perplexity_portfolio_analysis else ''}
        
        {'<div class="analysis-section"><div class="analysis-header gemini"><span class="icon">🔵</span><h2>Gemini Analysis</h2></div><div class="analysis-content">' + format_markdown_to_html(result.gemini_portfolio_analysis) + '</div></div>' if result.gemini_portfolio_analysis else ''}
        
        {'<div class="analysis-section"><div class="analysis-header claude"><span class="icon">🟣</span><h2>Claude Analysis</h2></div><div class="analysis-content">' + format_markdown_to_html(result.claude_portfolio_analysis) + '</div></div>' if result.claude_portfolio_analysis else ''}
        
        {'<div class="analysis-section"><div class="analysis-header openai"><span class="icon">🟢</span><h2>OpenAI Analysis</h2></div><div class="analysis-content">' + format_markdown_to_html(result.openai_portfolio_analysis) + '</div></div>' if result.openai_portfolio_analysis else ''}
        
        {'<div class="analysis-section"><div class="analysis-header news"><span class="icon">📰</span><h2>Latest Market News</h2></div><div class="analysis-content">' + format_markdown_to_html(result.market_news) + '</div></div>' if result.market_news else ''}
        
        <footer>
            <p>Generated by AI Trading Bot | Analysis from Gemini, Claude, OpenAI, and Perplexity</p>
            <p>⚠️ This is not financial advice. Always do your own research before trading.</p>
        </footer>
    </div>
</body>
</html>
"""
        
        # Save to file
        report_dir = Path(__file__).parent.parent / "reports"
        report_dir.mkdir(exist_ok=True)
        
        filename = f"portfolio_analysis_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.html"
        filepath = report_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Generate individual position detail pages
        main_report_filename = filename
        for symbol, data in position_detail_pages.items():
            pos = data['pos']
            detail_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{symbol} - AI Analysis</title>
    <style>
        :root {{
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-purple: #a371f7;
            --accent-orange: #f0883e;
            --border: #30363d;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--accent-blue);
            text-decoration: none;
            margin-bottom: 1.5rem;
            font-size: 0.9rem;
        }}
        .back-link:hover {{ text-decoration: underline; }}
        header {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        header h1 {{
            font-size: 2rem;
            color: var(--accent-blue);
            margin-bottom: 0.5rem;
        }}
        .summary-row {{
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }}
        .summary-item {{
            display: flex;
            flex-direction: column;
        }}
        .summary-label {{ font-size: 0.8rem; color: var(--text-secondary); }}
        .summary-value {{ font-size: 1.2rem; font-weight: bold; }}
        .positive {{ color: var(--accent-green); }}
        .negative {{ color: var(--accent-red); }}
        .majority-badge {{
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.1rem;
            margin-top: 1rem;
        }}
        .majority-badge.buy {{ background: rgba(63, 185, 80, 0.2); color: var(--accent-green); border: 1px solid var(--accent-green); }}
        .majority-badge.hold {{ background: rgba(240, 136, 62, 0.2); color: var(--accent-orange); border: 1px solid var(--accent-orange); }}
        .majority-badge.sell {{ background: rgba(248, 81, 73, 0.2); color: var(--accent-red); border: 1px solid var(--accent-red); }}
        .ai-section {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }}
        .ai-header {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .ai-header.perplexity {{ background: linear-gradient(90deg, #1e3a5f 0%, var(--bg-card) 100%); }}
        .ai-header.gemini {{ background: linear-gradient(90deg, #1a365d 0%, var(--bg-card) 100%); }}
        .ai-header.claude {{ background: linear-gradient(90deg, #3d1a5d 0%, var(--bg-card) 100%); }}
        .ai-header.openai {{ background: linear-gradient(90deg, #1a4d3d 0%, var(--bg-card) 100%); }}
        .ai-header.news {{ background: linear-gradient(90deg, #4d3d1a 0%, var(--bg-card) 100%); }}
        .ai-header h2 {{ font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem; }}
        .ai-rec {{
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .ai-rec.buy {{ background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }}
        .ai-rec.hold {{ background: rgba(240, 136, 62, 0.2); color: var(--accent-orange); }}
        .ai-rec.sell {{ background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }}
        .ai-rec.na {{ background: rgba(139, 148, 158, 0.2); color: var(--text-secondary); }}
        .ai-content {{
            padding: 1.5rem;
            line-height: 1.7;
        }}
        .ai-content p {{ margin-bottom: 1rem; }}
        .ai-content h3 {{ margin: 1rem 0 0.5rem 0; color: var(--accent-blue); }}
        .ai-content ul {{ margin: 0.5rem 0 0.5rem 1.5rem; }}
        .ai-content li {{ margin: 0.3rem 0; }}
        .source-link {{
            color: var(--accent-blue);
            text-decoration: none;
            word-break: break-all;
        }}
        .source-link:hover {{ text-decoration: underline; color: var(--accent-purple); }}
        .no-analysis {{
            padding: 1.5rem;
            color: var(--text-secondary);
            font-style: italic;
        }}
        .news-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        .news-item {{
            padding: 1rem;
            background: var(--bg-dark);
            border-radius: 8px;
            border-left: 3px solid var(--accent-blue);
        }}
        .news-source {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-bottom: 0.3rem;
        }}
        .news-title {{
            display: block;
            font-size: 1rem;
            font-weight: 600;
            color: var(--accent-blue);
            text-decoration: none;
            margin-bottom: 0.5rem;
            line-height: 1.4;
        }}
        .news-title:hover {{
            color: var(--accent-purple);
            text-decoration: underline;
        }}
        .news-preview {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin: 0;
            line-height: 1.5;
        }}
        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            border-top: 1px solid var(--border);
            margin-top: 2rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="{main_report_filename}" class="back-link">← Back to Portfolio</a>
        
        <header>
            <h1>{symbol}</h1>
            <div class="summary-row">
                <div class="summary-item">
                    <span class="summary-label">Shares</span>
                    <span class="summary-value">{pos.quantity:.2f}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Avg Cost</span>
                    <span class="summary-value">${pos.avg_cost:.2f}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Current Price</span>
                    <span class="summary-value">${pos.current_price:.2f}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Market Value</span>
                    <span class="summary-value">${pos.market_value:,.2f}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">P/L</span>
                    <span class="summary-value {data['pnl_class']}">{data['pnl_sign']}${abs(pos.unrealized_pnl):,.2f} ({data['pnl_sign']}{pos.unrealized_pnl_pct:.2f}%)</span>
                </div>
            </div>
            <div class="majority-badge {'buy' if 'BUY' in data['majority'].upper() else 'sell' if 'SELL' in data['majority'].upper() else 'hold'}">
                ⚖️ AI Consensus: {data['majority']}
            </div>
        </header>
        
        <div class="ai-section">
            <div class="ai-header perplexity">
                <h2>🌐 Perplexity Analysis</h2>
                <span class="ai-rec {'buy' if 'BUY' in data['perp_rec'].upper() else 'sell' if any(x in data['perp_rec'].upper() for x in ['SELL', 'TRIM']) else 'hold' if 'HOLD' in data['perp_rec'].upper() else 'na'}">{data['perp_rec']}</span>
            </div>
            <div class="ai-content">
                {format_markdown_to_html(data['perp_analysis']) if data['perp_analysis'] else '<div class="no-analysis">No specific analysis found for this position.</div>'}
            </div>
        </div>
        
        <div class="ai-section">
            <div class="ai-header gemini">
                <h2>🔵 Gemini Analysis</h2>
                <span class="ai-rec {'buy' if 'BUY' in data['gemini_rec'].upper() else 'sell' if any(x in data['gemini_rec'].upper() for x in ['SELL', 'TRIM']) else 'hold' if 'HOLD' in data['gemini_rec'].upper() else 'na'}">{data['gemini_rec']}</span>
            </div>
            <div class="ai-content">
                {format_markdown_to_html(data['gemini_analysis']) if data['gemini_analysis'] else '<div class="no-analysis">No specific analysis found for this position.</div>'}
            </div>
        </div>
        
        <div class="ai-section">
            <div class="ai-header claude">
                <h2>🟣 Claude Analysis</h2>
                <span class="ai-rec {'buy' if 'BUY' in data['claude_rec'].upper() else 'sell' if any(x in data['claude_rec'].upper() for x in ['SELL', 'TRIM']) else 'hold' if 'HOLD' in data['claude_rec'].upper() else 'na'}">{data['claude_rec']}</span>
            </div>
            <div class="ai-content">
                {format_markdown_to_html(data['claude_analysis']) if data['claude_analysis'] else '<div class="no-analysis">No specific analysis found for this position.</div>'}
            </div>
        </div>
        
        <div class="ai-section">
            <div class="ai-header openai">
                <h2>🟢 OpenAI Analysis</h2>
                <span class="ai-rec {'buy' if 'BUY' in data['openai_rec'].upper() else 'sell' if any(x in data['openai_rec'].upper() for x in ['SELL', 'TRIM']) else 'hold' if 'HOLD' in data['openai_rec'].upper() else 'na'}">{data['openai_rec']}</span>
            </div>
            <div class="ai-content">
                {format_markdown_to_html(data['openai_analysis']) if data['openai_analysis'] else '<div class="no-analysis">No specific analysis found for this position.</div>'}
            </div>
        </div>
        
        <div class="ai-section">
            <div class="ai-header news">
                <h2>📰 Latest News from Robinhood</h2>
            </div>
            <div class="ai-content news-list">
                {''.join([f'''
                <div class="news-item">
                    <div class="news-source">{article['source']} • {article['published_at'][:10] if article['published_at'] else 'Recent'}</div>
                    <a href="{article['url']}" target="_blank" class="news-title">{article['title']}</a>
                    <p class="news-preview">{article['preview']}</p>
                </div>
                ''' for article in data['robinhood_news']]) if data['robinhood_news'] else '<div class="no-analysis">No recent news found for this position.</div>'}
            </div>
        </div>
        
        <footer>
            <p>Generated by AI Trading Bot</p>
            <p>⚠️ This is not financial advice. Always do your own research.</p>
        </footer>
    </div>
</body>
</html>"""
            
            # Save detail page
            detail_filepath = report_dir / data['filename']
            with open(detail_filepath, 'w', encoding='utf-8') as f:
                f.write(detail_html)
        
        print(f"   Generated {len(position_detail_pages)} position detail pages")
        
        # Cleanup old reports - keep only last 5 versions
        self._cleanup_old_reports(report_dir, keep_versions=5)
        
        return str(filepath)
    
    def _cleanup_old_reports(self, report_dir: Path, keep_versions: int = 5):
        """Delete old reports, keeping only the most recent versions."""
        try:
            # Find all main portfolio analysis reports
            main_reports = sorted(
                report_dir.glob("portfolio_analysis_*.html"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            
            # Keep track of timestamps from reports we're keeping
            keep_timestamps = set()
            reports_to_keep = main_reports[:keep_versions]
            
            for report in reports_to_keep:
                # Extract timestamp from filename (e.g., portfolio_analysis_20251216_131409.html)
                name = report.stem  # portfolio_analysis_20251216_131409
                parts = name.split('_')
                if len(parts) >= 3:
                    timestamp = f"{parts[-2]}_{parts[-1]}"  # 20251216_131409
                    keep_timestamps.add(timestamp)
            
            # Delete old main reports
            deleted_count = 0
            for report in main_reports[keep_versions:]:
                try:
                    report.unlink()
                    deleted_count += 1
                except Exception:
                    pass
            
            # Delete position detail pages that don't match kept timestamps
            for detail_file in report_dir.glob("position_*_*.html"):
                # Extract timestamp from filename (e.g., position_MSFT_20251216_131409.html)
                name = detail_file.stem
                parts = name.split('_')
                if len(parts) >= 3:
                    timestamp = f"{parts[-2]}_{parts[-1]}"
                    if timestamp not in keep_timestamps:
                        try:
                            detail_file.unlink()
                            deleted_count += 1
                        except Exception:
                            pass
            
            if deleted_count > 0:
                print(f"   🧹 Cleaned up {deleted_count} old report files (keeping last {keep_versions} versions)")
                
        except Exception as e:
            print(f"   ⚠️ Could not cleanup old reports: {e}")
    
    def open_report_in_browser(self, result: PortfolioAnalysisResult) -> str:
        """Generate HTML report and open in browser."""
        filepath = self.generate_html_report(result)
        print(f"\n📄 Report saved to: {filepath}")
        print("🌐 Opening in browser...")
        webbrowser.open(f"file://{filepath}")
        return filepath
