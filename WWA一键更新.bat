@echo off
title WWA Update
chcp 65001 >nul
setlocal DisableDelayedExpansion

:: =========================================
:: 更新仓库地址
:: 不可修改此脚本，会导致更新失败，请拷贝一份再改
:: =========================================
set "REPO_GITHUB=https://github.com/wakening/WutheringWavesAssistant.git"
set "REPO_PROXY1=https://cnb.cool/github.wakening/WutheringWavesAssistant.git"
set "REPO_PROXY2=https://atomgit.com/unwaking/WutheringWavesAssistant.git"

:: =========================================
:: 判断是否为临时更新脚本
:: =========================================
if "%~1"=="--update" goto UPDATE_LOGIC

:: =========================================
:: 启动脚本逻辑（复制自身到临时脚本执行）
:: =========================================
echo WWA update starting...

set "ROOT_DIR=%~dp0"

:: 切换到项目根目录
cd /d "%ROOT_DIR%"
if errorlevel 1 goto START_ROOT_FAILED

:: 使用相对路径
set "TEMP_DIR=temp\update"
set "TEMP_SCRIPT=temp\update\update_temp.bat"

:: 创建临时目录
if exist "%TEMP_DIR%\" goto TEMP_DIR_READY
mkdir "%TEMP_DIR%" 2>nul
if exist "%TEMP_DIR%\" goto TEMP_DIR_READY
goto TEMP_DIR_FAILED

:TEMP_DIR_READY

:: 删除旧临时脚本
if not exist "%TEMP_SCRIPT%" goto COPY_SCRIPT

del /f /q "%TEMP_SCRIPT%" 2>nul
if not exist "%TEMP_SCRIPT%" goto COPY_SCRIPT
goto TEMP_SCRIPT_FAILED

:COPY_SCRIPT

:: 复制自身到临时脚本
copy /y "%~f0" "%TEMP_SCRIPT%" >nul
if errorlevel 1 goto COPY_FAILED
if not exist "%TEMP_SCRIPT%" goto COPY_FAILED

:: 后台启动临时脚本
start "" /b "%ComSpec%" /d /c ""%ROOT_DIR%%TEMP_SCRIPT%" --update"
if errorlevel 1 goto START_FAILED

exit /b 0


:: =========================================
:: 更新逻辑
:: 临时脚本位于项目根目录\temp\update
:: =========================================
:UPDATE_LOGIC

:: 根据已知目录层级获取项目根目录
pushd "%~dp0..\.." 2>nul
if errorlevel 1 goto ROOT_FAILED

set "ROOT_DIR=%CD%"
popd

:: 切换到项目根目录
cd /d "%ROOT_DIR%"
if errorlevel 1 goto ROOT_FAILED

:: =========================================
:: 检查 Git 可执行文件位置
:: 优先使用项目内的便携版 Git
:: 不搜索系统 Git
:: =========================================
set "GIT_EXE=git"

if not exist "git\git.exe" goto CHECK_GIT_CMD
set "GIT_EXE=%ROOT_DIR%\git\git.exe"
goto GIT_FOUND

:CHECK_GIT_CMD
if not exist "git\cmd\git.exe" goto GIT_FOUND
set "GIT_EXE=%ROOT_DIR%\git\cmd\git.exe"

:GIT_FOUND

:: =========================================
:: 提示用户选择仓库
:: =========================================
echo.
echo Please select a repository to update:
echo [1] GitHub       %REPO_GITHUB%
echo [2] CN-腾讯云    %REPO_PROXY1%
echo [3] CN-AtomGit   %REPO_PROXY2%
echo.

:CHOICE
set "choice="
set /p "choice=Enter your choice (1, 2, or 3): "

if "%choice%"=="1" goto SET1
if "%choice%"=="2" goto SET2
if "%choice%"=="3" goto SET3

echo Invalid selection. Please choose 1, 2, or 3.
goto CHOICE

:SET1
set "REPO_URL=%REPO_GITHUB%"
goto AFTER_CHOICE

