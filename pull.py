#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT

import glob
import itertools
import json
import os
import sys
import urllib.parse
import urllib.request

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree


URI = 'https://www.gnu.org/licenses/license-list.html'

TAGS = {
    'blue': {'viewpoint'},
    'green': {'glp-compatible', 'libre'},
    'orange': {'libre'},
    'purple': {'fdl-compatible', 'libre'},
    'red': {'non-free'},
}

SPLITS = {
    'AcademicFreeLicense': [ # all versions through 3.0
        'AcademicFreeLicense1.1',
        'AcademicFreeLicense1.2',
        'AcademicFreeLicense2.0',
        'AcademicFreeLicense2.1',
        'AcademicFreeLicense3.0',
    ],
    'CC-BY-NC': [ # any version (!)
        'CC-BY-NC-1.0',
        'CC-BY-NC-2.0',
        'CC-BY-NC-2.5',
        'CC-BY-NC-3.0',
        'CC-BY-NC-4.0',
    ],
    'CC-BY-ND': [ # any version
        'CC-BY-ND-1.0',
        'CC-BY-ND-2.0',
        'CC-BY-ND-2.5',
        'CC-BY-ND-3.0',
        'CC-BY-ND-4.0',
    ],
    'FDL': [
        'FDLv1.1',
        'FDLv1.2',
        'FDLv1.3',
    ],
    'FDLOther': [ # unify with FDL (multi-tag)
        'FDLv1.1',
        'FDLv1.2',
        'FDLv1.3',
    ],
    'FreeBSDDL': ['FreeBSD'],  # unify (multi-tag)
    # FIXME: still working through this
}

IDENTIFIERS = {
    'AGPLv1.0': {'spdx': 'AGPL-1.0'},
    'AGPLv3.0': {'spdx': 'AGPL-3.0'},
    'AcademicFreeLicense1.1': {'spdx': 'AFL-1.1'},
    'AcademicFreeLicense1.2': {'spdx': 'AFL-1.2'},
    'AcademicFreeLicense2.0': {'spdx': 'AFL-2.0'},
    'AcademicFreeLicense2.1': {'spdx': 'AFL-2.1'},
    'AcademicFreeLicense3.0': {'spdx': 'AFL-3.0'},
    'Aladdin': {'spdx': 'Aladdin'},
    'ArtisticLicense': {'spdx': 'Artistic-1.0'},
    'ArtisticLicense2': {'spdx': 'Artistic-2.0'},
    'BerkeleyDB': {'spdx': 'Sleepycat'},
    'CC-BY-NC-1.0': {'spdx': 'CC-BY-NC-1.0'},
    'CC-BY-NC-2.0': {'spdx': 'CC-BY-NC-2.0'},
    'CC-BY-NC-2.5': {'spdx': 'CC-BY-NC-2.5'},
    'CC-BY-NC-3.0': {'spdx': 'CC-BY-NC-3.0'},
    'CC-BY-NC-4.0': {'spdx': 'CC-BY-NC-4.0'},
    'CC-BY-ND-1.0': {'spdx': 'CC-BY-ND-1.0'},
    'CC-BY-ND-2.0': {'spdx': 'CC-BY-ND-2.0'},
    'CC-BY-ND-2.5': {'spdx': 'CC-BY-ND-2.5'},
    'CC-BY-ND-3.0': {'spdx': 'CC-BY-ND-3.0'},
    'CC-BY-ND-4.0': {'spdx': 'CC-BY-ND-4.0'},
    'CC0': {'spdx': 'CC0-1.0'},
    'CDDL': {'spdx': 'CDDL-1.0'},
    'CPAL': {'spdx': 'CPAL-1.0'},
    'CeCILL': {'spdx': 'CECILL-2.0'},
    'CeCILL-B': {'spdx': 'CECILL-B'},
    'CeCILL-C': {'spdx': 'CECILL-C'},
    'ClarifiedArtistic': {'spdx': 'ClArtistic'},
    'CommonPublicLicense10': {'spdx': 'CPL-1.0'},
    'Condor': {'spdx': 'Condor-1.1'},
    'ECL2.0': {'spdx': 'ECL-2.0'},
    'EPL': {'spdx': 'EPL-1.0'},
    'EPL2': {'spdx': 'EPL-2.0'}, # not in license-list-XML yet
    'EUDataGrid': {'spdx': 'EUDatagrid'},
    'EUPL': {'spdx': 'EUPL-1.1'},
    'Eiffel': {'spdx': 'EFL-2.0'},
    'Expat': {'spdx': 'MIT'},
    'FDLv1.1': {'spdx': 'GFDL-1.1'},
    'FDLv1.2': {'spdx': 'GFDL-1.2'},
    'FDLv1.3': {'spdx': 'GFDL-1.3'},
    'FreeBSD': {'spdx': 'BSD-2-Clause-FreeBSD'},
    'GNUAllPermissive': {'spdx': 'FSFAP'},
    'GNUGPLv3': {'spdx': 'GPL-3.0'},
    # FIXME: still working through this
}


