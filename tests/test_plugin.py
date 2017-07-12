import os
from subprocess import call
from io import StringIO

from swak.config import get_exe_dir
from swak.plugin import enumerate_plugins, get_plugins_dir, dump_plugin_import,\
    calc_plugin_hash, remove_plugin_initpy, check_plugin_initpy
from swak.main import parse_test_commands


def plugin_filter(_dir):
    return _dir in ['counter', 'stdout']


def plugin_filter1(_dir):
    return _dir in ['counter']


def test_plugin_cmd(capfd):
    cmd = ['swak', 'list']
    call(cmd)
    out, err = capfd.readouterr()
    assert 'Swak has {} plugin(s)'.format(1) in out

    cmd = ['swak', 'desc', 'in.Counter']
    call(cmd)
    out, err = capfd.readouterr()
    assert "Emit incremental number" in out

    cmd = ['swak', 'desc', 'in.NotExist']
    call(cmd)
    out, err = capfd.readouterr()
    assert "Can not find" in err


def test_plugin_util():
    path = os.path.join(get_exe_dir(), 'plugins')
    assert path == get_plugins_dir()

    plugin_infos = list(enumerate_plugins(None, plugin_filter))
    assert len(plugin_infos) > 0

    for pi in plugin_infos:
        print(pi)

    ret = list(parse_test_commands('in.Counter --fields 3 | out.Stdout'))
    assert len(ret) == 2
    assert ret[0][0] == 'in.Counter'
    assert ret[0][1] == '--fields'
    assert ret[0][2] == '3'
    assert ret[1][0] == 'out.Stdout'


def test_plugin_dump():
    dump = """\
# WARNING: Auto-generated code. Do not edit.

from __future__ import absolute_import

from swak.plugins.counter import in_counter
from swak.plugins.stdout import out_stdout

CHECKSUM = '7ed9a23f52202cd70253890a591bb96a'

MODULE_MAP = {
    'in.Counter': in_counter,
    'out.Stdout': out_stdout,
}
"""

    sbuf = StringIO()
    dump_plugin_import(sbuf)
    assert dump == sbuf.getvalue()
    sbuf.close()


def test_plugin_initpy():
    # test plugin checksum
    h = calc_plugin_hash(enumerate_plugins(None, plugin_filter1))
    assert '9d4feaa6af4dd11e31572d6c1896d8b2' == h

    # test plugins/__init__.py creation
    remove_plugin_initpy()

    # enumerate 1 plugin and __init__.py has been created.
    created, chksum1 = check_plugin_initpy(enumerate_plugins(None,
                                                             plugin_filter1))
    assert created

    # enumerate 1 plugin again and __init__.py hasn't been created.
    created, _ = check_plugin_initpy(enumerate_plugins(None, plugin_filter1))
    assert not created

    # enumerate 2 plugin and __init__.py has been created.
    created, chksum = check_plugin_initpy(enumerate_plugins(None,
                                                            plugin_filter))
    assert created
    assert chksum != chksum1