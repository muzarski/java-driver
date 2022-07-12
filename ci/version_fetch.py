#!/usr/bin/python3

"""
This Python script allows you to list the
latest version numbers of Scylla and Cassandra.
You can specify whether you want the
versions of Scylla OSS or Scylla Enterprise,
either N latest stable X.Y.latest or
all non-obsolete RCs. You can also fetch
the latest version of Cassandra 3.
How are those versions fetched? We use Docker Hub
tags API.
"""

import requests
import re
import json
from itertools import groupby, islice
import sys

DOCKER_HUB_TAGS_ENDPOINT = 'https://registry.hub.docker.com/v1/repositories/%s/tags'
DOCKER_HUB_SCYLLA_ORG = 'scylladb/'

SCYLLA_OSS = DOCKER_HUB_SCYLLA_ORG + 'scylla'
SCYLLA_OSS_RELEASED_VERSION_REGEX = re.compile(r'(\d+)\.(\d+)\.(\d+)')
SCYLLA_OSS_RC_VERSION_REGEX = re.compile(r'(\d+)\.(\d+)\.rc(\d+)')

SCYLLA_ENTERPRISE = DOCKER_HUB_SCYLLA_ORG + 'scylla-enterprise'
SCYLLA_ENTERPRISE_RELEASED_VERSION_REGEX = re.compile(r'(\d{4})\.(\d+)\.(\d+)')
SCYLLA_ENTERPRISE_RC_VERSION_REGEX = re.compile(r'(\d{4})\.(\d+)\.rc(\d+)')

CASSANDRA_ENDPOINT = 'https://dlcdn.apache.org/cassandra/'

CASSANDRA3_REGEX = re.compile(r'a href="(3)\.(\d+)\.(\d+)/"')
CASSANDRA4_REGEX = re.compile(r'a href="(4)\.(\d+)\.(\d+)/"')

COMMAND_LINE_ARGUMENT = re.compile(
    r'((?:(scylla-oss-stable):(\d+))|(?:(scylla-enterprise-stable):(\d+))|(?:(cassandra3-stable):(\d+))|(?:(cassandra4-stable):(\d+))|(?:(scylla-oss-rc))|(?:(scylla-enterprise-rc)))')


def fetch_last_scylla_oss_minor_versions(count):
    # Download Docker tags for repository
    tags_data = requests.get(DOCKER_HUB_TAGS_ENDPOINT % (SCYLLA_OSS)).json()
    tags_data = map(lambda e: e['name'], tags_data)

    # Parse only those tags which match 'NUM.NUM.NUM'
    # into tuple (NUM, NUM, NUM)
    tags_data = filter(SCYLLA_OSS_RELEASED_VERSION_REGEX.fullmatch, tags_data)
    tags_data = map(lambda e: SCYLLA_OSS_RELEASED_VERSION_REGEX.match(
        e).groups(), tags_data)
    tags_data = map(lambda e: tuple(map(int, e)), tags_data)

    # Group by (major, minor) and select latest patch version
    tags_data = sorted(tags_data)
    tags_data = groupby(tags_data, key=lambda e: (e[0], e[1]))
    tags_data = ((e[0][0], e[0][1], max(e[1])[2])
                 for e in tags_data)

    # Return the latest ones
    tags_data = list(tags_data)[-count:]
    tags_data = [f'{e[0]}.{e[1]}.{e[2]}' for e in tags_data]
    return tags_data


