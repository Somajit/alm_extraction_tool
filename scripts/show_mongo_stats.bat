@echo off
REM Show MongoDB Schema and Statistics

echo ========================================
echo MongoDB Schema and Statistics
echo ========================================
echo.

docker exec mongo mongosh releasecraftdb --quiet --eval "print('\\n=== DATABASE STATS ==='); printjson(db.stats());"

docker exec mongo mongosh releasecraftdb --quiet --eval "print('\\n=== COLLECTIONS ==='); db.getCollectionNames().forEach(function(col) { print('\\n--- Collection: ' + col + ' ---'); print('Document Count: ' + db[col].countDocuments()); });"

docker exec mongo mongosh releasecraftdb --quiet --eval "print('\\n=== SAMPLE DOCUMENTS ==='); db.getCollectionNames().forEach(function(col) { print('\\n--- ' + col + ' ---'); printjson(db[col].findOne()); });"

docker exec mongo mongosh releasecraftdb --quiet --eval "print('\\n=== COLLECTION SIZES ==='); db.getCollectionNames().forEach(function(col) { var stats = db[col].stats(); print(col + ': ' + stats.count + ' docs, Size: ' + (stats.size / 1024 / 1024).toFixed(2) + ' MB'); });"

echo.
echo ========================================
echo Press any key to exit...
pause > nul
