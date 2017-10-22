#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT

import glob
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
    'CC-BY': [ # any version
        'CC-BY-1.0',
        'CC-BY-2.0',
        'CC-BY-2.5',
        'CC-BY-3.0',
        'CC-BY-4.0',
    ],
    'CC-BY-SA': [ # any version
        'CC-BY-SA-1.0',
        'CC-BY-SA-2.0',
        'CC-BY-SA-2.5',
        'CC-BY-SA-3.0',
        'CC-BY-SA-4.0',
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
    'FreeArt': [ # any version
        'LAL-1.2',
        'LAL-1.3',
    ],
    'FreeBSDDL': ['FreeBSD'],  # unify (multi-tag)
    'NPL': [ #any version
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
    'RPL': [ # any version - Note that FSF website does not state any version, but references version 1.3 in the URL.  It is assumed that it also covers version 1.1 and 1.5, but this should be verified with FSF.
        'RPL-1.1',
        'RPL-1.3',
        'RPL-1.5',
    ],
    'Unicode': [ # any version
        'Unicode-DFS-2015',
        'Unicode-DFS-2016',
    ],
    'W3C': [ # any version
        'W3C',
        'W3C-20150513',
        'W3C-19980720',
    ],
    'Zope2.0': [ # Versions 2.0 and later
        'ZPL-2.0',
        'ZPL-2.1',
    ],
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
    'apache1.1': {'spdx': 'Apache-1.1'},
    'apache1': {'spdx': 'Apache-1.0'},
    'apache2': {'spdx': 'Apache-2.0'},
    'apsl1': {'spdx': 'APSL-1.0'},
    'apsl2': {'spdx': 'APSL-2.0'},
    'ArtisticLicense': {'spdx': 'Artistic-1.0'},
    'ArtisticLicense2': {'spdx': 'Artistic-2.0'},
    'BerkeleyDB': {'spdx': 'Sleepycat'},
    'bittorrent': {'spdx': 'BitTorrent-1.1'},
    'boost': {'spdx': 'BSL-1.0'},
    'CC-BY-1.0': {'spdx': 'CC-BY-1.0'},
    'CC-BY-2.0': {'spdx': 'CC-BY-2.0'},
    'CC-BY-2.5': {'spdx': 'CC-BY-2.5'},
    'CC-BY-3.0': {'spdx': 'CC-BY-3.0'},
    'CC-BY-4.0': {'spdx': 'CC-BY-4.0'},
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
    'CC-BY-SA-1.0': {'spdx': 'CC-BY-SA-1.0'},
    'CC-BY-SA-2.0': {'spdx': 'CC-BY-SA-2.0'},
    'CC-BY-SA-2.5': {'spdx': 'CC-BY-SA-2.5'},
    'CC-BY-SA-3.0': {'spdx': 'CC-BY-SA-3.0'},
    'CC-BY-SA-4.0': {'spdx': 'CC-BY-SA-4.0'},
    'CC0': {'spdx': 'CC0-1.0'},
    'CDDL': {'spdx': 'CDDL-1.0'},
    'CPAL': {'spdx': 'CPAL-1.0'},
    'CeCILL': {'spdx': 'CECILL-2.0'},
    'CeCILL-B': {'spdx': 'CECILL-B'},
    'CeCILL-C': {'spdx': 'CECILL-C'},
    'ClarifiedArtistic': {'spdx': 'ClArtistic'},
    'clearbsd': {'spdx': 'BSD-3-Clause-Clear'},
    'CommonPublicLicense10': {'spdx': 'CPL-1.0'},
    'cpol': {'spdx': 'CPOL-1.02'},
    'Condor': {'spdx': 'Condor-1.1'},
    'ECL2.0': {'spdx': 'ECL-2.0'},
    'eCos11': {'spdx': 'RHeCos-1.1'},
    'eCos2.0': {'spdx': 'GPL-2.0+ WITH eCos-exception-2.0'},
    'EPL': {'spdx': 'EPL-1.0'},
    'EPL2': {'spdx': 'EPL-2.0'}, # not in license-list-XML yet
    'EUDataGrid': {'spdx': 'EUDatagrid'},
    'EUPL': {'spdx': 'EUPL-1.1'},
    'Eiffel': {'spdx': 'EFL-2.0'},
    'Expat': {'spdx': 'MIT'},
    'FDL1.1': {'spdx': 'GFDL-1.1'},
    'FDL1.2': {'spdx': 'GFDL-1.2'},
    'FDL1.3': {'spdx': 'GFDL-1.3'},
    'FreeBSD': {'spdx': 'BSD-2-Clause-FreeBSD'},
    'freetype': {'spdx': 'FTL'},
    'GNUAllPermissive': {'spdx': 'FSFAP'},
    'GNUGPLv3': {'spdx': 'GPL-3.0'},
    'gnuplot': {'spdx': 'gnuplot'},
    'GPLv2': {'spdx': 'GPL-2.0'},
    'HPND': {'spdx': 'HPND'},
    'IBMPL': {'spdx': 'IPL-1.0'},
    'iMatix': {'spdx': 'iMatix'},
    'imlib': {'spdx': 'Imlib2'},
    'ijg': {'spdx': 'IJG'},
    'intel': {'spdx': 'Intel'},
    'IPAFONT': {'spdx': 'IPA'},
    'ISC': {'spdx': 'ISC'},
    'JSON': {'spdx': 'JSON'},
    'LAL-1.2': {'spdx':'LAL-1.2'},
    'LAL-1.3': {'spdx':'LAL-1.3'},
    'LGPLv3': {'spdx': 'LGPL-3.0'},
    'LGPLv2.1': {'spdx': 'LGPL-2.1'},
    'LPPL-1.2': {'spdx': 'LPPL-1.2'},
    'LPPL-1.3a': {'spdx': 'LPPL-1.3a'},
    'lucent102': {'spdx': 'LPL-1.02'},
    'ModifiedBSD': {'spdx': 'BSD-3-Clause'},
    'MPL': {'spdx': 'MPL-1.1'},
    'MPL-2.0': {'spdx':'MPL-2.0'},
    'ms-pl': {'spdx': 'MS-PL'},
    'ms-rl': {'spdx': 'MS-RL'},
    'NASA': {'spdx': 'NASA-1.3'},
    'NCSA': {'spdx':'NCSA'},
    'newOpenLDAP': {'spdx': 'OLDAP-2.7'},
    'Nokia': {'spdx': 'Nokia'},
    'NoLicense': {'spdx': 'NONE'},
    'NOSL': {'spdx': 'NOSL'},
    'NPL-1.0': {'spdx': 'NPL-1.0'},
    'NPL-1.1': {'spdx': 'NPL-1.1'},
    'ODbl': {'spdx': 'ODbL-1.0'},
    'oldOpenLDAP': {'spdx': 'OLDAP-2.7'},
    'OpenPublicL': {'spdx': 'OPL-1.0'},
    'OpenSSL': {'spdx': 'OpenSSL'},
    'OriginalBSD': {'spdx': 'BSD-4-Clause'},
    'OSL-1.0': {'spdx': 'OSL-1.0'},
    'OSL-1.1': {'spdx': 'OSL-1.1'},
    'OSL-2.0': {'spdx': 'OSL-2.0'},
    'OSL-2.1': {'spdx': 'OSL-2.1'},
    'OSL-3.0': {'spdx': 'OSL-3.0'},
    'PHP-3.01': {'spdx': 'PHP-3.01'},
    'Python': {'spdx': 'Python-2.0'}, # Note: references 'later versions which are not in the SPDX license list
    'QPL': {'spdx': 'QPL-1.0'},
    'RPL-1.1': {'spdx': 'RPL-1.1'},
    'RPL-1.5': {'spdx': 'RPL-1.5'},
    'RPSL': {'spdx': 'RPSL-1.0'},
    'Ruby': {'spdx': 'Ruby'}, # Note that the text linked is 'not an exact match to the SPDX license list
    'SGIFreeB': {'spdx': 'SGI-B-2.0'},
    'SILOFL': {'spdx': 'OFL-1.1'},
    'SISSL': {'spdx': 'SISSL'}, # Note that the header on the 'FSF website states version 1.0, but the link points to 'version 1.1.  The SPDX license is version 1.1
    'SPL': {'spdx': 'SPL-1.0'},
    'StandardMLofNJ': {'spdx': 'SMLNJ'},
    'Unicode-DFS-2015': {'spdx': 'Unicode-DFS-2015'},
    'Unicode-DFS-2016': {'spdx': 'Unicode-DFS-2016'},
    'Unlicense': {'spdx': 'Unlicense'},
    'UPL': {'spdx': 'UPL-1.0'},
    'Vim': {'spdx': 'Vim'},
    'W3C': {'spdx': 'W3C'},
    'W3C-20150513': {'spdx': 'W3C-20150513'},
    'W3C-19980720': {'spdx': 'W3C-19980720'},
    'Watcom': {'spdx': 'Watcom-1.0'},
    'WTFPL': {'spdx': 'WTFPL'},
    'X11License': {'spdx': 'X11'},
    'XFree861.1License': {'spdx': 'XFree86-1.1'},
    'xinetd': {'spdx': 'xinetd'},
    'Yahoo': {'spdx': 'YPL-1.1'},
    'Zend': {'spdx': 'Zend-2.0'},
    'Zimbra': {'spdx': 'Zimbra-1.3'},
    'ZLib': {'spdx': 'Zlib'},
    'Zope': {'spdx': 'ZPL-1.1'}, # Note the FSF refers to version 1.0 and SPDX uses version 1.1 - it should be verified that 1.1 should be included
    'ZPL-2.0': {'spdx': 'ZPL-2.0'},
    'ZPL-2.1': {'spdx': 'ZPL-2.1'},

    # FIXME: still working through this
}


def get(uri):
    parser = etree.XMLParser(ns_clean=True, resolve_entities=False)
    with urllib.request.urlopen(uri) as response:
        return etree.parse(response, base_url=uri, parser=parser)


def extract(root, base_uri=None):
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
    return licenses


def save(licenses, dir=os.curdir):
    os.makedirs(dir, exist_ok=True)
    for path in glob.glob(os.path.join(dir, '*.json')):
        os.remove(path)
    index = {}
    for id, license in licenses.items():
        index[id] = {'name': license['name']}
        if 'identifiers' in license:
            index[id]['identifiers'] = license['identifiers']
    with open(os.path.join(dir, 'licenses.json'), 'w') as f:
        json.dump(obj=index, fp=f, indent=2, sort_keys=True)
        f.write('\n')
    for id, license in licenses.items():
        license = license.copy()
        if 'tags' in license:
            license['tags'] = sorted(license['tags'])
        with open(os.path.join(dir, '{}.json'.format(id)), 'w') as f:
            json.dump(obj=license, fp=f, indent=2, sort_keys=True)
            f.write('\n')


if __name__ == '__main__':
    dir = os.curdir
    if len(sys.argv) > 1:
        dir = sys.argv[1]
    tree = get(uri=URI)
    root = tree.getroot()
    licenses = extract(root=root, base_uri=URI)
    save(licenses=licenses, dir=dir)