:SET2
set "REPO_URL=%REPO_PROXY1%"
goto AFTER_CHOICE

:SET3
set "REPO_URL=%REPO_PROXY2%"
goto AFTER_CHOICE

:AFTER_CHOICE
echo.
echo Using repository [%choice%]: %REPO_URL%
echo.

:: =========================================
:: 用户选择后检查 Git 版本
:: =========================================
"%GIT_EXE%" --version
if errorlevel 1 goto GIT_EXEC_FAILED

:: =========================================
:: 设置 safe.directory
:: =========================================
"%GIT_EXE%" config --global --replace-all safe.directory "%ROOT_DIR%"
if errorlevel 1 goto SAFE_DIRECTORY_FAILED

:: =========================================
:: 初始化或更新仓库
:: =========================================
if exist ".git" goto UPDATE_EXISTING

echo.
echo .git folder not found. Initializing repository...

"%GIT_EXE%" init
if errorlevel 1 goto INIT_FAILED

"%GIT_EXE%" remote add origin "%REPO_URL%"
if errorlevel 1 goto REMOTE_ADD_FAILED

"%GIT_EXE%" fetch origin
if errorlevel 1 goto FETCH_FAILED

"%GIT_EXE%" checkout -f -b main origin/main
if errorlevel 1 goto CHECKOUT_REMOTE_FAILED

goto UPDATE_SUCCESS

:UPDATE_EXISTING

:: 更新已有仓库
"%GIT_EXE%" remote set-url origin "%REPO_URL%"
if errorlevel 1 goto REMOTE_FAILED

"%GIT_EXE%" pull
if errorlevel 1 goto PULL_FAILED

:: =========================================
:: 删除更新器（如果存在）
:: =========================================
:UPDATE_SUCCESS
if not exist "WWA_updater.exe" goto UPDATE_COMPLETE

del /f /q "WWA_updater.exe" >nul 2>&1

:UPDATE_COMPLETE
echo.
echo Update complete!
pause
exit


:: =========================================
:: 错误处理
:: =========================================

:START_ROOT_FAILED
echo.
echo [ERROR] Failed to enter project root:
echo "%ROOT_DIR%"
pause
exit /b 1

:TEMP_DIR_FAILED
echo.
echo [ERROR] Failed to create temporary directory.
pause
exit /b 1

:TEMP_SCRIPT_FAILED
echo.
echo [ERROR] Temporary script is in use, cannot delete.
echo "%ROOT_DIR%%TEMP_SCRIPT%"
pause
exit /b 1

:COPY_FAILED
echo.
echo [ERROR] Failed to copy temporary script.
pause
exit /b 1

:START_FAILED
echo.
echo [ERROR] Failed to start temporary update script.
pause
exit /b 1

:ROOT_FAILED
echo.
echo [ERROR] Failed to locate or enter project root.
pause
exit

:GIT_EXEC_FAILED
echo.
echo [ERROR] Git was not found or cannot be executed.
echo Please install Git or provide portable Git in the project git directory.
pause
exit

:SAFE_DIRECTORY_FAILED
echo.
echo [ERROR] Failed to configure Git safe.directory.
pause
exit

:INIT_FAILED
echo.
echo [ERROR] Git init failed.
pause
exit

:CHECKOUT_MAIN_FAILED
echo.
echo [ERROR] Failed to create local main branch.
pause
exit

:REMOTE_ADD_FAILED
echo.
echo [ERROR] Failed to add remote origin.
pause
exit

:FETCH_FAILED
echo.
echo [ERROR] Git fetch failed.
pause
exit

:CHECKOUT_REMOTE_FAILED
echo.
echo [ERROR] Failed to check out origin/main.
pause
exit

:REMOTE_FAILED
echo.
echo [ERROR] Failed to set repository URL.
pause
exit

:PULL_FAILED
echo.
echo [ERROR] Git update failed.
echo Please check the Git error messages above.
pause
exit