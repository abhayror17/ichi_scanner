# =============================================================================
#  SENSEI-LEVEL MULTI-TIMEFRAME STRATEGY SCANNER (V5 - STRATEGIC RANKING)
# =============================================================================
#
#  This final version correctly sorts the strategy report by the quality of the
#  signal first (A+ > Potential Reversal > Warning), and then by the combined
#  power score. This ensures the most actionable setups are always at the top.
#
# =============================================================================
# FIX: Removed the version constraint on numpy to resolve compatibility issues
!pip install pandas_ta numpy==1.26.4
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from collections import defaultdict

# --- List of pairs to analyze ---
forex_pairs = [
    'EURUSD=X', 'EURJPY=X', 'EURCAD=X', 'EURAUD=X', 'EURGBP=X', 'EURCHF=X',
    'GBPUSD=X', 'GBPJPY=X', 'GBPCAD=X', 'GBPAUD=X', 'GBPCHF=X', 'USDJPY=X',
    'USDCAD=X', 'USDCHF=X', 'AUDUSD=X', 'AUDCAD=X', 'AUDJPY=X', 'AUDCHF=X',
    'CADJPY=X', 'CADCHF=X', 'CHFJPY=X', 'NZDCHF=X', 'GC=F','SI=F'
]

# --- Main Analysis Function (Complete) ---
def analyze_ichimoku_chart(pair, timeframe="4h"):
    """
    Analyzes a single pair on a single timeframe and returns the verdict and score.
    """
    try:
        period = "60d" if timeframe in ["1h", "4h"] else "250d"
        data = yf.Ticker(pair).history(period=period, interval=timeframe)
        if data.empty or len(data) < 52: return None
        data.ta.ichimoku(append=True); data.ta.atr(length=14, append=True); data.dropna(inplace=True)
        if len(data) < 27: return None
        last_row = data.iloc[-1]
        momentum_score, analysis_details, max_score = 0, [], 11
        senkou_a = last_row['ISA_9']; senkou_b = last_row['ISB_26']
        cloud_top = max(senkou_a, senkou_b); cloud_bottom = min(senkou_a, senkou_b)
        if last_row['Close'] > cloud_top: momentum_score += 2; analysis_details.append("Price > Kumo")
        elif last_row['Close'] < cloud_bottom: momentum_score -= 2; analysis_details.append("Price < Kumo")
        else: analysis_details.append("Price in Kumo")
        if last_row['ITS_9'] > last_row['IKS_26']: momentum_score += 1; analysis_details.append("TK Cross Bullish")
        else: momentum_score -= 1; analysis_details.append("TK Cross Bearish")
        past_price_for_chikou = data['Close'].iloc[-27]
        if last_row['ICS_26'] > past_price_for_chikou: momentum_score += 2; analysis_details.append("Chikou Confirms Bull")
        else: momentum_score -= 2; analysis_details.append("Chikou Confirms Bear")
        if senkou_a > senkou_b: momentum_score += 1; analysis_details.append("Future Kumo Bullish")
        else: momentum_score -= 1; analysis_details.append("Future Kumo Bearish")
        atr = last_row['ATRr_14']
        if atr > 0:
            if last_row['Close'] > cloud_top and (last_row['Close'] - cloud_top) / atr > 1.5: momentum_score += 1; analysis_details.append("Overextended Bull")
            elif last_row['Close'] < cloud_bottom and (cloud_bottom - last_row['Close']) / atr > 1.5: momentum_score -= 1; analysis_details.append("Overextended Bear")
            if abs(senkou_a - senkou_b) / atr > 0.8:
                if senkou_a > senkou_b and momentum_score > 0: momentum_score += 1
                if senkou_a < senkou_b and momentum_score < 0: momentum_score -= 1
                analysis_details.append("Thick Kumo")
        recent_candles = data.iloc[-5:]
        bounce_event_added = False
        if not bounce_event_added:
            touched_kijun = any(c['Low'] <= c['IKS_26'] for _, c in recent_candles.iterrows())
            if touched_kijun and last_row['Close'] > last_row['IKS_26']: momentum_score += 2; analysis_details.append("EVENT: KIJUN BOUNCE"); bounce_event_added = True
        if not bounce_event_added:
            touched_kumo = any(c['Low'] <= max(c['ISA_9'], c['ISB_26']) for _, c in recent_candles.iterrows())
            if touched_kumo and last_row['Close'] > cloud_top: momentum_score += 2; analysis_details.append("EVENT: KUMO BOUNCE"); bounce_event_added = True
        if not bounce_event_added:
            touched_kijun = any(c['High'] >= c['IKS_26'] for _, c in recent_candles.iterrows())
            if touched_kijun and last_row['Close'] < last_row['IKS_26']: momentum_score -= 2; analysis_details.append("EVENT: KIJUN BOUNCE"); bounce_event_added = True
        if not bounce_event_added:
            touched_kumo = any(c['High'] >= min(c['ISA_9'], c['ISB_26']) for _, c in recent_candles.iterrows())
            if touched_kumo and last_row['Close'] < cloud_bottom: momentum_score -= 2; analysis_details.append("EVENT: KUMO BOUNCE"); bounce_event_added = True
        verdict = "Neutral"
        if momentum_score >= 8: verdict = "Strong Bullish"
        elif momentum_score >= 3: verdict = "Moderate Bullish"
        elif momentum_score <= -8: verdict = "Strong Bearish"
        elif momentum_score <= -3: verdict = "Moderate Bearish"
        return {"verdict": verdict, "score": momentum_score}
    except Exception: return None

