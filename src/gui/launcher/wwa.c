#include <windows.h>
#include <io.h>
#include <stdio.h>
#include <string.h>

#pragma comment(lib, "User32.lib")


int WINAPI WinMain(
    HINSTANCE hInstance,
    HINSTANCE hPrevInstance,
    LPSTR lpCmdLine,
    int nCmdShow
)
{
    /*
        设置当前目录为 WWA.exe 所在目录
    */
    char exePath[MAX_PATH];

    if (GetModuleFileNameA(NULL, exePath, MAX_PATH))
    {
        char* lastSlash = strrchr(exePath, '\\');

        if (lastSlash)
        {
            *lastSlash = '\0';
            SetCurrentDirectoryA(exePath);
        }
    }


    /*
        GUI 程序使用 pythonw.exe
        不会创建控制台窗口
    */
    const char* local_python = "py312\\pythonw.exe";


    STARTUPINFOA si = {0};
    PROCESS_INFORMATION pi = {0};

    si.cb = sizeof(si);


    char cmdline[1024];


    if (_access(local_python, 0) == 0)
    {
        /*
            本地 Python

            WWA.exe
                └── pythonw.exe
                       └── main.py
        */

        snprintf(
            cmdline,
            sizeof(cmdline),
            "\"%s\" main.py",
            local_python
        );


        if (!CreateProcessA(
                local_python,
                cmdline,
                NULL,
                NULL,
                FALSE,
                0,
                NULL,
                NULL,
                &si,
                &pi
        ))
        {
            char msg[256];

            snprintf(
                msg,
                sizeof(msg),
                "Failed to start pythonw.exe.\nError code: %lu",
                GetLastError()
            );

            MessageBoxA(
                NULL,
                msg,
                "Error",
                MB_OK | MB_ICONERROR
            );

            return 1;
        }
    }
    else
    {
        /*
            保留你的 Conda 逻辑
            不修改
        */

        snprintf(
            cmdline,
            sizeof(cmdline),
            "powershell.exe -Command \"conda run -n wwa-cuda python main.py\""
        );


        if (!CreateProcess(
                NULL,
                cmdline,
                NULL,
                NULL,
                FALSE,
                CREATE_NO_WINDOW,
                NULL,
                NULL,
                &si,
                &pi
        ))
        {
            char msg[256];

            snprintf(
                msg,
                sizeof(msg),
                "Failed to start conda.\nError code: %lu",
                GetLastError()
            );

            MessageBoxA(
                NULL,
                msg,
                "Error",
                MB_OK | MB_ICONERROR
            );

            return 1;
        }
    }


    /*
        等待 Python 退出

        保持：

        WWA.exe
            └── pythonw.exe
    */
    WaitForSingleObject(
        pi.hProcess,
        INFINITE
    );


    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);


    return 0;
}