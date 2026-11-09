#include <windows.h>
#include <io.h>
#include <stdio.h>
#include <wchar.h>

#pragma comment(lib, "User32.lib")

// 重启限流：10 分钟窗口内最多 20 次重启
#define RESTART_WINDOW_MS  (10 * 60 * 1000)
#define RESTART_MAX_COUNT  20

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

// 启动 Python（优先项目自带）或 Conda，并等待其退出。
// 成功拿到退出码返回 TRUE 并写入 *pExitCode；
// 启动失败返回 FALSE（已弹窗）。
static BOOL RunApp(const wchar_t *local_python, DWORD *pExitCode)
{
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
            return FALSE;
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

            return FALSE;
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

            return FALSE;
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

    if (!gotExitCode)
        return FALSE;

    *pExitCode = exitCode;
    return TRUE;
}

// 重启限流：记录最近 RESTART_MAX_COUNT 次重启的时间戳（环形队列）
typedef struct
{
    ULONGLONG stamps[RESTART_MAX_COUNT];
    int count;      // 已记录数量（最多 RESTART_MAX_COUNT）
    int next;       // 下一个写入位置
} RestartLimiter;

// 尝试登记一次重启；允许返回 TRUE，超过限流返回 FALSE
static BOOL RestartLimiter_TryAcquire(RestartLimiter *lim)
{
    ULONGLONG now = GetTickCount64();

    // 清理窗口外的旧记录：只看环形队列里最老的那条
    if (lim->count == RESTART_MAX_COUNT)
    {
        int oldest = lim->next;  // 写满时 next 指向最老记录
        if (now - lim->stamps[oldest] >= RESTART_WINDOW_MS)
        {
            // 最老记录已出窗口，覆盖它即可
            lim->stamps[oldest] = now;
            lim->next = (lim->next + 1) % RESTART_MAX_COUNT;
            return TRUE;
        }
        // 写满且最老记录仍在窗口内，说明窗口内已达上限
        return FALSE;
    }

    // 未写满，直接追加
    lim->stamps[lim->next] = now;
    lim->next = (lim->next + 1) % RESTART_MAX_COUNT;
    lim->count++;
    return TRUE;
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

    // 重启限流器（清零即 count=0, next=0）
    RestartLimiter limiter = { { 0 }, 0, 0 };

    // 启动 -> 等待 -> 根据退出码决定是否重启/更新
    for (;;)
    {
        DWORD exitCode = 0;

        if (!RunApp(local_python, &exitCode))
        {
            // 启动失败（RunApp 已弹窗），直接退出
            return 1;
        }

        // 200：不更新，直接重新启动（受 10 分钟 20 次限流）
        if (exitCode == 200)
        {
            if (!RestartLimiter_TryAcquire(&limiter))
            {
                MessageBoxW(
                    NULL,
                    L"Too many restarts in a short time.\n"
                    L"Up to 20 restarts per 10 minutes are allowed.",
                    L"Error",
                    MB_OK | MB_ICONERROR
                );
                break;
            }

            continue;
        }

        // 101～109 均触发更新，个位数作为脚本参数
        if (exitCode >= 101 && exitCode <= 109)
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

        // 其他退出码：保留原版的启动器返回行为
        break;
    }

    return 0;
}