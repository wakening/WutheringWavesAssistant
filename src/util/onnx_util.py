import onnxruntime

"""
Preload DLLs
Since version 1.21.0, the onnxruntime-gpu package provides the preload_dlls function to preload CUDA, cuDNN, and Microsoft Visual C++ (MSVC) runtime DLLs. This function offers flexibility in specifying which libraries to load and from which directories.

Function Signature:

onnxruntime.preload_dlls(cuda=True, cudnn=True, msvc=True, directory=None)

Parameters:

cuda (bool): Preload CUDA DLLs if set to True.
cudnn (bool): Preload cuDNN DLLs if set to True.
msvc (bool): Preload MSVC runtime DLLs if set to True.
directory (str or None): Directory to load the DLLs from.
None: Search in default directories.
"" (empty string): Search in NVIDIA site packages.
Specific path: Load DLLs from the specified directory.  
"""


def preload_dlls():
    # https://github.com/microsoft/onnxruntime/pull/23674
    # https://github.com/microsoft/onnxruntime/pull/23744
    onnxruntime.preload_dlls(cuda=True, cudnn=True, msvc=True, directory=None)
    onnxruntime.print_debug_info()
