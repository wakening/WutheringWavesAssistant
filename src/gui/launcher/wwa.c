#include <windows.h>
#include <io.h>
#include <stdio.h>
#include <wchar.h>

#pragma comment(lib, "User32.lib")

// 启动更新脚本；失败时统一弹窗
static BOOL LaunchUpdater(const wchar_t *root, int updateArg)
{
    wchar_t tempDir[MAX_PATH];
    wchar_t source[MAX_PATH];
    wchar_t target[MAX_PATH];
    wchar_t cmdline[MAX_PATH * 3];

    if (swprintf_s(
            tempDir, MAX_PATH,
            L"%ls\\temp\\update", root) < 0 ||
        swprintf_s(
            source, MAX_PATH,
            L"%ls\\scripts\\update.bat", root) < 0 ||
        swprintf_s(
            target, MAX_PATH,
            L"%ls\\update.bat", tempDir) < 0)
    {
        goto failed;
    }

    // 创建 temp\update 目录；已存在则继续
    if (!CreateDirectoryW(tempDir, NULL) &&
        GetLastError() != ERROR_ALREADY_EXISTS)
    {
        goto failed;
    }

    // 确保路径确实是目录
    DWORD attrs = GetFileAttributesW(tempDir);

    if (attrs == INVALID_FILE_ATTRIBUTES ||
        !(attrs & FILE_ATTRIBUTE_DIRECTORY))
    {
        goto failed;
    }

    // 覆盖复制更新脚本
    if (!CopyFileW(source, target, FALSE))
        goto failed;

    // 将个位数参数传递给 update.bat
    // /k：脚本执行结束后保留控制台窗口
    if (swprintf_s(
            cmdline, MAX_PATH * 3,
            L"cmd.exe /k \"\"%ls\" %d\"",
            target, updateArg) < 0)
    {
        goto failed;
    }

    STARTUPINFOW si = { 0 };
    PROCESS_INFORMATION pi = { 0 };
    si.cb = sizeof(si);

    if (!CreateProcessW(
            NULL,
            cmdline,
            NULL,
            NULL,
            FALSE,
            CREATE_NEW_CONSOLE,
            NULL,
            root,
            &si,
            &pi))
    {
        goto failed;
    }

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    return TRUE;

failed:
    MessageBoxW(
        NULL,
        L"Failed to start updater.",
        L"Error",
        MB_OK | MB_ICONERROR
    );

    return FALSE;
}

int WINAPI wWinMain(
    HINSTANCE hInstance,
    HINSTANCE hPrevInstance,
    PWSTR lpCmdLine,
    int nCmdShow)
{
    (void)hInstance;
    (void)hPrevInstance;
    (void)lpCmdLine;
    (void)nCmdShow;

    // 获取 WWA.exe 所在目录
    wchar_t exePath[MAX_PATH];
    wchar_t root[MAX_PATH] = { 0 };

    DWORD len = GetModuleFileNameW(
        NULL, exePath, MAX_PATH);

    if (len > 0 && len < MAX_PATH)
    {
        wchar_t *lastSlash = wcsrchr(exePath, L'\\');

        if (lastSlash != NULL)
        {
            *lastSlash = L'\0';

            if (swprintf_s(
                    root, MAX_PATH, L"%ls", exePath) >= 0)
            {
                SetCurrentDirectoryW(root);
            }
        }
    }

    // 优先使用项目自带的 Python
    const wchar_t *local_python = L"py312\\pythonw.exe";

    STARTUPINFOW si = { 0 };
    PROCESS_INFORMATION pi = { 0 };
    si.cb = sizeof(si);

    wchar_t cmdline[1024];

    if (_waccess(local_python, 0) == 0)
    {
        if (swprintf_s(
                cmdline, 1024,
                L"\"%ls\" main.py",
                local_python) < 0)
        {
            MessageBoxW(
                NULL,
                L"Failed to build Python command line.",
                L"Error",
                MB_OK | MB_ICONERROR
            );
            return 1;
        }

        if (!CreateProcessW(
                local_python,
                cmdline,
                NULL,
                NULL,
                FALSE,
                0,
                NULL,
                NULL,
                &si,
                &pi))
        {
            wchar_t msg[256];

            swprintf_s(
                msg, 256,
                L"Failed to start pythonw.exe.\nError code: %lu",
                GetLastError()
            );

            MessageBoxW(
                NULL,
                msg,
                L"Error",
                MB_OK | MB_ICONERROR
            );

            return 1;
        }
    }
    else
    {
        // 保留 Conda 回退逻辑，并传递 Python 退出码
        wchar_t powershellCmd[] =
            L"powershell.exe -NoProfile -Command "
            L"\"conda run -n wwa-cuda python main.py; "
            L"$code = $LASTEXITCODE; "
            L"if ($null -eq $code) { exit 1 }; "
            L"exit $code\"";

        if (!CreateProcessW(
                NULL,
                powershellCmd,
                NULL,
                NULL,
                FALSE,
                CREATE_NO_WINDOW,
                NULL,
                NULL,
                &si,
                &pi))
        {
            wchar_t msg[256];

            swprintf_s(
                msg, 256,
                L"Failed to start conda.\nError code: %lu",
                GetLastError()
            );

            MessageBoxW(
                NULL,
                msg,
                L"Error",
                MB_OK | MB_ICONERROR
            );

            return 1;
        }
    }

    // 等待 Python / Conda 进程退出
    DWORD waitResult = WaitForSingleObject(
        pi.hProcess, INFINITE);

    DWORD exitCode = 0;
    BOOL gotExitCode = FALSE;

    if (waitResult == WAIT_OBJECT_0)
    {
        gotExitCode = GetExitCodeProcess(
            pi.hProcess, &exitCode);
    }

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    // 101～109 均触发更新，个位数作为脚本参数
    if (gotExitCode && exitCode >= 101 && exitCode <= 109)
    {
        int updateArg = (int)(exitCode % 10);

        if (root[0] != L'\0')
        {
            LaunchUpdater(root, updateArg);
        }
        else
        {
            MessageBoxW(
                NULL,
                L"Failed to locate the application directory.",
                L"Error",
                MB_OK | MB_ICONERROR
            );
        }
    }

    // 保留原版的启动器返回行为
    return 0;
}