def get(uri):
    parser = etree.XMLParser(ns_clean=True, resolve_entities=False)
    with urllib.request.urlopen(uri) as response:
        return etree.parse(response, base_url=uri, parser=parser)


def extract(root, base_uri=None):
    oids = set()
    licenses = {}
    for dl in root.iter(tag='{http://www.w3.org/1999/xhtml}dl'):
        try:
            tags = TAGS[dl.attrib.get('class')]
        except KeyError:
            raise ValueError(
                'unrecognized class {!r}'.format(dl.attrib.get('class')))
        for a in dl.iter(tag='{http://www.w3.org/1999/xhtml}a'):
            if 'id' not in a.attrib:
                continue
            oid = a.attrib['id']
            oids.add(oid)
            for id in SPLITS.get(oid, [oid]):
                license = {
                    'tags': tags.copy(),
                }
                if a.text and a.text.strip():
                    license['name'] = a.text.strip()
                else:
                    continue
                uri = a.attrib.get('href')
                if uri:
                    if base_uri:
                        uri = urllib.parse.urljoin(base=base_uri, url=uri)
                    license['uri'] = uri
                identifiers = IDENTIFIERS.get(id)
                if identifiers:
                    license['identifiers'] = identifiers
                if id not in licenses:
                    licenses[id] = license
                else:
                    licenses[id]['tags'].update(tags)
    unused_splits = set(SPLITS.keys()).difference(oids)
    if unused_splits:
        raise ValueError('unused SPLITS keys: {}'.format(
            ', '.join(sorted(unused_splits))))
    return licenses


def save(licenses, dir=os.curdir):
    os.makedirs(dir, exist_ok=True)
    if sys.version_info >= (3, 5):
        paths = glob.glob(os.path.join(dir, '**', '*.json'), recursive=True)
    else:
        paths = itertools.chain(
            glob.glob(os.path.join(dir, '*.json')),
            glob.glob(os.path.join(dir, '*', '*.json')),
        )
    for path in paths:
        os.remove(path)
    index = sorted(licenses.keys())
    with open(os.path.join(dir, 'licenses.json'), 'w') as f:
        json.dump(obj=index, fp=f, indent=2)
        f.write('\n')
    for id, license in licenses.items():
        license = license.copy()
        if 'tags' in license:
            license['tags'] = sorted(license['tags'])
        license_path = os.path.join(dir, '{}.json'.format(id))
        with open(license_path, 'w') as f:
            json.dump(obj=license, fp=f, indent=2, sort_keys=True)
            f.write('\n')
        for scheme, identifier in license.get('identifiers', {}).items():
            scheme_dir = os.path.join(dir, scheme)
            os.makedirs(scheme_dir, exist_ok=True)
            id_path = os.path.join(scheme_dir, '{}.json'.format(identifier))
            os.link(license_path, id_path)


if __name__ == '__main__':
    dir = os.curdir
    if len(sys.argv) > 1:
        dir = sys.argv[1]
    tree = get(uri=URI)
    root = tree.getroot()
    licenses = extract(root=root, base_uri=URI)
    unused_identifiers = {
        key for key in IDENTIFIERS.keys() if key not in licenses}
    if unused_identifiers:
        raise ValueError('unused IDENTIFIERS keys: {}'.format(
            ', '.join(sorted(unused_identifiers))))
    save(licenses=licenses, dir=dir)
