@echo off
REM Clear all data from MongoDB persistent volume

echo ========================================
echo WARNING: Clear All MongoDB Data
echo ========================================
echo.
echo This will permanently delete ALL data from MongoDB including:
echo   - User credentials
echo   - Extraction results
echo   - TestLab extraction results
echo   - Domains and projects
echo   - Test folders
echo   - TestSet details
echo   - Defects
echo   - Cached attachments
echo.
echo The persistent volume will be cleared.
echo.

set /p CONFIRM="Are you sure you want to continue? Type 'YES' to confirm: "

if /I not "%CONFIRM%"=="YES" (
    echo Operation cancelled.
    pause
    exit /b
)

echo.
echo Clearing MongoDB data...
echo.

docker exec mongo mongosh releasecraftdb --quiet --eval "db.getCollectionNames().forEach(function(col) { print('Dropping: ' + col); db[col].drop(); });"

docker exec mongo mongosh releasecraftdb --quiet --eval "print('\\nAll collections dropped successfully!'); printjson(db.stats());"

echo.
echo ========================================
echo MongoDB data cleared successfully!
echo ========================================
echo.
pause
