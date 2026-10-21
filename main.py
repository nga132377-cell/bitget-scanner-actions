import time
import requests

# Konfigurasi Token & Chat ID dari GitHub Secrets
import os
TELEGRAM_BOT_TOKEN = os.environ.get("8600031494:AAFyhLb394cADrBRxVRodfO5bb3OcvDCKAA")
TELEGRAM_CHAT_ID = os.environ.get("5341741757")

THRESHOLD = 0.95  # Minimal 95% body candle
TIMEFRAME = '1h'  # Timeframe Bitget ('1h', '4h', '1D')

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Gagal kirim pesan: {e}")

def get_bitget_usdt_pairs():
    url = "https://api.bitget.com/api/v2/mix/market/contracts?productType=USDT-FUTURES"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("code") == "00000":
            return [item["symbol"] for item in res.get("data", [])]
    except Exception as e:
        print(f"Error fetch pairs: {e}")
    return []

def scan_marubozu():
    pairs = get_bitget_usdt_pairs()
    if not pairs:
        print("Tidak ada pair yang ditemukan.")
        return

    full_green = []
    full_red = []

    print(f"Scanning {len(pairs)} pair di Bitget...")

    for symbol in pairs:
        try:
            url = f"https://api.bitget.com/api/v2/mix/market/candles?symbol={symbol}&productType=USDT-FUTURES&granularity={TIMEFRAME}&limit=3"
            res = requests.get(url, timeout=5).json()

            if res.get("code") == "00000" and len(res.get("data", [])) >= 2:
                candle = res["data"][1]  # Candle yang baru saja closed
                open_p  = float(candle[1])
                high_p  = float(candle[2])
                low_p   = float(candle[3])
                close_p = float(candle[4])

                candle_range = high_p - low_p
                if candle_range == 0:
                    continue

                body = abs(close_p - open_p)
                ratio = body / candle_range

                if ratio >= THRESHOLD:
                    clean_symbol = symbol.replace("_UMCBL", "")
                    if close_p > open_p:
                        full_green.append(clean_symbol)
                    else:
                        full_red.append(clean_symbol)
        except Exception:
            continue
        time.sleep(0.02)

    # Kirim notifikasi jika ada koin yang sesuai kriteria
    if full_green or full_red:
        msg = f"🚨 *BITGET MARUBOZU ALERT (TF {TIMEFRAME})* 🚨\n\n"
        if full_green:
            msg += "🟢 *FULL HIJAU:* " + ", ".join(full_green) + "\n\n"
        if full_red:
            msg += "🔴 *FULL MERAH:* " + ", ".join(full_red) + "\n"
        send_telegram_msg(msg)
    else:
        print("Scan selesai: Tidak ada candle Marubozu jam ini.")

if __name__ == "__main__":
    scan_marubozu()
