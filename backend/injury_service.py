import requests
from bs4 import BeautifulSoup

class InjuryService:
    @staticmethod
    def get_injury_report(team_name: str) -> List[Dict[str, str]]:
        """
        Scrapes ESPN.com for real-time injury data.
        """
        print(f"[Injury] Scraping ESPN for {team_name}...")
        
        url = "https://www.espn.com/nba/injuries"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            # We don't raise status to avoid crashing flow on internet blip
            if resp.status_code != 200:
                print(f"[Warning] ESPN Scrape HTTP {resp.status_code}")
                return []
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find all team titles
            titles = soup.find_all("div", class_="Table__Title")
            
            target_injuries = []
            
            # Robust Fuzzy Match
            # e.g. "Los Angeles Lakers" vs input "Lakers"
            # We iterate ALL teams found on page and see if they match our target
            
            for title in titles:
                page_team_name = title.text.strip()
                
                # Check for match (Input "Lakers" in Page "Los Angeles Lakers")
                if team_name.lower() in page_team_name.lower() or page_team_name.lower() in team_name.lower():
                    
                    # Found our team! Get parent table
                    parent = title.find_parent("div", class_="ResponsiveTable")
                    if not parent:
                        continue
                        
                    rows = parent.find_all("tr", class_="Table__TR")
                    
                    for row in rows:
                        cols = row.find_all("td")
                        if not cols or len(cols) < 2:
                            continue
                            
                        # Skip header
                        if "NAME" in cols[0].text:
                            continue
                            
                        # Extract
                        name = cols[0].text.strip()
                        pos = cols[1].text.strip() # Pos logic
                        date = cols[2].text.strip() if len(cols) > 2 else ""
                        status_desc = cols[3].text.strip() if len(cols) > 3 else "" # "Out", "Day-To-Day"
                        
                        # Determine Importance
                        importance = 5.0
                        # 2025 Star list
                        stars = ["LeBron", "Curry", "Doncic", "Giannis", "Jokic", "Embiid", "Tatum", "Durant", "Davis", "Booker", "Edwards", "Shai", "Wembanyama"]
                        if any(s in name for s in stars):
                            importance = 9.5
                        elif status_desc.lower() == "out":
                            importance = 7.0
                            
                        target_injuries.append({
                            "player": name,
                            "position": pos,
                            "est_return_date": date,
                            "status": status_desc, # Usage: "GTD" or "Out"
                            "expected_minutes_change": "-30" if "out" in status_desc.lower() else "-5", 
                            "importance_score": importance
                        })
                    
                    return target_injuries # Found our team, return immediately
            
            print(f"[Injury] No report found for {team_name} (Team Healthy?)")
            return []

        except Exception as e:
            print(f"[Error] Injury Scrape Failed: {e}")
            return []

if __name__ == "__main__":
    # Test
    print("Test Lakers:", InjuryService.get_injury_report("Lakers"))
