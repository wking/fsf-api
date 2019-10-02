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
    'green': {'gpl-2-compatible', 'gpl-3-compatible', 'libre'},
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
    'ccbynd': ['CC-BY-ND-4.0'],  # unify (multi-tag)
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
    'FreeBSDDL': ['FreeBSD'], # unify (multi-tag)
    'NPL': [ # versions 1.0 and 1.1
        'NPL-1.0',
        'NPL-1.1',
    ],
    'OSL': [ # any version through 3.0
        'OSL-1.0',
        'OSL-1.1',
        'OSL-2.0',
        'OSL-2.1',
        'OSL-3.0',
    ],
    'PythonOld': [ # 1.6b1 through 2.0 and 2.1
        'Python1.6b1',
        'Python2.0',
        'Python2.1',
    ],
    'SILOFL': [ # title has 1.1 but text says the same metadata applies to 1.0
        'SILOFL-1.0',
        'SILOFL-1.1',
    ],
    'Zope2.0': [ # versions 2.0 and 2.1
        'Zope2.0',
        'Zope2.1',
    ],
}

TAG_OVERRIDES = {
    'AGPLv3.0': {'libre', 'gpl-3-compatible'},
    'ECL2.0': {'libre', 'gpl-3-compatible'},
    'freetype': {'libre', 'gpl-3-compatible'},
    'GNUGPLv3': {'libre', 'gpl-3-compatible'},
    'GPLv2': {'libre', 'gpl-2-compatible'},
    'LGPLv3': {'libre', 'gpl-3-compatible'},
}

