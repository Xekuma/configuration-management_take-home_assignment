[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
Write-Host "=== ТЕСТ: Примеры из разных предметных областей ===`n"

Write-Host "-------------------------------------------------------"
Write-Host "=== 1. Пример 1: Конфигурация 2D-игры ==="
Write-Host "Параметры: -i tests/game_config.cfg`n"
python src/main.py -i tests/game_config.cfg

Write-Host "`n-------------------------------------------------------"
Write-Host "=== 2. Пример 2: Конфигурация сети датчиков ==="
Write-Host "Параметры: -i tests/sensor_network.cfg`n"
python src/main.py -i tests/sensor_network.cfg