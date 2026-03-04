import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class MusicDecisionEngine:
    """
    AI Decision layer using Groq LLaMA 3.3 70B.
    Analyzes data feeds to predict music market outcomes.
    """
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def generate_analysis(self, spotify_data, viral_signals, event_context):
        """
        Generates a market analysis based on the three-tier logic framework.
        """
        prompt = f"""
        # PolyMusic QUANT ANALYSIS REPORT

        ## INPUT DATA:
        - Spotify Charts: {spotify_data}
        - Viral Signals (TikTok/YT): {viral_signals}
        - Contextual Events: {event_context}

        ## ANALYSIS FRAMEWORK:
        P0 (Event Trigger): Evaluate artist social media pre-warming or surprise drops.
        P1 (Viral Drift): Detect non-musical event impact (trends, challenges).
        P2 (Consistency Check): Compare current stream acceleration with Polymarket price accuracy.

        ## TASK:
        Provide a concise quantitative conclusion. Is the market undervalued or overvalued? 
        Output in Markdown format with a 'Confidence Score' (0-100%).
        """

        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional Music Market Quant Analyst."},
                {"role": "user", "content": prompt}
            ],
            model=self.model,
            temperature=0.2
        )
        return response.choices[0].message.content

if __name__ == "__main__":
    # Sample Test
    engine = MusicDecisionEngine()
    # print(engine.generate_analysis("Top 1: Die With A Smile (9M)", "TikTok 200% growth", "Grammy next week"))