IDENTIFIERS = {
    'AGPLv1.0': {'spdx': ['AGPL-1.0']},
    'AGPLv3.0': {'spdx': ['AGPL-3.0-or-later', 'AGPL-3.0-only', 'AGPL-3.0']},
    'AcademicFreeLicense1.1': {'spdx': ['AFL-1.1']},
    'AcademicFreeLicense1.2': {'spdx': ['AFL-1.2']},
    'AcademicFreeLicense2.0': {'spdx': ['AFL-2.0']},
    'AcademicFreeLicense2.1': {'spdx': ['AFL-2.1']},
    'AcademicFreeLicense3.0': {'spdx': ['AFL-3.0']},
    'Aladdin': {'spdx': ['Aladdin']},
    'apache1.1': {'spdx': ['Apache-1.1']},
    'apache1': {'spdx': ['Apache-1.0']},
    'apache2': {'spdx': ['Apache-2.0']},
    'apsl1': {'spdx': ['APSL-1.0']},
    'apsl2': {'spdx': ['APSL-2.0']},
    'ArtisticLicense': {'spdx': ['Artistic-1.0']},
    'ArtisticLicense2': {'spdx': ['Artistic-2.0']},
    'BerkeleyDB': {'spdx': ['Sleepycat']},
    'bittorrent': {'spdx': ['BitTorrent-1.1']},
    'boost': {'spdx': ['BSL-1.0']},
    'ccby': {'spdx': ['CC-BY-4.0']},
    'CC-BY-NC-1.0': {'spdx': ['CC-BY-NC-1.0']},
    'CC-BY-NC-2.0': {'spdx': ['CC-BY-NC-2.0']},
    'CC-BY-NC-2.5': {'spdx': ['CC-BY-NC-2.5']},
    'CC-BY-NC-3.0': {'spdx': ['CC-BY-NC-3.0']},
    'CC-BY-NC-4.0': {'spdx': ['CC-BY-NC-4.0']},
    'CC-BY-ND-1.0': {'spdx': ['CC-BY-ND-1.0']},
    'CC-BY-ND-2.0': {'spdx': ['CC-BY-ND-2.0']},
    'CC-BY-ND-2.5': {'spdx': ['CC-BY-ND-2.5']},
    'CC-BY-ND-3.0': {'spdx': ['CC-BY-ND-3.0']},
    'CC-BY-ND-4.0': {'spdx': ['CC-BY-ND-4.0']},
    'ccbysa': {'spdx': ['CC-BY-SA-4.0']},
    'CC0': {'spdx': ['CC0-1.0']},
    'CDDL': {'spdx': ['CDDL-1.0']},
    'CPAL': {'spdx': ['CPAL-1.0']},
    'CeCILL': {'spdx': ['CECILL-2.0']},
    'CeCILL-B': {'spdx': ['CECILL-B']},
    'CeCILL-C': {'spdx': ['CECILL-C']},
    'ClarifiedArtistic': {'spdx': ['ClArtistic']},
    'clearbsd': {'spdx': ['BSD-3-Clause-Clear']},
    'CommonPublicLicense10': {'spdx': ['CPL-1.0']},
    'cpol': {'spdx': ['CPOL-1.02']},
    'Condor': {'spdx': ['Condor-1.1']},
    'ECL2.0': {'spdx': ['ECL-2.0']},
    'eCos11': {'spdx': ['RHeCos-1.1']},
    'eCos2.0': {'spdx': ['GPL-2.0+ WITH eCos-exception-2.0', 'eCos-2.0']},
    'EPL': {'spdx': ['EPL-1.0']},
    'EPL2': {'spdx': ['EPL-2.0']},
    'EUDataGrid': {'spdx': ['EUDatagrid']},
    'EUPL-1.1': {'spdx': ['EUPL-1.1']},
    'EUPL-1.2': {'spdx': ['EUPL-1.2']},
    'Eiffel': {'spdx': ['EFL-2.0']},
    'Expat': {'spdx': ['MIT']},
    'FDLv1.1': {'spdx': ['GFDL-1.1-or-later', 'GFDL-1.1-only', 'GFDL-1.1']},
    'FDLv1.2': {'spdx': ['GFDL-1.2-or-later', 'GFDL-1.2-only', 'GFDL-1.2']},
    'FDLv1.3': {'spdx': ['GFDL-1.3-or-later', 'GFDL-1.3-only', 'GFDL-1.3']},
    'FreeBSD': {'spdx': ['BSD-2-Clause-FreeBSD', 'BSD-2-Clause']},
    'freetype': {'spdx': ['FTL']},
    'GNUAllPermissive': {'spdx': ['FSFAP']},
    'GNUGPLv3': {'spdx': ['GPL-3.0-or-later', 'GPL-3.0-only', 'GPL-3.0', 'GPL-3.0+']},
    'gnuplot': {'spdx': ['gnuplot']},
    'GPLv2': {'spdx': ['GPL-2.0-or-later', 'GPL-2.0-only', 'GPL-2.0', 'GPL-2.0+']},
    'HPND': {'spdx': ['HPND']},
    'IBMPL': {'spdx': ['IPL-1.0']},
    'iMatix': {'spdx': ['iMatix']},
    'imlib': {'spdx': ['Imlib2']},
    'ijg': {'spdx': ['IJG']},
    'intel': {'spdx': ['Intel']},
    'IPAFONT': {'spdx': ['IPA']},
    'ISC': {'spdx': ['ISC']},
    'JSON': {'spdx': ['JSON']},
    'LGPLv3': {'spdx': ['LGPL-3.0-or-later', 'LGPL-3.0-only', 'LGPL-3.0', 'LGPL-3.0+']},
    'LGPLv2.1': {'spdx': ['LGPL-2.1-or-later', 'LGPL-2.1-only', 'LGPL-2.1', 'LGPL-2.1+']},
    'LPPL-1.2': {'spdx': ['LPPL-1.2']},
    'LPPL-1.3a': {'spdx': ['LPPL-1.3a']},
    'lucent102': {'spdx': ['LPL-1.02']},
    'ModifiedBSD': {'spdx': ['BSD-3-Clause']},
    'MPL': {'spdx': ['MPL-1.1']},
    'MPL-2.0': {'spdx': ['MPL-2.0']},
    'ms-pl': {'spdx': ['MS-PL']},
    'ms-rl': {'spdx': ['MS-RL']},
    'NASA': {'spdx': ['NASA-1.3']},
    'NCSA': {'spdx': ['NCSA']},
    'newOpenLDAP': {'spdx': ['OLDAP-2.7']},
    'Nokia': {'spdx': ['Nokia']},
    'NoLicense': {'spdx': ['NONE']},
    'NOSL': {'spdx': ['NOSL']},
    'NPL-1.0': {'spdx': ['NPL-1.0']},
    'NPL-1.1': {'spdx': ['NPL-1.1']},
    'ODbl': {'spdx': ['ODbL-1.0']},
    'oldOpenLDAP': {'spdx': ['OLDAP-2.3']},
    'OpenPublicL': {'spdx': ['OPL-1.0']},
    'OpenSSL': {'spdx': ['OpenSSL']},
    'OriginalBSD': {'spdx': ['BSD-4-Clause']},
    'OSL-1.0': {'spdx': ['OSL-1.0']},
    'OSL-1.1': {'spdx': ['OSL-1.1']},
    'OSL-2.0': {'spdx': ['OSL-2.0']},
    'OSL-2.1': {'spdx': ['OSL-2.1']},
    'OSL-3.0': {'spdx': ['OSL-3.0']},
    'PHP-3.01': {'spdx': ['PHP-3.01']},
    'Python2.0': {'spdx': ['Python-2.0']},
    'QPL': {'spdx': ['QPL-1.0']},
    'RPSL': {'spdx': ['RPSL-1.0']},
    'Ruby': {'spdx': ['Ruby']},
    'SGIFreeB': {'spdx': ['SGI-B-2.0']},
    'SILOFL-1.0': {'spdx': ['OFL-1.0']},
    'SILOFL-1.1': {'spdx': ['OFL-1.1']},
    'SPL': {'spdx': ['SPL-1.0']},
    'StandardMLofNJ': {'spdx': ['SMLNJ', 'StandardML-NJ']},
    'Unlicense': {'spdx': ['Unlicense']},
    'UPL': {'spdx': ['UPL-1.0']},
    'Vim': {'spdx': ['Vim']},
    'W3C': {'spdx': ['W3C']},
    'Watcom': {'spdx': ['Watcom-1.0']},
    'WTFPL': {'spdx': ['WTFPL']},
    'X11License': {'spdx': ['X11']},
    'XFree861.1License': {'spdx': ['XFree86-1.1']},
    'xinetd': {'spdx': ['xinetd']},
    'Yahoo': {'spdx': ['YPL-1.1']},
    'Zend': {'spdx': ['Zend-2.0']},
    'Zimbra': {'spdx': ['Zimbra-1.3']},
    'ZLib': {'spdx': ['Zlib', 'Nunit']},
    'Zope2.0': {'spdx': ['ZPL-2.0']},
    'Zope2.1': {'spdx': ['ZPL-2.1']},
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
                    'tags': TAG_OVERRIDES.get(id, tags).copy(),
                }
                if a.text and a.text.strip():
                    license['name'] = a.text.strip()
                else:
                    continue
                uris = ['{}#{}'.format(base_uri, oid)]
                uri = a.attrib.get('href')
                if uri:
                    if base_uri:
                        uris.append(urllib.parse.urljoin(base=base_uri, url=uri))
                license['uris'] = uris
                identifiers = IDENTIFIERS.get(id)
                if identifiers:
                    license['identifiers'] = identifiers
                if id not in licenses:
                    licenses[id] = license
                else:
                    licenses[id]['tags'].update(tags)
                    for uri in uris:
                        if uri not in licenses[id]['uris']:
                            licenses[id]['uris'].append(uri)
    unused_splits = set(SPLITS.keys()).difference(oids)
    if unused_splits:
        raise ValueError('unused SPLITS keys: {}'.format(
            ', '.join(sorted(unused_splits))))
    return licenses


