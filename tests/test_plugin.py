"""This module implements plugin test."""

from __future__ import absolute_import

import os
from subprocess import call
import shutil
import types

from swak.config import get_exe_dir
from swak.plugin import iter_plugins, get_plugins_dir, calc_plugins_hash,\
    get_plugins_initpy_path, PREFIX, import_plugins_package
from swak.util import test_logconfig

SWAK_CLI = 'swak.bat' if os.name == 'nt' else 'swak'

test_logconfig()


def plugin_filter(_dir):
    """Filter plugins."""
    return _dir in ['scounter', 'stdout']


def plugin_filter_ext(_dir):
    """Plugin filter for external plugin test."""
    return _dir in ['swak-testfoo']


def test_plugin_cmd(capfd):
    """Test plugin list & desc command."""
    cmd = [SWAK_CLI, '-vv', 'list']
    try:
        call(cmd)
    except FileNotFoundError:
        return

    out, err = capfd.readouterr()
    print(err)
    assert 'Swak has 4 standard plugins' in out

    # after first command, plugins/__init__.py shall exist.
    assert os.path.isfile(get_plugins_initpy_path(True))

    cmd = [SWAK_CLI, 'desc', 'in.counter']
    call(cmd)
    out, err = capfd.readouterr()
    assert "Generate incremental numbers" in out

    cmd = [SWAK_CLI, 'desc', 'in.notexist']
    call(cmd)
    out, err = capfd.readouterr()
    assert "Can not find" in err


def test_plugin_init_cmd(capfd):
    """Test plugin init command."""
    # remove previous test pacakge.
    base_dir = get_plugins_dir(False)
    plugin_dir = os.path.join(base_dir, 'swak-testfoo')
    if os.path.isdir(plugin_dir):
        shutil.rmtree(plugin_dir)

    cmd = [SWAK_CLI, 'init', '--type', 'in', '--type', 'par', '--type', 'mod',
           '--type', 'buf', '--type', 'out', 'testfoo', 'TestFoo']
    try:
        call(cmd)
    except FileNotFoundError:
        return
    out, err = capfd.readouterr()
    assert err == ''

    for pr in PREFIX:
        pfile = os.path.join(plugin_dir, '{}_testfoo.py'.format(pr))
        assert os.path.isfile(pfile)
        with open(pfile, 'rt') as f:
            code = f.read()
            assert "class TestFoo" in code

    readme_file = os.path.join(plugin_dir, 'README.md')
    assert os.path.isfile(readme_file)
    with open(readme_file, 'rt') as f:
        text = f.read()
        assert '# swak-testfoo' in text
        assert "plugin package for Swak" in text

    # enumerate external plugins
    plugin_infos = list(iter_plugins(False, _filter=plugin_filter_ext))
    assert plugin_infos[0].dname == 'swak-testfoo'

    # desc command should find new external plugins
    cmd = [SWAK_CLI, 'list']
    call(cmd)
    out, err = capfd.readouterr()
    assert 'in.testfoo' in out
    assert 'par.testfoo' in out

    # check duplicate plugin error
    cmd = [SWAK_CLI, 'init', '--type', 'out', 'stdout', 'Stdout']
    call(cmd)
    out, err = capfd.readouterr()
    assert 'already exists' in err

    shutil.rmtree(plugin_dir)

    # check after removing
    cmd = [SWAK_CLI, 'list']
    call(cmd)
    out, err = capfd.readouterr()
    assert err == ''
    assert '0 external plugin' in out


def test_plugin_util():
    """Test plugin util."""
    # check standard plugin dir
    path = os.path.join(get_exe_dir(), 'stdplugins')
    assert path == get_plugins_dir(True)
    plugin_infos = list(iter_plugins(True, None, plugin_filter))
    assert len(plugin_infos) > 0

    # check external plugin dir
    path = os.path.join(get_exe_dir(), 'plugins')
    assert path == get_plugins_dir(False)


def test_plugin_initpy():
    """Test plugin __init__.py."""
    # test plugin checksum
    h = calc_plugins_hash(iter_plugins(True, plugin_filter))
    assert '94d7a4e72a88639e8a136ea821effcdb' == h


def test_plugin_import():
    """Test import plugins from plugins base package."""
    stdplugins = import_plugins_package(True)
    assert isinstance(stdplugins, types.ModuleType)
    __import__('stdplugins.counter')
    __import__('stdplugins.filter')
