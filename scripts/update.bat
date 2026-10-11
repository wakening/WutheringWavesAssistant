@echo off
title WWA Updater
setlocal
chcp 65001 >nul

echo ========================================
echo WWA Updater
echo ========================================
echo.

rem Check that the script is located in the temp directory
for %%I in ("%~dp0.") do set "SCRIPT_DIR=%%~nxI"
if /i not "%SCRIPT_DIR%"=="temp" goto invalid_directory

rem Return to project root
cd /d "%~dp0.."
if errorlevel 1 goto failed

set "ROOT=%CD%"
set "GIT=%ROOT%\git\cmd\git.exe"
set "LAUNCHER=%ROOT%\WWA.exe"

rem Check required files
if not exist "%GIT%" goto git_not_found
if not exist "%ROOT%\.git" goto repository_not_found
if not exist "%LAUNCHER%" goto launcher_not_found

rem Optionally change the origin URL
set "REPO_URL="

if "%~1"=="1" set "REPO_URL=https://github.com/wakening/WutheringWavesAssistant.git"
if "%~1"=="2" set "REPO_URL=https://cnb.cool/github.wakening/WutheringWavesAssistant.git"
if "%~1"=="3" set "REPO_URL=https://atomgit.com/unwaking/WutheringWavesAssistant.git"

if not defined REPO_URL goto fetch_updates

echo [1/3] Setting remote repository...
"%GIT%" remote set-url origin "%REPO_URL%"
if errorlevel 1 goto failed

:fetch_updates
echo.
echo Fetching updates...
"%GIT%" fetch
if errorlevel 1 goto failed

echo.
echo Resetting to upstream...
"%GIT%" reset --hard "@{upstream}"
if errorlevel 1 goto failed

rem Restart application
echo.
echo Update completed. Starting WWA...
start "" "%LAUNCHER%"
if errorlevel 1 goto failed

echo.
echo WWA has been started.
exit /b 0

:invalid_directory
echo [ERROR] update.bat must be located in the project's temp directory.
goto failed

:git_not_found
echo [ERROR] Git executable not found:
echo "%GIT%"
goto failed

:repository_not_found
echo [ERROR] Git repository not found:
echo "%ROOT%\.git"
goto failed

:launcher_not_found
echo [ERROR] WWA.exe not found:
echo "%LAUNCHER%"
goto failed

:failed
echo.
echo [ERROR] Update failed. Please check the messages above.
echo WWA was not restarted.
pause
exit /b 1