def save(licenses, base_uri, dir=os.curdir):
    schema_dir = os.path.join(dir, 'schema')
    os.makedirs(schema_dir, exist_ok=True)
    if sys.version_info >= (3, 5):
        paths = glob.glob(os.path.join(dir, '**', '*.json'), recursive=True)
    else:
        paths = itertools.chain(
            glob.glob(os.path.join(dir, '*.json')),
            glob.glob(os.path.join(dir, '*', '*.json')),
        )
    for path in paths:
        os.remove(path)
    license_schema = {
        '@context': {
            'schema': 'https://schema.org/',
            'id': {
                '@id': 'schema:identifier'
            },
            'name': {
                '@id': 'schema:name',
            },
            'uris': {
                '@container': '@list',
                '@id': 'schema:url',
            },
            'tags': {
                '@id': 'schema:keywords',
            },
            'identifiers': {
                '@container': '@index',
                '@id': 'schema:identifier',
            },
        },
    }
    with open(os.path.join(schema_dir, 'license.jsonld'), 'w') as f:
        json.dump(obj=license_schema, fp=f, indent=2, sort_keys=True)
        f.write('\n')
    license_schema_uri = urllib.parse.urljoin(
        base=base_uri, url='schema/license.jsonld')
    licenses_schema = license_schema.copy()
    licenses_schema['@context']['licenses'] = {
        '@container': '@index',
        '@id': license_schema_uri,
    }
    licenses_schema.update(license_schema)
    with open(os.path.join(schema_dir, 'licenses.jsonld'), 'w') as f:
        json.dump(obj=licenses_schema, fp=f, indent=2, sort_keys=True)
        f.write('\n')
    licenses_schema_uri = urllib.parse.urljoin(
        base=base_uri, url='schema/licenses.jsonld')
    index = sorted(licenses.keys())
    with open(os.path.join(dir, 'licenses.json'), 'w') as f:
        json.dump(obj=index, fp=f, indent=2, sort_keys=True)
        f.write('\n')
    full_index = {
        '@context': licenses_schema_uri,
        'licenses': {},
    }
    for id, license in licenses.items():
        license = license.copy()
        if 'tags' in license:
            license['tags'] = sorted(license['tags'])
        license['id'] = id
        full_index['licenses'][id] = license.copy()
        license['@context'] = urllib.parse.urljoin(
            base=base_uri, url='schema/license.jsonld')
        license_path = os.path.join(dir, '{}.json'.format(id))
        with open(license_path, 'w') as f:
            json.dump(obj=license, fp=f, indent=2, sort_keys=True)
            f.write('\n')
        for scheme, identifiers in license.get('identifiers', {}).items():
            scheme_dir = os.path.join(dir, scheme)
            os.makedirs(scheme_dir, exist_ok=True)
            if isinstance(identifiers, str):
                identifiers = [identifiers]
            for identifier in identifiers:
                id_path = os.path.join(scheme_dir, '{}.json'.format(identifier))
                os.link(license_path, id_path)
    with open(os.path.join(dir, 'licenses-full.json'), 'w') as f:
        json.dump(obj=full_index, fp=f, indent=2, sort_keys=True)
        f.write('\n')


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
    save(licenses=licenses, base_uri='https://wking.github.io/fsf-api/', dir=dir)
