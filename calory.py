import pandas as pd
import os
import time
from google import genai
from google.genai import types

# Load data yang sudah diekspor sebelumnya
df = pd.read_csv("dataset-recipes/resep_dengan_kalori_final.csv")

# Inisialisasi Gemini Client (pastikan ENV key aktif)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
model = "gemini-2.0-flash-001"

# Fungsi estimate seperti sebelumnya, dengan regex yang sudah ditingkatkan
def estimate_calories(bahan: str):
    prompt_text = f"""Estimasikan total kalori dari bahan-bahan berikut untuk satu resep makanan (tanpa perlu penjelasan panjang):
{bahan}

Tulis hasil akhir seperti ini: Total kalori: xxx kkal"""

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)],
        ),
    ]

    config = types.GenerateContentConfig(response_mime_type="text/plain")

    try:
        result = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config,
        ):
            result += chunk.text
        print("[RESPON]:", result.strip())

        # Regex fleksibel
        import re
        def extract_calories_from_text(text):
            for line in reversed(text.splitlines()):
                match = re.search(r"kalori.*?(\d{1,3}(?:[.,]\d{3})*|\d+)\s*kkal", line.lower())
                if match:
                    angka = match.group(1).replace('.', '').replace(',', '')
                    return float(angka)
            return None

        kalori = extract_calories_from_text(result)
        if kalori is not None:
            print("[BERHASIL] REGEX")
            return kalori
        else:
            print("[GAGAL] REGEX")
            return None

    except Exception as e:
        print(f"[ERROR] Saat memproses bahan: {bahan[:30]}... => {e}")
        return None

# Iterasi ulang untuk baris yang kalori-nya kosong
for i, row in df.iterrows():
    if pd.isna(row["kalori"]):
        print(f"🔄 Mengisi ulang kalori untuk resep {i+1}...")
        kalori_baru = estimate_calories(row["Bahan"])
        df.at[i, "kalori"] = kalori_baru
        time.sleep(1)  # Delay untuk hindari rate limit

# Simpan hasil akhir
df.to_csv("dataset-recipes/resep_dengan_kalori_final_1.csv", index=False)
print("✅ Update selesai! File disimpan sebagai 'resep_dengan_kalori_final_1.csv'")
