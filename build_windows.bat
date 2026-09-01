@echo off
chcp 65001 >nul
cd /d %~dp0

where uv >nul 2>nul
if errorlevel 1 (
    echo 未检测到 uv，请先安装：
    echo   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b 1
)

echo === [1/2] 同步依赖 ===
uv sync || goto :err

echo === [2/2] 打包 ===
uv run pyinstaller --noconfirm --clean --onefile --windowed --name ABTestAudio ab_test.py || goto :err

echo.
echo 打包完成: dist\ABTestAudio.exe
pause
exit /b 0

:err
echo.
echo 打包失败，请检查上方错误信息。
pause
exit /b 1
