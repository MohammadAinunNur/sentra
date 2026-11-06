import boto3
from django.conf import settings

def pct(part, total):
    """Menghitung persentase secara aman."""
    if not total or total == 0:
        return 0
    return round((part / total) * 100)

def analyze_sentiment_aws(text):
    """Mengirim teks komentar ke AWS Comprehend atau mengembalikan default jika belum aktif."""
    if not text or not text.strip():
        return 'NEUTRAL'
        
    try:
        client = boto3.client(
            'comprehend',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            region_name=getattr(settings, 'AWS_REGION_NAME', 'us-east-1')
        )

        response = client.detect_sentiment(
            Text=text,
            LanguageCode='id'  # 'id' untuk Bahasa Indonesia
        )
        return response.get('Sentiment', 'NEUTRAL')
    except Exception as e:
        # Fallback otomatis jika AWS belum aktif/kredensial kosong
        print(f"Catatan AWS (Abaikan jika akun masih verifikasi): {e}")
        
        # Simulasi sederhana berbasis kata kunci untuk pengujian lokal sementara
        lower_text = text.lower()
        if any(w in lower_text for w in ['bagus', 'keren', 'mantap', 'terbaik', 'suka', 'puas']):
            return 'POSITIVE'
        elif any(w in lower_text for w in ['buruk', 'jelek', 'parah', 'kecewa', 'lambat', 'rusak']):
            return 'NEGATIVE'
        return 'NEUTRAL'