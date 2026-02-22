
import os
import time

class MarketOracle:
    """
    Market Oracle (Sovereign Interface)
    Mocks the commodification of digital assets.
    Satisfies Rule III (Sovereign Interface) and Rule 5 (Sovereignty).
    """
    def __init__(self, sovereign_pass="ALETHEIA-OMEGA"):
        self.sovereign_pass = sovereign_pass
        self.ledger_path = "data/market_ledger.json"
        
    def sell_asset(self, auth_token, asset_path, price_estimate=50):
        """
        Processes a transaction for a digital asset.
        Requires sovereign authentication.
        """
        if auth_token != self.sovereign_pass:
            print("[Market] Sovereignty violation! Transaction rejected.")
            return None

        print(f"[Market] Processing sale for {os.path.basename(asset_path)}...")
        
        # Simulate market transaction
        revenue = price_estimate * 1.2 # Market premium
        
        entry = {
            "asset": os.path.basename(asset_path),
            "revenue": revenue,
            "wisdom_mass_gain": revenue * 0.5,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        self._append_to_ledger(entry)
        
        print(f"[Market] SUCCESS: Sold for \u20ac{revenue:.2f}. Wisdom Mass +{entry['wisdom_mass_gain']:.1f}")
        return entry

    def _append_to_ledger(self, entry):
        import json
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        
        ledger = []
        if os.path.exists(self.ledger_path):
            with open(self.ledger_path, "r") as f:
                try:
                    ledger = json.load(f)
                except:
                    pass
        
        ledger.append(entry)
        with open(self.ledger_path, "w") as f:
            json.dump(ledger, f, indent=2)

if __name__ == "__main__":
    oracle = MarketOracle()
    oracle.sell_asset("ALETHEIA-OMEGA", "test_asset.md")
