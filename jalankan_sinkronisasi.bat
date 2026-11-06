@echo off
REM Masuk ke direktori project Django Anda
cd /d C:\xampp\htdocs\sentra

REM Mengaktifkan virtual environment
call env\Scripts\activate

REM Menjalankan perintah management command Django
python manage.py ambil_komentar

REM Menahan jendela agar tidak langsung tertutup
pause