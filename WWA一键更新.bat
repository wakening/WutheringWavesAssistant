@echo off
title WWA Update
chcp 65001 >nul
setlocal enabledelayedexpansion

:: =========================================
:: 更新仓库地址
:: 不可修改此脚本，会导致更新失败，请拷贝一份再改
:: =========================================
set REPO_GITHUB=https://github.com/wakening/WutheringWavesAssistant.git
set REPO_PROXY1=https://cnb.cool/github.wakening/WutheringWavesAssistant.git
set REPO_PROXY2=https://atomgit.com/unwaking/WutheringWavesAssistant.git
:: set REPO_PROXY3=https://ghproxy.net/https://github.com/wakening/WutheringWavesAssistant.git

:: =========================================
:: 判断是否为临时更新脚本
:: =========================================
if "%1"=="--update" goto :UPDATE_LOGIC

:: =========================================
:: 启动脚本逻辑（复制自身到临时脚本执行）
:: =========================================
echo WWA update starting...

:: 临时目录和脚本
set ROOT_DIR=%~dp0
set SCRIPT_DIR=%~dp0
set TEMP_DIR=%ROOT_DIR%temp\update
set TEMP_SCRIPT=%TEMP_DIR%\update_temp.bat

:: 创建临时目录
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%" 2>nul

:: 删除旧临时脚本，如果失败则退出
if exist "%TEMP_SCRIPT%" (
    del /f /q "%TEMP_SCRIPT%" 2>nul
    if exist "%TEMP_SCRIPT%" (
        echo Temporary script is in use, cannot delete. Exiting.
        pause
        exit /b 1
    )
)

:: 复制自身到临时脚本
copy "%~f0" "%TEMP_SCRIPT%" /Y >nul

:: 启动临时脚本执行更新逻辑
start "" /b "%TEMP_SCRIPT%" --update

:: 原脚本退出
exit

:: =========================================
:UPDATE_LOGIC
:: 真正的更新逻辑
:: =========================================

:: 获取项目根目录（临时脚本在 script 子目录）
pushd "%~dp0..\.." >nul
set "ROOT_DIR=%CD%"
popd >nul

set SCRIPT_DIR=%~dp0
set TEMP_DIR=%ROOT_DIR%\temp\update
set TEMP_SCRIPT=%TEMP_DIR%\update_temp.bat

:: echo %ROOT_DIR%
:: echo %SCRIPT_DIR%
:: echo %TEMP_DIR%
:: echo %TEMP_SCRIPT%

:: 切换到项目根目录
cd /d "%ROOT_DIR%"

:: 如果当前目录下 git\git.exe 存在，则加入 PATH 前面
if exist "%ROOT_DIR%\git\cmd\git.exe" (
    set "PATH=%ROOT_DIR%\git\cmd;%PATH%"
)

:: 设置 safe.directory 防止权限/信任问题
git config --global --replace-all safe.directory "%ROOT_DIR%"

:: 提示用户选择仓库
echo.
echo Please select a repository to update:
echo [1] GitHub      %REPO_GITHUB%
echo [2] CN-腾讯云    %REPO_PROXY1%
echo [3] CN-AtomGit	 %REPO_PROXY2%
:: echo [4] 国内加速3	 %REPO_PROXY3%

:CHOICE
set "REPO_URL="
:: set /p choice="Enter your choice (1, 2, 3, or 4): "
set /p choice="Enter your choice (1, or 2): "

if "%choice%"=="1" goto SET1
if "%choice%"=="2" goto SET2
if "%choice%"=="3" goto SET3
:: if "%choice%"=="4" goto SET4

:: echo Invalid selection. Please choose 1, 2, 3, or 4.
echo Invalid selection. Please choose 1, or 2.
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

:SET4
set "REPO_URL=%REPO_PROXY3%"
goto AFTER_CHOICE

:AFTER_CHOICE
echo Using repository [%choice%]: %REPO_URL%

:: =========================================
:: 检查 Git 是否可用
:: =========================================
git --version >nul 2>&1
if errorlevel 1 (
    echo Git is not found! Please install Git or provide portable Git in %ROOT_DIR%\git
    pause
    exit /b 1
)

git --version

:: 判断 .git 是否存在，如果没有则初始化仓库
if not exist "%ROOT_DIR%\.git" (
    echo .git folder not found. Initializing repository...
    :: git config --global init.defaultBranch main
    git init -b main
    git remote add origin %REPO_URL%
    git fetch
    git checkout -f -b main origin/main
) else (
    git remote set-url origin %REPO_URL%
    git pull
)

:: 拉取最新代码
:: git fetch --all
:: git reset --hard origin/main
:: git fetch
:: git merge
:: git pull

if exist "WWA_updater.exe" (
    del /f /q "WWA_updater.exe" >nul 2>&1
)

echo Update complete!
pause
exit
