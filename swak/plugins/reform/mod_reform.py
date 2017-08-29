"""Reform: A modifier plugin."""

import re
import socket

import click

from swak.plugin import BaseModifier

# Placeholder keys
PHK_HOSTNAME = '${hostname}'
PHK_HOSTADDR = '${hostaddr}'
PHK_TAG_PARTS = '\${tag_parts\[(-?\d)\]}'
PHK_HOSTADDR_PARTS = '\${hostaddr_parts\[(-?\d)\]}'
ptrn_tag_parts = re.compile(PHK_TAG_PARTS)
ptrn_hostaddr_parts = re.compile(PHK_HOSTADDR_PARTS)


def _tag_prefix(tag_parts):
    cnt = len(tag_parts)
    if cnt == 0:
        return []
    tag_prefix = [None] * cnt
    for i in range(1, cnt + 1):
        tag_prefix[i - 1] = '.'.join([tag_parts[j] for j in range(0, i)])
    return tag_prefix


def _tag_suffix(tag_parts):
    cnt = len(tag_parts)
    if cnt == 0:
        return []
    rev_tag_parts = tag_parts[::-1]
    rev_tag_suffix = [None] * cnt
    for i in range(1, cnt + 1):
        rev_tag_suffix[i - 1] = '.'.join([rev_tag_parts[j]
                                         for j in range(0, i)][::-1])
    return rev_tag_suffix


def _expand(val, placeholders):
    """Expand value string with placeholders.

    Args:
        val (str): A string value with possible placeholder.
        placeholders (dict): Placeholder value reference.

    Returns:
        dict: Expanded value
    """
    if PHK_HOSTNAME in val:
        phv = placeholders[PHK_HOSTNAME]
        val = val.replace(PHK_HOSTNAME, phv)
    if PHK_HOSTADDR in val:
        phv = placeholders[PHK_HOSTADDR]
        val = val.replace(PHK_HOSTADDR, phv)

    # expand tag_parts
    while True:
        m = ptrn_tag_parts.search(val)
        if m is None:
            break
        idx = int(m.groups()[0])
        key = '${{tag_parts[{}]}}'.format(idx)
        phv = placeholders[key]
        val = val.replace(key, phv)

    # expand hostaddr_parts
    while True:
        m = ptrn_hostaddr_parts.search(val)
        if m is None:
            break
        idx = int(m.groups()[0])
        key = '${{hostaddr_parts[{}]}}'.format(idx)
        phv = placeholders[key]
        val = val.replace(key, phv)

    return val


def _make_default_placeholders():
    """Make a default placeholder."""
    pholder = {}
    hostname = socket.gethostname()
    pholder[PHK_HOSTNAME] = hostname
    hostaddr = socket.gethostbyname(hostname)
    pholder[PHK_HOSTADDR] = hostaddr
    hostaddr_parts = hostaddr.split('.')
    for i in range(4):
        key = '${{hostaddr_parts[{}]}}'.format(i)
        pholder[key] = hostaddr_parts[i]
        rkey = '${{hostaddr_parts[{}]}}'.format(i - 4)
        pholder[rkey] = hostaddr_parts[i]
    return pholder


class Reform(BaseModifier):
    """Reform class."""

    def __init__(self, adds, dels=[]):
        """Init.

        Args:
            adds (list): List of (key, value) tuple to add.
            dels (list): List of key to delete.
        """
        for k, v in adds:
            assert type(k) == str and "Key must be a string"
            assert type(v) == str and "Value must be a string"
        self.adds = adds
        self.dels = dels

    def prepare_for_stream(self, tag, es):
        """Prepare to modify an event stream.

        Args:
            tag (str): Event tag
            es (EventStream): Event stream
        """
        placeholders = _make_default_placeholders()
        placeholders['tag'] = tag
        tag_parts = tag.split('.')
        tp_cnt = len(tag_parts)

        # tag parts
        placeholders['tag_parts'] = tag_parts
        for i in range(tp_cnt):
            key = '${{tag_parts[{}]}}'.format(i)
            placeholders[key] = tag_parts[i]
            rkey = '${{tag_parts[{}]}}'.format(i - tp_cnt)
            placeholders[rkey] = tag_parts[i]

        placeholders['tag_prefix'] = _tag_prefix(tag_parts)
        placeholders['tag_suffix'] = _tag_suffix(tag_parts)
        self.placeholders = placeholders

    def modify(self, tag, time, record):
        """Modify an event by modifying.

        If adds & dels conflicts, deleting key wins.

        Args:
            tag (str): Event tag
            time (float): Event time
            record (dict): Event record

        Returns:
            float: Modified time
            record: Modified record
        """
        self.placeholders['time'] = time
        self.placeholders['record'] = record
        for key, val in self.adds:
            record[key] = _expand(val, self.placeholders)

        for key in self.dels:
            del record[key]

        return time, record


@click.command(help="Add, delete, overwrite record field.")
@click.option('-a', '--add', "adds", type=(str, str), multiple=True,
              help="Add new key / value pair.")
@click.option('-d', '--del', "dels", type=str, multiple=True,
              help="Delete existing key / value pair by key.")
def main(adds, dels):
    """Plugin entry for CLI."""
    return Reform(adds, dels)


if __name__ == '__main__':
    main()