from __future__ import annotations

import ctypes
import os


def _pid_is_running_windows(pid: int) -> bool:
    # Windows-safe probe: never use os.kill(pid, 0) as a liveness check.
    process_query_limited_information = 0x1000
    still_active = 259
    error_access_denied = 5
    error_invalid_parameter = 87

    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        open_process = kernel32.OpenProcess
        open_process.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        open_process.restype = ctypes.c_void_p
        get_exit_code = kernel32.GetExitCodeProcess
        get_exit_code.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        get_exit_code.restype = ctypes.c_int
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = [ctypes.c_void_p]
        close_handle.restype = ctypes.c_int

        handle = open_process(process_query_limited_information, 0, int(pid))
        if not handle:
            err = ctypes.get_last_error()
            if err == error_access_denied:
                return True
            if err == error_invalid_parameter:
                return False
            return False

        try:
            exit_code = ctypes.c_uint32(0)
            ok = get_exit_code(handle, ctypes.byref(exit_code))
            if not ok:
                err = ctypes.get_last_error()
                if err == error_access_denied:
                    return True
                return True
            return int(exit_code.value) == still_active
        finally:
            close_handle(handle)
    except Exception:
        # Conservative fallback: do not reclaim locks or PID files when the probe fails.
        return True


def pid_is_running(pid: int | str) -> bool:
    """Return whether a PID appears live without terminating it on Windows."""
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return False
    if pid_int <= 0:
        return False

    if os.name == "nt":
        return _pid_is_running_windows(pid_int)

    try:
        os.kill(pid_int, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


__all__ = ["pid_is_running"]