def fetch_all_scylla_oss_rc_versions():
    # Download Docker tags for repository
    tags_data = requests.get(DOCKER_HUB_TAGS_ENDPOINT % (SCYLLA_OSS)).json()
    tags_data = list(map(lambda e: e['name'], tags_data))

    # Parse only those tags which match 'NUM.NUM.rcNUM'
    # into tuple (NUM, NUM, NUM)
    rc_tags_data = filter(SCYLLA_OSS_RC_VERSION_REGEX.fullmatch, tags_data)
    rc_tags_data = map(lambda e: SCYLLA_OSS_RC_VERSION_REGEX.match(
        e).groups(), rc_tags_data)
    rc_tags_data = map(lambda e: tuple(map(int, e)), rc_tags_data)

    # Parse only those tags which match 'NUM.NUM.NUM'
    # into tuple (NUM, NUM)
    stable_tags_data = filter(
        SCYLLA_OSS_RELEASED_VERSION_REGEX.fullmatch, tags_data)
    stable_tags_data = map(lambda e: SCYLLA_OSS_RELEASED_VERSION_REGEX.match(
        e).groups(), stable_tags_data)
    stable_tags_data = map(lambda e: tuple(map(int, e[0:2])), stable_tags_data)
    stable_tags_data = set(stable_tags_data)

    # Group by (major, minor) and select latest RC version
    rc_tags_data = sorted(rc_tags_data)
    rc_tags_data = groupby(rc_tags_data, key=lambda e: (e[0], e[1]))
    rc_tags_data = ((e[0][0], e[0][1], max(e[1])[2])
                    for e in rc_tags_data)

    # Filter out those RCs that are obsoleted by released stable version
    rc_tags_data = filter(lambda e: (
        e[0], e[1]) not in stable_tags_data, rc_tags_data)
    rc_tags_data = [f'{e[0]}.{e[1]}.rc{e[2]}' for e in rc_tags_data]
    return rc_tags_data


def fetch_last_scylla_enterprise_minor_versions(count):
    # Download Docker tags for repository
    tags_data = requests.get(DOCKER_HUB_TAGS_ENDPOINT %
                             (SCYLLA_ENTERPRISE)).json()
    tags_data = map(lambda e: e['name'], tags_data)

    # Parse only those tags which match 'YEAR.NUM.NUM'
    # into tuple (YEAR, NUM, NUM)
    tags_data = filter(
        SCYLLA_ENTERPRISE_RELEASED_VERSION_REGEX.fullmatch, tags_data)
    tags_data = map(lambda e: SCYLLA_ENTERPRISE_RELEASED_VERSION_REGEX.match(
        e).groups(), tags_data)
    tags_data = map(lambda e: tuple(map(int, e)), tags_data)

    # Group by (major, minor) and select latest patch version
    tags_data = sorted(tags_data)
    tags_data = groupby(tags_data, key=lambda e: (e[0], e[1]))
    tags_data = ((e[0][0], e[0][1], max(e[1])[2])
                 for e in tags_data)

    # Return the latest ones
    tags_data = list(tags_data)[-count:]
    tags_data = [f'{e[0]}.{e[1]}.{e[2]}' for e in tags_data]
    return tags_data


def fetch_all_scylla_enterprise_rc_versions():
    # Download Docker tags for repository
    tags_data = requests.get(DOCKER_HUB_TAGS_ENDPOINT %
                             (SCYLLA_ENTERPRISE)).json()
    tags_data = list(map(lambda e: e['name'], tags_data))

    # Parse only those tags which match 'YEAR.NUM.rcNUM'
    # into tuple (YEAR, NUM, NUM)
    rc_tags_data = filter(
        SCYLLA_ENTERPRISE_RC_VERSION_REGEX.fullmatch, tags_data)
    rc_tags_data = map(lambda e: SCYLLA_ENTERPRISE_RC_VERSION_REGEX.match(
        e).groups(), rc_tags_data)
    rc_tags_data = map(lambda e: tuple(map(int, e)), rc_tags_data)

    # Parse only those tags which match 'YEAR.NUM.NUM'
    # into tuple (YEAR, NUM)
    stable_tags_data = filter(
        SCYLLA_ENTERPRISE_RELEASED_VERSION_REGEX.fullmatch, tags_data)
    stable_tags_data = map(lambda e: SCYLLA_ENTERPRISE_RELEASED_VERSION_REGEX.match(
        e).groups(), stable_tags_data)
    stable_tags_data = map(lambda e: tuple(map(int, e[0:2])), stable_tags_data)

    # Group by (major, minor) and select latest RC version
    rc_tags_data = sorted(rc_tags_data)
    rc_tags_data = groupby(rc_tags_data, key=lambda e: (e[0], e[1]))
    rc_tags_data = ((e[0][0], e[0][1], max(e[1])[2])
                    for e in rc_tags_data)

    # Filter out those RCs that are obsoleted by released stable version
    rc_tags_data = filter(lambda e: (
        e[0], e[1]) not in stable_tags_data, rc_tags_data)
    rc_tags_data = [f'{e[0]}.{e[1]}.rc{e[2]}' for e in rc_tags_data]
    return rc_tags_data


