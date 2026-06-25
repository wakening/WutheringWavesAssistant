#include <windows.h>
#include <io.h>     // _access
#include <stdlib.h> // system

#pragma comment(lib, "User32.lib")

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    const char *local_python = "py312\\python.exe";

    STARTUPINFO si = { sizeof(si) };
    PROCESS_INFORMATION pi;

    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;

    char cmdline[1024];

    if (_access(local_python, 0) == 0) {
        // 如果本地 Python 存在，用 cmd /C 运行，避免卡住
        snprintf(cmdline, sizeof(cmdline), "cmd.exe /C \"%s main.py\"", local_python);
    } else {
        // 否则通过 Conda 环境运行
        snprintf(cmdline, sizeof(cmdline),
                 "powershell.exe -Command \"conda run -n wwa-cuda python main.py\"");
    }

    if (CreateProcess(
            NULL,
            // (LPSTR)"conda run -n wwa-cuda python main.py",
            // (LPSTR)"cmd.exe /c conda run -n wwa-cuda python main.py",
            // (LPSTR)"powershell.exe -Command \"conda run -n wwa-cuda python main.py\"",
            // (LPSTR)"powershell.exe -Command \"$p='$PWD\\py312\\python.exe'; if (Test-Path $p) { & $p 'main.py' } else { conda run -n wwa-cuda python main.py }\"",
            // (LPSTR)"cmd.exe /C \"if exist \"%cd%\\py312\\python.exe\" ( \"%cd%\\py312\\python.exe\" main.py ) else ( powershell.exe -Command \\\"conda run -n wwa-cuda python main.py\\\" )\"",
            cmdline,
            NULL,
            NULL,
            FALSE,
            CREATE_NO_WINDOW,
            NULL,
            NULL,
            &si,
            &pi
    )) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    } else {
        MessageBox(NULL, "Failed to start process.", "Error", MB_OK | MB_ICONERROR);
    }

    return 0;
}
