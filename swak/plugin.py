import os
import sys
import glob
from collections import namedtuple
import hashlib

from swak.config import get_exe_dir
from swak.exception import UnsupportedPython


PREFIX = ['in_', 'par_', 'tr_', 'buf_', 'out_', 'cmd_']

PluginInfo = namedtuple('PluginInfo', ['fname', 'pname', 'dname', 'desc',
                                       'module'])


class Plugin(object):
    """Base class for plugin."""

    def __init__(self): self.started = self.terminated = False

    def start(self):
        self.started = True

    def stop(self):
        self.started = False

    def terminate(self):
        self.terminated = True


class BaseInput(Plugin):
    """Base class for input plugin.

    Following methods should be implemented:
        read

    """

    def read(self):
        raise NotImplemented()


class BaseParser(Plugin):
    """Base class for parser plugin.

    Following methods should be implemented:
        execute

    """

    def parse(self):
        raise NotImplemented()


class BaseTransform(Plugin):
    """Base class for transform plugin

    Following methods should be implemented:
        transform

    """

    def transform(self):
        raise NotImplemented()


class BaseBuffer(Plugin):
    """Base class for buffer plugin.

    Following methods should be implemented:
        append

    """

    def append(self, record):
        raise NotImplemented()


class BaseOutput(Plugin):
    """Base class for output plugin.

    Following methods should be implemented:
        process or write

    """

    def process(self, record):
        raise NotImplemented()

    def write(self, chunk):
        raise NotImplemented()


class BaseCommand(Plugin):
    """Base class for command plugin.

    Following methods should be implemented:
        execute

    """

    def execute(self):
        raise NotImplemented()


BASE_CLASS_MAP = {
    'in_': BaseInput,
    'par_': BaseParser,
    'tr_': BaseTransform,
    'buf_': BaseBuffer,
    'out_': BaseOutput,
    'cmd_': BaseCommand,
}


def get_plugins_dir(_home=None):
    edir = get_exe_dir()
    return os.path.join(edir, 'plugins')


def enumerate_plugins(_home=None, _filter=None):
    """Enumerate plugin infos.

    While visiting each sub-directory of the plugin directory, yield plugin
    information if the directory conform plugin standard.

    Args:
        _home (str): Explict home directory. Defaults to None.
        _filter (function): filter plugins for test.

    Returns:
        PluginInfo:
    """
    pdir = get_plugins_dir(_home)
    if not os.path.isdir(pdir):
        raise ValueError("Directory '{}' is not exist.".format(pdir))

    for _dir in os.listdir(pdir):
        if _dir.startswith('_'):
            continue
        if _filter is not None and not _filter(_dir):
            continue

        adir = os.path.join(pdir, _dir)
        pi = validate_plugin_info(adir)
        if pi is not None:
            yield pi


def validate_plugin_info(adir):
    """Check a directory whether it conforms plugin rules.

    Valid plugin rules:

    1. The directory has a python script with a name of standard plugin module
        name:

        plugin type prefix(`in`, `par`, `tr`, `buf`, `out`, `cmd`) + '_' +
        module name(snake case).
        ex) in_fake_data.py

    2. TODO

    Args:
        adir: Absolute directory path to test.

    Returns:
        PluginInfo: If the direcotry is valid.
        None: If not.
    """
    for pypath in glob.glob(os.path.join(adir, '*.py')):
        fname = os.path.basename(pypath)
        for pr in PREFIX:
            if not fname.startswith(pr):
                continue
            mod = load_module(fname, pypath)
            pclass = _infer_plugin_class(mod, pr, fname)
            prefix = pr.replace('_', '.')
            pname = '{}{}'.format(prefix, pclass.__name__)
            dname = os.path.basename(adir)
            return PluginInfo(fname, pname, dname, mod.main.help, mod)


def _infer_plugin_class(mod, pr, fname):
    name = fname.replace(pr, '').split('.')[0]

    if pr in BASE_CLASS_MAP:
        bclass = BASE_CLASS_MAP[pr]
    else:
        raise ValueError("Unknown prefix: '{}'".format(pr))

    for n in dir(mod):
        obj = getattr(mod, n)
        n = n.lower()
        if issubclass(obj, bclass) and n == name:
            return obj


def load_module(name, path):
    """Load a module considering python versions.

    Args:
        name: Module name
        path: Absolute path to the module.

    Returns:
        module: Imported module.
    """
    major, minor = sys.version_info[0:2]
    if major == 2:
        import imp
        return imp.load_source(name, path)
    if major == 3 and minor >= 5:
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    else:
        raise UnsupportedPython()


def dump_plugin_import(io, chksum=None):
    """Enumerate all plugins and dump import code to io.

    Args:
        io (IOBase): an IO instance where import code is written to.
        chksum (str): Explicitly given checksum.
    """
    io.write(u"# WARNING: Auto-generated code. Do not edit.\n\n")
    io.write(u'from __future__ import absolute_import\n\n')

    plugins = []
    for pi in enumerate_plugins():
        fname = os.path.splitext(pi.fname)[0]
        io.write(u'from swak.plugins.{} import {}\n'.format(pi.dname, fname))
        plugins.append((pi.pname, fname))

    if chksum is None:
        chksum = calc_plugin_hash(enumerate_plugins())
    io.write(u'\nCHECKSUM = \'{}\'\n'.format(chksum))

    io.write(u'\nMODULE_MAP = {\n')
    for pl in plugins:
        io.write(u"    '{}': {},\n".format(pl[0], pl[1]))
    io.write(u'}\n')


def calc_plugin_hash(plugin_infos):
    """Make plugins hash.

    Hash value is made by md5 algorithm with plugin module names.

    Args:
        plugin_infos: generator of PluginInfo

    Returns:
        str: Hexadecimal hash value
    """
    m = hashlib.md5()
    for pi in plugin_infos:
        m.update(pi.fname.encode('utf8'))
    return m.hexdigest()


def _plugins_initpy_path():
    return os.path.join(get_exe_dir(), 'plugins', '__init__.py')


def remove_plugin_initpy():
    """Remove plugins/__init__.py file."""
    path = _plugins_initpy_path()
    if os.path.isfile(path):
        os.unlink(path)


def check_plugin_initpy(plugin_infos):
    """Create plugins/__init__.py file if plugins checksum has been changed.

    Args:
        plugin_infos: Generator of PluginInfo

    Returns:
        bool: Where file has been created.
        str: Plugins checksum
    """
    create = False
    path = _plugins_initpy_path()
    chksum = calc_plugin_hash(plugin_infos)
    if not os.path.isfile(path):
        create = True
    else:
        mod = load_module('__init__.py', path)
        create = mod.CHECKSUM != chksum

    if create:
        with open(path, 'wt') as f:
            dump_plugin_import(f, chksum)

    return create, chksum