def fetch_last_cassandra3_minor_versions(count):
    # Download folder listing for Cassandra download site
    data = requests.get(CASSANDRA_ENDPOINT).text

    # Parse only those version numbers which match '3.NUM.NUM'
    # into tuple (3, NUM, NUM)
    data = CASSANDRA3_REGEX.finditer(data)
    data = map(lambda e: e.groups(), data)
    data = map(lambda e: tuple(map(int, e)), data)

    # Group by (major, minor) and select latest patch version
    data = sorted(data)
    data = groupby(data, key=lambda e: (e[0], e[1]))
    data = ((e[0][0], e[0][1], max(e[1])[2])
            for e in data)

    # Return the latest ones
    data = list(data)[-count:]
    data = [f'{e[0]}.{e[1]}.{e[2]}' for e in data]
    return data

def fetch_last_cassandra4_minor_versions(count):
    # Download folder listing for Cassandra download site
    data = requests.get(CASSANDRA_ENDPOINT).text

    # Parse only those version numbers which match '4.NUM.NUM'
    # into tuple (4, NUM, NUM)
    data = CASSANDRA4_REGEX.finditer(data)
    data = map(lambda e: e.groups(), data)
    data = map(lambda e: tuple(map(int, e)), data)

    # Group by (major, minor) and select latest patch version
    data = sorted(data)
    data = groupby(data, key=lambda e: (e[0], e[1]))
    data = ((e[0][0], e[0][1], max(e[1])[2])
            for e in data)

    # Return the latest ones
    data = list(data)[-count:]
    data = [f'{e[0]}.{e[1]}.{e[2]}' for e in data]
    return data


if __name__ == '__main__':
    names = set()

    for arg in sys.argv[1:]:
        if not COMMAND_LINE_ARGUMENT.fullmatch(arg):
            print("Usage:", sys.argv[0], "[scylla-oss-stable:COUNT] [scylla-oss-rc] [scylla-enterprise-stable:COUNT] [scylla-enterprise-rc] [cassandra3-stable:COUNT] [cassandra4-stable:COUNT]...", file=sys.stderr)
            sys.exit(1)

        groups = COMMAND_LINE_ARGUMENT.match(arg).groups()
        groups = [g for g in groups if g][1:]

        mode_name = groups[0]
        if mode_name == 'scylla-oss-stable':
            names.update(fetch_last_scylla_oss_minor_versions(int(groups[1])))
        elif mode_name == 'scylla-enterprise-stable':
            names.update(
                fetch_last_scylla_enterprise_minor_versions(int(groups[1])))
        elif mode_name == 'cassandra3-stable':
            names.update(
                fetch_last_cassandra3_minor_versions(int(groups[1])))
        elif mode_name == 'cassandra4-stable':
            names.update(
                fetch_last_cassandra4_minor_versions(int(groups[1])))
        elif mode_name == 'scylla-oss-rc':
            names.update(fetch_all_scylla_oss_rc_versions())
        elif mode_name == 'scylla-enterprise-rc':
            names.update(fetch_all_scylla_enterprise_rc_versions())

    print(json.dumps(list(names)))