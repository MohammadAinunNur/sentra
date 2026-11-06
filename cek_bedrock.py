"""Cek model Bedrock apa saja yang bisa dipakai di region Anda.

Jalankan dari folder sentra:  python cek_bedrock.py
Membaca AWS_REGION, BEDROCK_MODEL_ID, dan kunci AWS dari file .env.
"""
import os
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
region = os.environ.get("AWS_REGION", "ap-southeast-3")
wanted = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
print(f"Region              : {region}")
print(f"Model yang diinginkan: {wanted}\n")

try:
    client = boto3.client("bedrock", region_name=region)
    models = client.list_foundation_models(byProvider="Amazon", byOutputModality="TEXT")["modelSummaries"]
    profiles = client.list_inference_profiles(maxResults=100, typeEquals="SYSTEM_DEFINED")["inferenceProfileSummaries"]
except (BotoCoreError, ClientError) as exc:
    raise SystemExit(f"Gagal menghubungi AWS: {type(exc).__name__}: {exc}")

print("Model teks Amazon di region ini:")
for m in sorted(models, key=lambda m: m["modelId"]):
    print(f"  {m['modelId']:<35} {', '.join(m.get('inferenceTypesSupported', []))}")

print("\nInference profile (lintas region) yang memuat 'nova':")
nova_profiles = sorted(p["inferenceProfileId"] for p in profiles if "nova" in p["inferenceProfileId"])
for pid in nova_profiles or ["(tidak ada)"]:
    print(f"  {pid}")

print("\nKESIMPULAN")
direct = next((m for m in models if m["modelId"] == wanted), None)
via_profile = [p for p in nova_profiles if p.endswith("." + wanted)]
if direct and "ON_DEMAND" in direct.get("inferenceTypesSupported", []):
    print(f"  BISA dipakai langsung. Biarkan BEDROCK_MODEL_ID={wanted}")
elif via_profile:
    print(f"  Tidak bisa langsung, tetapi tersedia lewat inference profile.")
    print(f"  Isi di .env:  BEDROCK_MODEL_ID={via_profile[0]}")
else:
    print(f"  {wanted} TIDAK tersedia di {region}.")
    print("  Pilihan: (a) pakai model lain dari daftar di atas, atau")
    print("           (b) ganti AWS_REGION ke region yang menyediakannya, lalu jalankan skrip ini lagi.")
