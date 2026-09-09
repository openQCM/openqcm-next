"""
File descriptors: how many the process may open, how many it has open.

Bench, 2026-09-09: START failed twice with "OSError: [Errno 24] Too many open
files" while creating a multiprocessing.Queue. The terminal running the app
had the macOS default soft limit, 256; one Worker costs about 100 descriptors
(14 queues, each a pipe plus its locks and semaphore -- lsof showed 65 PSXSEM
and 35 PIPE for one Worker), the process idles at ~140, and START used to build
the new Worker while the old one was still referenced, so for an instant there
were two: 240, one open dialog away from the limit.

Two things here. `raise_soft_limit()` lifts the soft limit to what the system
allows, so the application no longer depends on the shell that launched it.
`open_fd_count()` is the observable the main window prints on START and STOP,
"open file descriptors: N of limit M", so a leak would show as a slope in the
System Log instead of as a crash after the eighth cycle.
"""

import os
import sys

TAG = "[fdLimit]"

# tried in order until one is accepted; macOS refuses a soft limit above
# kern.maxfilesperproc even when the hard limit says "unlimited"
CANDIDATES = (65536, 32768, 16384, 10240, 4096, 2048, 1024)


def limits():
    """(soft, hard) or (None, None) where the platform has no rlimit."""
    try:
        import resource
        return resource.getrlimit(resource.RLIMIT_NOFILE)
    except (ImportError, ValueError, OSError):
        return (None, None)


def raise_soft_limit(candidates=CANDIDATES):
    """Lift the soft limit to the first candidate the system accepts.

    Returns (before, after). Never lowers it; never raises; on Windows, where
    there is no rlimit, returns (None, None).
    """
    soft, hard = limits()
    if soft is None:
        return (None, None)
    import resource
    for target in candidates:
        if target <= soft:
            break
        if hard != resource.RLIM_INFINITY and target > hard:
            continue
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
        except (ValueError, OSError):
            continue
        return (soft, target)
    return (soft, soft)


def open_fd_count():
    """Descriptors this process has open, or None where it cannot be counted."""
    for path in ("/dev/fd", "/proc/self/fd"):
        try:
            return len(os.listdir(path))
        except OSError:
            continue
    return None


def describe():
    """'open file descriptors: 142 of limit 65536', or what is known."""
    count = open_fd_count()
    soft, _hard = limits()
    if count is None:
        return "open file descriptors: not countable on {}".format(sys.platform)
    if soft is None:
        return "open file descriptors: {}".format(count)
    return "open file descriptors: {} of limit {}".format(count, soft)