# --- Strategy Determination Function (Complete) ---
def determine_strategy(d1_result, h4_result):
    d1_v = d1_result['verdict']
    h4_v = h4_result['verdict']

    if "Bullish" in d1_v:
        if "Bullish" in h4_v: return "A+ Bullish Continuation"
        elif "Bearish" in h4_v: return "Warning: Bullish Pullback"
        else: return "Wait for 4H Bull Signal"
    elif "Bearish" in d1_v:
        if "Bearish" in h4_v: return "A+ Bearish Continuation"
        elif "Bullish" in h4_v: return "Warning: Bearish Pullback"
        else: return "Wait for 4H Bear Signal"
    elif "Neutral" in d1_v:
        if "Strong Bullish" in h4_v: return "Potential Bullish Reversal"
        elif "Strong Bearish" in h4_v: return "Potential Bearish Reversal"
        else: return "Ranging Market - Avoid"

# --- Table Printing Function (Complete) ---
def print_strategy_table(data):
    """Prints the final, formatted strategy report including the Combined Score."""
    print(f"\n{'='*45} MULTI-TIMEFRAME STRATEGY REPORT (STRATEGICALLY RANKED) {'='*45}")
    print(f"| {'Pair':<10} | {'Combined':<10} | {'1D Verdict':<18} | {'1D Score':<10} | {'4H Verdict':<18} | {'4H Score':<10} | {'Strategy Signal':<28} |")
    print(f"|{'-'*12}|{'-'*12}|{'-'*20}|{'-'*12}|{'-'*20}|{'-'*12}|{'-'*30}|")

    for item in data:
        print(f"| {item['pair']:<10} | {str(item['combined_score']):<10} | {item['d1_verdict']:<18} | {str(item['d1_score']):<10} | {item['h4_verdict']:<18} | {str(item['h4_score']):<10} | {item['strategy']:<28} |")
    print(f"{'='*144}")

# --- Main Execution Block ---
if __name__ == "__main__":
    strategy_results = []
    print("Running Multi-Timeframe Analysis (1D & 4H) for all pairs...")

    for pair in forex_pairs:
        result_1d = analyze_ichimoku_chart(pair, timeframe="1d")
        result_4h = analyze_ichimoku_chart(pair, timeframe="4h")

        if result_1d and result_4h:
            strategy = determine_strategy(result_1d, result_4h)
            combined_score = abs(result_1d['score']) + abs(result_4h['score'])

            strategy_results.append({
                "pair": pair.replace("=X", ""),
                "combined_score": combined_score,
                "d1_verdict": result_1d['verdict'],
                "d1_score": result_1d['score'],
                "h4_verdict": result_4h['verdict'],
                "h4_score": result_4h['score'],
                "strategy": strategy
            })

    # --- NEW: STRATEGIC SORTING LOGIC ---
    # 1. Define the order of importance for strategy signals
    strategy_order = {
        "A+ Bullish Continuation": 0,
        "A+ Bearish Continuation": 0,
        "Potential Bullish Reversal": 1,
        "Potential Bearish Reversal": 1,
        "Warning: Bullish Pullback": 2,
        "Warning: Bearish Pullback": 2,
        "Wait for 4H Bull Signal": 3,
        "Wait for 4H Bear Signal": 3,
        "Ranging Market - Avoid": 4
    }

    # 2. Sort the results: first by strategy quality, then by combined power
    strategy_results.sort(key=lambda x: (strategy_order.get(x['strategy'], 99), -x['combined_score']))

    print_strategy_table(strategy_results)
