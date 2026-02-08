@echo off
REM Gecikmeli değişken genişletmeyi etkinleştir
setlocal enabledelayedexpansion

REM Kutu karakterleri için UTF-8 karakter kodlamasını zorla
chcp 65001 >nul

REM ANSI renk kodlarını hazırla (terminal renklendirmesi için)
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (set "ESC=%%b")

REM Renk kodlarını tanımla
set "G=%ESC%[92m"  REM Yeşil
set "C=%ESC%[96m"  REM Cyan (Camgöbeği)
set "Y=%ESC%[93m"  REM Sarı
set "R=%ESC%[91m"  REM Kırmızı
set "M=%ESC%[95m"  REM Magenta (Mor)
set "W=%ESC%[97m"  REM Beyaz
set "B=%ESC%[1m"   REM Kalın
set "X=%ESC%[0m"   REM Sıfırla

REM GitHub depo URL'sini ayarla
set "REPO_URL=https://github.com/Memati8383/PyCraft.git"
REM Pencere başlığını ayarla
title PyCraft Bulut Senkronizasyonu

:START
REM Ekranı temizle
cls
REM Başlık çerçevesini göster
echo %B%%C%┌──────────────────────────────────────────────────────────┐%X%
echo %B%%C%│ %X%%B%PyCraft %X%%C%│ %W%Yüksek Hızlı GitHub Senkronizasyonu%X%%B%%C%        │%X%
echo %B%%C%└──────────────────────────────────────────────────────────┘%X%
echo.

REM 1. Sistem Kontrolü - Git'in yüklü olup olmadığını kontrol et
echo %C%[%B%BİLGİ%X%%C%]%X% Ortam kontrol ediliyor...
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo %R%[HATA] Git bulunamadı! Lütfen Git yükleyip tekrar deneyin.%X%
    pause & exit /b
)

REM 2. Depo Yönetimi - Git deposu yoksa oluştur ve GitHub'a bağla
if not exist .git (
    echo %Y%[BAŞLAT]%X% Yeni Git ortamı oluşturuluyor...
    git init >nul 2>&1
    git remote add origin %REPO_URL% >nul 2>&1
    git branch -M main >nul 2>&1
    echo %G%[TAMAM]%X% Depo GitHub'a bağlandı.
)

REM 3. Değişiklik Taraması - Tüm değişiklikleri sahneye ekle ve durumu göster
echo %C%[%B%DURUM%X%%C%]%X% Değişiklikler taranıyor...
git add .
echo %W%----------------------------------------------------------%X%
git status --short
echo %W%----------------------------------------------------------%X%
echo.

REM 4. Bulut Entegrasyonu (Rebase) - Uzak sunucudaki değişiklikleri al ve birleştir
echo %M%[%B%GÜNCELLE%X%%M%]%X% Uzak sunucudaki değişiklikler alınıyor...
git pull origin main --rebase > github_sync.log 2>&1
if %errorlevel% neq 0 (
    echo %Y%[UYARI]%X% Güncelleme atlandı veya çakışma var. github_sync.log dosyasına bakın.
)

REM 5. Etiket Hazırlığı - Commit mesajını kullanıcıdan al
echo %C%[%B%KAYIT%X%%C%]%X% Değişiklikler paketleniyor...
set /p msg="%B%%C%[MESAJ]> %X%"
REM Mesaj boşsa varsayılan mesaj kullan
if "%msg%"=="" (
    set msg=Düzenli Güncelleme - %date% %time%
)

REM 6. Dağıtım - Değişiklikleri commit et ve GitHub'a gönder
echo.
echo %C%[%B%GÖNDER%X%%C%]%X% GitHub'a aktarılıyor...
git commit -m "!msg!" >> github_sync.log 2>&1
if %errorlevel% neq 0 (
    echo %G%[STABİL]%X% Gönderilecek yeni bir değişiklik yok.
    timeout /t 3 >nul & exit /b
)

REM Değişiklikleri uzak sunucuya gönder
git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo %R%[BAŞARISIZ]%X% Gönderim hatası. Bağlantınızı veya yetkilerinizi kontrol edin.
    echo %Y%[DETAY]%X% Ayrıntılar için github_sync.log dosyasına bakın.
) else (
    echo.
    echo %B%%G%==========================================================%X%
    echo %B%%G%     BAŞARILI: Ekosistem %time% itibarıyla güncel!     %X%
    echo %B%%G%==========================================================%X%
)

echo.
echo %C%Çıkmak için [ENTER] tuşuna basın...%X%
pause >nul
