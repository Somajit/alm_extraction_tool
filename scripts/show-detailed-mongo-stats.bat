@echo off
REM Show detailed MongoDB statistics for releasecraftdb
REM Usage: show-detailed-mongo-stats.bat [mongo_type] [connection_string]
REM   mongo_type: "local" or "atlas"
REM   connection_string: MongoDB connection string (required for atlas)

setlocal enabledelayedexpansion

set MONGO_TYPE=%1
set MONGO_URI=%2

if "%MONGO_TYPE%"=="local" (
    set MONGO_CMD=docker exec mongo mongosh releasecraftdb --quiet
) else if "%MONGO_TYPE%"=="atlas" (
    if "%MONGO_URI%"=="" (
        echo [ERROR] MongoDB Atlas connection string is required
        exit /b 1
    )
    set MONGO_CMD=mongosh "%MONGO_URI%" --quiet
)

echo.
echo ============================================
echo MongoDB Statistics - releasecraftdb
echo ============================================
echo.

REM Get database stats
%MONGO_CMD% --eval "var stats = db.stats(); print('Database: releasecraftdb'); print('Collections: ' + stats.collections); print('Total Documents: ' + stats.objects); print('Data Size: ' + (stats.dataSize / 1024 / 1024).toFixed(2) + ' MB'); print('Storage Size: ' + (stats.storageSize / 1024 / 1024).toFixed(2) + ' MB');"

echo.
echo Collection Details:
echo -------------------------------------------

REM Check each collection
%MONGO_CMD% --eval "var collections = ['users', 'domains', 'projects', 'testplan_folders', 'testplan_tests', 'testplan_test_design_steps', 'testplan_folder_attachments', 'testplan_test_attachments', 'testplan_test_design_step_attachments', 'testlab_releases', 'testlab_release_cycles', 'testlab_testsets', 'testlab_testruns', 'testlab_testset_attachments', 'defects', 'defect_attachments', 'user_credentials', 'tree_cache', 'attachment_cache', 'testplan_test_details', 'testplan_extraction_results', 'testlab_testset_details', 'testlab_extraction_results', 'defect_details']; collections.forEach(function(col) { var count = db[col].countDocuments(); if (count > 0) { print(col + ': ' + count + ' documents'); } else { print(col + ': 0 documents'); } });"

echo.
