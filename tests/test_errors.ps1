[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
Write-Host "=== ТЕСТ: Синтаксические и файловые ошибки ===`n"

Write-Host "-------------------------------------------------------"
Write-Host "=== 1. Ошибка: необъявленная константа ==="
Write-Host "Параметры: -i tests/err_undef_const.cfg`n"
python src/main.py -i tests/err_undef_const.cfg

Write-Host "`n-------------------------------------------------------"
Write-Host "=== 2. Ошибка: недопустимое имя константы ==="
Write-Host "Параметры: -i tests/err_bad_name.cfg`n"
python src/main.py -i tests/err_bad_name.cfg

Write-Host "`n-------------------------------------------------------"
Write-Host "=== 3. Ошибка: пропущена точка с запятой ==="
Write-Host "Параметры: -i tests/err_no_semicolon.cfg`n"
python src/main.py -i tests/err_no_semicolon.cfg

Write-Host "`n-------------------------------------------------------"
Write-Host "=== 4. Ошибка: незакрытый многострочный комментарий ==="
Write-Host "Параметры: -i tests/err_unclosed_comment.cfg`n"
python src/main.py -i tests/err_unclosed_comment.cfg

Write-Host "`n-------------------------------------------------------"
Write-Host "=== 5. Ошибка: некорректный синтаксис массива ==="
Write-Host "Параметры: -i tests/err_array_syntax.cfg`n"
python src/main.py -i tests/err_array_syntax.cfg

Write-Host "`n-------------------------------------------------------"
Write-Host "=== 6. Ошибка: входной файл не найден ==="
Write-Host "Параметры: -i tests/missing.cfg`n"
python src/main.py -i tests/missing.cfg