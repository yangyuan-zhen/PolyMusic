import numpy as np

class DecayController:
    """
    Calculates the 'Half-life' of music trends.
    Distinguishes between 'Single-day spikes' and 'Long-term steps'.
    """
    def __init__(self, historical_streams):
        """
        historical_streams: list or array of daily stream counts.
        """
        self.streams = np.array(historical_streams)

    def calculate_decay_rate(self):
        """
        Calculates the percentage drop between peak and current.
        """
        if len(self.streams) < 2:
            return 0
        
        peak = np.max(self.streams)
        current = self.streams[-1]
        
        if peak == 0:
            return 0
            
        decay = (peak - current) / peak
        return decay

    def is_sustainable(self, threshold=0.15):
        """
        If the decay rate is below the threshold after 3 days, it might be a 'shift'.
        """
        decay = self.calculate_decay_rate()
        # threshold 0.15 means less than 15% drop from peak
        return decay < threshold

if __name__ == "__main__":
    # Case A: Viral spike that decays fast
    spike_streams = [1000, 5000, 3000, 1500]
    # Case B: New release that stays high
    hit_streams = [1000, 8000, 7800, 7500]
    
    da = DecayController(spike_streams)
    db = DecayController(hit_streams)
    
    print(f"Spike sustainable? {da.is_sustainable()}")
    print(f"Hit sustainable? {db.is_sustainable()}")
