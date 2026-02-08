@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   GITHUB GUNCELLEME ARACI
echo ========================================
echo.

echo [1/4] Degisiklikleri ekleniyor...
git add .

echo.
echo [2/4] Commit mesaji olusturuluyor...
set /p message="Commit mesaji girin (bos birakilirsa otomatik): "

if "%message%"=="" (
    set message=Yagmur sistemi sesleri eklendi ve entegre edildi
)

git commit -m "%message%"

echo.
echo [3/4] GitHub'a yukleniyor...
git push origin main

echo.
echo [4/4] Tamamlandi!
echo.
echo ========================================
echo   BASARIYLA YUKLENDI!
echo ========================================
echo.
pause
