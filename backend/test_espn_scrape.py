
import requests
from bs4 import BeautifulSoup
import json

def get_injuries():
    url = "https://www.espn.com/nba/injuries"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Fetching {url}...")
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # ESPN Injury structure often:
        # div.Table__Title -> Team Name
        # table.Table -> Rows of players
        
        injuries = {}
        
        # 2025 Layout: Usually sections by team
        # Look for the responsive-table-wrap
        
        # Strategy: Find all team names, then the adjacent table
        # Attempt to find the specific container
        
        # Let's try to grab all Table__Title
        titles = soup.find_all("div", class_="Table__Title")
        
        for title in titles:
            team_name = title.text.strip()
            
            # Find the next table
            # traversing up to parent then finding table?
            # Or usually the title is inside a structure adjacent to the table
            
            # ESPN structure: 
            # <div class="ResponsiveTable">
            #   <div class="Table__Title">Atlanta Hawks</div>
            #   <div class="Table__Scroller">...<table>...</table></div>
            # </div>
            
            parent = title.find_parent("div", class_="ResponsiveTable")
            if not parent:
                continue
                
            rows = parent.find_all("tr", class_="Table__TR")
            
            team_injuries = []
            
            for row in rows:
                cols = row.find_all("td")
                if not cols or len(cols) < 2:
                    continue
                    
                # Skip header row if it contains "NAME"
                if "NAME" in cols[0].text:
                    continue
                    
                name = cols[0].text.strip()
                status = cols[1].text.strip()
                date = cols[2].text.strip() if len(cols) > 2 else ""
                comment = cols[3].text.strip() if len(cols) > 3 else ""
                
                # Calculate simple importance (Star check)
                importance = 5.0
                stars = ["LeBron", "Curry", "Doncic", "Giannis", "Jokic", "Embiid", "Tatum", "Durant", "Davis", "Booker"]
                if any(s in name for s in stars):
                    importance = 9.5
                elif status == "Out":
                    importance = 7.0
                    
                team_injuries.append({
                    "player": name,
                    "status": status,
                    "desc": comment,
                    "importance": importance
                })
                
            if team_injuries:
                 injuries[team_name] = team_injuries

        return injuries

    except Exception as e:
        print(f"Scrape failed: {e}")
        return {}

if __name__ == "__main__":
    data = get_injuries()
    print("\n--- Scrape Results ---")
    print(json.dumps(data, indent=2))
    
    # Test lookup
    print("\n[Lookup Test] Lakers:")
    print(json.dumps(data.get("Los Angeles Lakers", []), indent=2))
