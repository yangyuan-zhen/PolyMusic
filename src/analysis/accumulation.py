import numpy as np

class AccumulationSolver:
    """
    Calculates the 'Stream Gap' for weekly charts.
    """
    def __init__(self, current_leader_total, contender_total, days_remaining):
        self.leader_total = current_leader_total
        self.contender_total = contender_total
        self.days_remaining = days_remaining

    def calculate_gap(self):
        """
        Calculates the average daily streams needed to overtake the leader.
        """
        if self.days_remaining <= 0:
            return 0
        
        gap = self.leader_total - self.contender_total
        avg_needed = gap / self.days_remaining
        return max(0, avg_needed)

    def probability_of_overtake(self, contender_avg, contender_std):
        """
        Simple probabilistic model (placeholder).
        """
        # Logic to estimate probability based on current momentum vs gap
        pass

if __name__ == "__main__":
    # Example: Leader has 10M, Contender has 8M, 3 days left
    solver = AccumulationSolver(10000000, 8000000, 3)
    print(f"Daily streams needed to overtake: {solver.calculate_gap():,.0f}")
