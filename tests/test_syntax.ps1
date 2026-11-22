[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
Write-Host "=== ТЕСТ: Конструкции языка и вложенность ===`n"

Write-Host "-------------------------------------------------------"
Write-Host "=== 1. Числа и комментарии (однострочные и многострочные) ==="
Write-Host "Параметры: -i tests/comments_numbers.cfg`n"
python src/main.py -i tests/comments_numbers.cfg

Write-Host "`n-------------------------------------------------------"
Write-Host "=== 2. Массивы и многоуровневая вложенность ==="
Write-Host "Параметры: -i tests/arrays_nested.cfg`n"
python src/main.py -i tests/arrays_nested.cfg

Write-Host "`n-------------------------------------------------------"
Write-Host "=== 3. Объявление и вложенное вычисление констант ==="
Write-Host "Параметры: -i tests/constants_nested.cfg`n"
python src/main.py -i tests/constants_nested.cfg