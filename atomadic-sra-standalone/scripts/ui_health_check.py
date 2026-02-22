
import urllib.request
import sys

def check_ui():
    url = "http://localhost:8420"
    print(f"Checking SRA UI at {url}...")
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            html = response.read().decode('utf-8')
            print(f"Status: {response.status}")
            
            # Verify v markers (using ASCII parts to be safe)
            markers = [
                "Sovereign Command Center",
                "ATOMADIC",
                "SRA_SUBSTRATE v3.2.1.0",
                "AGENT_ORACLE",
                "v3.2.1.0"
            ]
            
            found = []
            for m in markers:
                if m in html:
                    found.append(m)
            
            print(f"Found markers: {found}")
            if len(found) >= 3:
                print("\n[SUCCESS] Sovereign UI vΩ is active and serving.")
                return True
            else:
                print("\n[FAILED] vΩ markers not found in HTML.")
                return False
    except Exception as e:
        print(f"\n[ERROR] Could not connect to UI server: {e}")
        return False

if __name__ == "__main__":
    if check_ui():
        sys.exit(0)
    else:
        sys.exit(1)
