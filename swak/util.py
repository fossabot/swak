import os
import sys
from platform import platform
import collections
import errno
import logging

from swak.exception import UnsupportedPython

test_logger_inited = False

LOG_FMT = logging.Formatter('%(levelname)s [%(filename)s:%(lineno)d]'
                            ' %(message)s')

def make_dirs(adir):
    """Make directory if not exist."""
    try:
        os.makedirs(adir)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise
        else:
            # directory already exists
            pass


def is_windows():
    plt = platform()
    return 'Windows' in plt


def get_winsvc_status(svcname):
    import win32serviceutil
    import pywintypes

    try:
        ret = win32serviceutil.QueryServiceStatus(svcname)
    except pywintypes.error:
        return None
    return ret


def update_dict(d, u):
    """Update dictionary recursively.

    Update dictionary `d` with the value of `u` of matching key & hierarchy.

    Args:
        d (dict): Original dictionary to be updated.
        u (dict): Referential dictionary

    Returns:
        dict: Dictionary `d`

    """
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            r = update_dict(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def init_home(home, cfg):
    """Initialized required directories for home.

    Check following paths and make directories if needed.
        - run/
        - log/ (in view of logger/handlers/file/filename of config)
    """
    make_dirs(os.path.join(home, 'run'))
    make_dirs(os.path.join(home, 'logs'))
    if 'logger' in cfg:
        logger = cfg['logger']
        if 'handlers' in logger:
            handlers = logger['handlers']
            if 'file' in handlers:
                file = handlers['file']
                if 'filename' in file:
                    fname = file['filename']
                    dname = os.path.dirname(fname)
                    make_dirs(dname)


def query_stream_log_handler(logger):
    if len(logger.handlers):
        ch = logger.handlers[0]
    else:
        ch = logging.StreamHandler()
        logger.addHandler(ch)
    return ch


def test_logconfig():
    global test_logger_inited

    if test_logger_inited:
        return
    test_logger_inited = True

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = query_stream_log_handler(logger)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(LOG_FMT)


def check_python_version():
    """Check python version and return version info.

    Returns:
        int: 2 if Python version is 2.x
             3 if >= 3.5
             else raises.

    Raises:
        UnsupportedPython: If current python version is not supported.
    """
    vi = sys.version_info
    major, minor = vi[0:2]
    if major == 2:
        return 2
    if major == 3 and minor >= 5:
        return 3
    else:
        raise UnsupportedPython("Python {} is not supported".format(vi))


def log_level_from_verbosity(verbosity):
    if verbosity == 0:
        return 40
    elif verbosity == 1:
        return 20
    elif verbosity >= 2:
        return 10


def set_log_verbosity(verbosity):
    level = log_level_from_verbosity(verbosity)
    logger = logging.getLogger()
    logger.setLevel(level)
    handler = query_stream_log_handler(logger)
    handler.setLevel(level)
    handler.setFormatter(LOG_FMT)
