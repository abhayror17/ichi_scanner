# Make sure you have the correct libraries installed
# !pip install yfinance pandas pandas_ta numpy==1.26.4

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from collections import defaultdict

# List of forex pairs
forex_pairs = [
    'EURUSD=X', 'EURJPY=X', 'EURCAD=X', 'EURAUD=X', 'EURGBP=X', 'EURCHF=X',
    'GBPUSD=X', 'GBPJPY=X', 'GBPCAD=X', 'GBPAUD=X', 'GBPCHF=X', 'USDJPY=X',
    'USDCAD=X', 'USDCHF=X', 'AUDUSD=X', 'AUDCAD=X', 'AUDJPY=X', 'AUDCHF=X',
    'CADJPY=X', 'CADCHF=X', 'CHFJPY=X','NZDCHF=X', 'GC=F','SI=F','BTC-USD', 'ETH-USD'
]

def analyze_ichimoku_final(pair):
    """
    Performs a multi-confluence Ichimoku analysis, with corrected independent bounce pattern detection.
    """
    try:
        data = yf.Ticker(pair).history(period="250d", interval="1d")
        if data.empty or len(data) < 52: return None

        data.ta.ichimoku(append=True); data.ta.atr(length=14, append=True); data.dropna(inplace=True)
        if len(data) < 27: return None

        last_row = data.iloc[-1]
        momentum_score, analysis_details, max_score = 0, [], 11

        # --- CONFLUENCE ANALYSIS ---
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

        if atr > 0 and abs(senkou_a - senkou_b) / atr > 0.8:
            if senkou_a > senkou_b and momentum_score > 0: momentum_score += 1
            if senkou_a < senkou_b and momentum_score < 0: momentum_score -= 1
            analysis_details.append("Thick Kumo")

        # --- CORRECTED: Independent Bounce Pattern Detection ---
        recent_candles = data.iloc[-5:]
        bounce_event_added = False

        # Check for Bullish Bounces
        if not bounce_event_added:
            touched_kijun = any(c['Low'] <= c['IKS_26'] for _, c in recent_candles.iterrows())
            if touched_kijun and last_row['Close'] > last_row['IKS_26']:
                momentum_score += 2; analysis_details.append("EVENT: KIJUN BOUNCE"); bounce_event_added = True

        if not bounce_event_added:
            touched_kumo = any(c['Low'] <= max(c['ISA_9'], c['ISB_26']) for _, c in recent_candles.iterrows())
            if touched_kumo and last_row['Close'] > cloud_top:
                momentum_score += 2; analysis_details.append("EVENT: KUMO BOUNCE"); bounce_event_added = True

        # Check for Bearish Bounces
        if not bounce_event_added:
            touched_kijun = any(c['High'] >= c['IKS_26'] for _, c in recent_candles.iterrows())
            if touched_kijun and last_row['Close'] < last_row['IKS_26']:
                momentum_score -= 2; analysis_details.append("EVENT: KIJUN BOUNCE"); bounce_event_added = True

        if not bounce_event_added:
            touched_kumo = any(c['High'] >= min(c['ISA_9'], c['ISB_26']) for _, c in recent_candles.iterrows())
            if touched_kumo and last_row['Close'] < cloud_bottom:
                momentum_score -= 2; analysis_details.append("EVENT: KUMO BOUNCE"); bounce_event_added = True

        # --- FINAL VERDICT ---
        verdict = "Neutral"
        if momentum_score >= 8: verdict = "Strong Bullish"
        elif momentum_score >= 3: verdict = "Moderate Bullish"
        elif momentum_score <= -8: verdict = "Strong Bearish"
        elif momentum_score <= -3: verdict = "Moderate Bearish"

        return {"pair": pair.replace("=X", ""), "score": f"{momentum_score}/{max_score}", "verdict": verdict, "details": ", ".join(analysis_details)}
    except Exception:
        return None


# (The print_table function and main execution block remain the same)
def print_table(title, data):
    print(f"\n{'='*30} {title.upper()} {'='*30}")
    if not data:
        print("No pairs match this category.")
        return

    print(f"| {'Pair':<10} | {'Score':<8} | {'Verdict':<18} | {'Key Confluences':<75} |")
    print(f"|{'-'*12}|{'-'*10}|{'-'*20}|{'-'*77}|")

    for item in data:
        print(f"| {item['pair']:<10} | {item['score']:<8} | {item['verdict']:<18} | {item['details']:<75} |")
    print(f"{'='*(62 + len(title))}")


if __name__ == "__main__":
    all_results = []
    print("Scanning all forex pairs with advanced pattern recognition...")
    for pair in forex_pairs:
        result = analyze_ichimoku_final(pair)
        if result:
            all_results.append(result)
    print("Scan complete. Generating report...")

    categories = defaultdict(list)
    for r in all_results: categories[r['verdict']].append(r)

    bullish_data = categories['Strong Bullish'] + categories['Moderate Bullish']
    bullish_data.sort(key=lambda x: int(x['score'].split('/')[0]), reverse=True)
    print_table("Bullish Momentum Pairs", bullish_data)

    bearish_data = categories['Strong Bearish'] + categories['Moderate Bearish']
    bearish_data.sort(key=lambda x: int(x['score'].split('/')[0]))
    print_table("Bearish Momentum Pairs", bearish_data)

    neutral_data = categories['Neutral']
    print_table("Neutral / Ranging Pairs", neutral_data)
