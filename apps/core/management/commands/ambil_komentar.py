import re
import urllib3
import requests
from django.core.management.base import BaseCommand
from apps.core.models import Komentar
try:
    from transformers import pipeline
except ImportError:
    pipeline = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Command(BaseCommand):
    help = 'Menarik komentar Instagram, analisis sentimen menggunakan IndoBERT / Multilingual BERT (Hugging Face), dan simpan ke database'

    def handle(self, *args, **options):
        ACCESS_TOKEN = "EAAZAbCoPFcB4BS60tphNirxd7cTT150673EF6Id3IWktjixJ1o4VsSdk82ZAA7kxOs5ePED4IeXcYn1f6KeQVsN9KGRYBoWd2lKzx8GTLVK2OwbZBPWeXZBzZAEDAQqBbvapXWYLxDrb3RRVaZAToGHU4kdhfrYGyQZCPJu9uDefgPUs7GIlyx9t6geqsJn"
        IG_USER_ID = "17841415868144059"
        
        if pipeline is None:
            self.stdout.write(self.style.ERROR("Library transformers belum terpasang. Jalankan 'pip install transformers torch' untuk menggunakan fitur ini secara lokal."))
            return

        # Cek koneksi database terlebih dahulu sebelum menjalankan proses AI
        from django.db import connection
        try:
            connection.ensure_connection()
            db_target = f"{connection.settings_dict.get('HOST') or 'localhost'}:{connection.settings_dict.get('PORT')}"
            self.stdout.write(self.style.SUCCESS(f"Terhubung ke database: {db_target} (DB: {connection.settings_dict.get('NAME')})"))
        except Exception as conn_err:
            self.stdout.write(self.style.ERROR(
                f"\n[GAGAL KONEKSI DATABASE] Tidak dapat terhubung ke MySQL: {conn_err}\n"
                f"Penyebab & Solusi:\n"
                f"1. Jika menggunakan MySQL lokal (XAMPP): Buka XAMPP Control Panel dan klik START pada MySQL.\n"
                f"2. Jika ingin menyimpan ke Cloud (Aiven): Pastikan DB_HOST, DB_PORT, DB_USER, DB_PASSWORD sudah diatur di file .env.\n"
            ))
            return

        self.stdout.write("Memuat model AI dari Hugging Face (Mohon tunggu sebentar)...")
        
        # Menggunakan model bert-base-multilingual-uncased-sentiment yang stabil dan mendukung bahasa Indonesia
        try:
            sentiment_pipeline = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")
        except Exception as model_err:
            self.stdout.write(self.style.ERROR(f"Gagal memuat model AI: {model_err}"))
            return

        def analyze_sentiment_indobert(text):
            if not text.strip():
                return "NEUTRAL"
            
            text_lower = text.lower()
            
            # --- ATURAN KOREKSI / OVERRIDE MANUAL UNTUK KRITIKAN LOKAL ---
            # Jika komentar mengandung kata keluhan/kritikan mutlak ini, paksa jadi NEGATIF
            keyword_negatif_kuat = [
                'lama sekali', 'lama bgt', 'lambat', 'lemot', 'padam', 'mati', 
                'rusak', 'kecewa', 'parah', 'gagal', 'error', 'terus menerus', 
                'terus-menerus', 'komplen', 'komplain', 'buruk', 'kurang responsif'
            ]
            if any(kw in text_lower for kw in keyword_negatif_kuat):
                return "NEGATIVE"
            # -------------------------------------------------------------
            
            try:
                # Batasi teks maksimal 512 karakter (batas token BERT) agar tidak error
                truncated_text = text[:512]
                result = sentiment_pipeline(truncated_text)[0]
                label = result['label'].upper()
                score = result['score']
                
                # Pemetaan label dari model ke format database SENTRA
                if '4' in label or '5' in label or 'POS' in label:
                    return "POSITIVE"
                elif '1' in label or '2' in label or 'NEG' in label:
                    return "NEGATIVE"
                else:
                    return "NEUTRAL"
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error saat prediksi AI: {e}"))
                return "NEUTRAL"

        self.stdout.write("Sedang menghubungkan ke Instagram Graph API...")
        url_media = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media?fields=id,caption&access_token={ACCESS_TOKEN}"
        
        try:
            response = requests.get(url_media, verify=False)
            res_media = response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Gagal terhubung ke Instagram API: {e}"))
            return

        if 'data' in res_media and len(res_media['data']) > 0:
            jumlah_simpan = 0
            
            for post in res_media['data']:
                post_id = str(post.get('id'))
                caption = str(post.get('caption', 'Tanpa Caption'))
                
                url_comments = f"https://graph.facebook.com/v20.0/{post_id}/comments?fields=id,text,username&access_token={ACCESS_TOKEN}"
                
                while url_comments:
                    res_comments = requests.get(url_comments, verify=False).json()
                    comments = res_comments.get('data', [])
                    
                    for comment in comments:
                        username = str(comment.get('username', 'Unknown'))
                        text = str(comment.get('text', ''))
                        
                        # --- PROSES ANALISIS MENGGUNAKAN AI ---
                        sentiment_label = analyze_sentiment_indobert(text)
                        self.stdout.write(f"Teks: '{text[:30]}...' -> AI: {sentiment_label}")
                        # --------------------------------------

                        try:
                            existing_comments = Komentar.objects.filter(post_id=post_id, username=username, comment_text=text)
                            
                            if existing_comments.exists():
                                obj = existing_comments.first()
                                obj.caption = caption
                                obj.sentiment = sentiment_label
                                obj.save()
                            else:
                                Komentar.objects.create(
                                    post_id=post_id,
                                    username=username,
                                    caption=caption,
                                    comment_text=text,
                                    sentiment=sentiment_label
                                )
                                jumlah_simpan += 1
                                self.stdout.write(f"Berhasil menyimpan komentar dari @{username} [{sentiment_label}]")
                                
                        except Exception as db_err:
                            self.stdout.write(self.style.WARNING(f"Lewati baris karena error DB: {db_err}"))

                    paging = res_comments.get('paging', {})
                    url_comments = paging.get('next')

            self.stdout.write(self.style.SUCCESS(f"Sinkronisasi & analisis AI selesai! Total proses: {jumlah_simpan}"))
        else:
            self.stdout.write(self.style.WARNING("Tidak ada postingan ditemukan dari API."))