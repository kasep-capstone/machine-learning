import os
import pandas as pd
from google import genai
from google.genai import types
import time
import re

# Konfigurasi API key Gemini dari environment variable
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Load CSV berisi resep
df = pd.read_csv("dataset-recipes/resep_setengah_bersih.csv")  # Ganti dengan nama file kamu

# Inisialisasi klien Gemini
model = "gemini-2.0-flash-001"

def extract_calories_from_text(text):
    # Ambil baris yang mengandung kata "kalori"
    for line in reversed(text.splitlines()):
        match = re.search(r"kalori.*?(\d{1,3}(?:[.,]\d{3})*|\d+)\s*kkal", line.lower())
        if match:
            # Bersihkan angka dari titik/koma ribuan
            angka = match.group(1).replace('.', '').replace(',', '')
            return float(angka)
    return None

# Fungsi untuk estimasi kalori dari bahan
def estimate_calories(bahan: str):
    # Buat prompt dinamis
    prompt_text = f"""Estimasikan total kalori dari bahan-bahan berikut untuk satu resep makanan (tanpa perlu penjelasan panjang):
{bahan}

Tulis hasil akhir seperti ini: Total kalori: xxx kkal"""
    
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
    )

    try:
        result = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            result += chunk.text

        print("[RESPON]:", result.strip())  # Tampilkan hasil sementara

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

# Proses semua baris dan tambahkan estimasi kalori
kalori_list = []
for index, row in df.iterrows():
    bahan = row['Bahan']
    print(f"Estimasi kalori untuk resep {index+1}/{len(df)}...")
    kalori = estimate_calories(bahan)
    kalori_list.append(kalori)
    print(kalori_list)
    time.sleep(1)  # jeda 1 detik untuk menghindari rate limit

# Tambahkan kolom kalori ke DataFrame
df["kalori"] = kalori_list

# Simpan ke file baru
df.to_csv("dataset-recipes/resep_dengan_kalori.csv", index=False)
print("✅ Estimasi kalori selesai! File disimpan sebagai 'resep_dengan_kalori.csv'")