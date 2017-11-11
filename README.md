# FSF License Metadata API

The FSF is [interested in having the SPDX expose some of its metadata in the SPDX license list][fsf-api].
The cleanest way to do that is to have the FSF provide [their annotated license list][fsf-list] in a format that is more convenient for automated tools.
For example, [the OSI provides an API][osi-api] which, while [currently][osi-api-noncanon-1] [non-canonical][osi-api-non-canon-2], provides convenient access to OSI license annotations.

This repository scrapes the FSF list and provides the scraped data in a JSON API for others to consume.
Ideally we'll hand this repository over to the FSF once they're ready to maintain it, or we'll deprecate this repository if they decide to provide a different API.

## Endpoints

<a name="licenses.json"></a>
You can pull an array of identifiers from [https://wking.github.io/fsf-api/licenses.json](https://wking.github.io/fsf-api/licenses.json).

<a name="licenses-full.json"></a>
You can pull an object with all the license data [https://wking.github.io/fsf-api/licenses-full.json](https://wking.github.io/fsf-api/licenses-full.json).

You can pull an individual license from a few places:

* <a name="by-fsf-id"></a>
    Using their FSF ID:

        https://wking.github.io/fsf-api/{id}.json

    For example [https://wking.github.io/fsf-api/Expat.json](https://wking.github.io/fsf-api/Expat.json).

* <a name="by-non-fsf-id"></a>
    Using a non-FSF ID, according to the mapping between other scheme and the FSF scheme asserted by this API:

        https://wking.github.io/fsf-api/{scheme}/{id}.json

    For example [https://wking.github.io/fsf-api/spdx/MIT.json](https://wking.github.io/fsf-api/spdx/MIT.json).
    This API currently [attempts](#caveats) to maintain the following mappings:

    * `spdx`, using [the SPDX identifiers][spdx-list].

## Caveats

There are currently two hacks in [the pulling script](pull.py):

* `SPLITS`, which:

    * Unpacks some places where [the FSF's HTML page][fsf-list] uses a single identifier for multiple licenses (e.g. [using `AcademicFreeLicense` for “all versions through 3.0”][fsf-afl]).
    * Repacks places where [the FSF's HTML page][fsf-list] uses two identifiers for the same license (e.g. to classify `FreeBSD` as both [GPL-compatible][fsf-freebsd-gpl] and [FDL-compatible][fsf-freebsd-fdl]).

* `IDENTIFIERS`, which maps FSF identifiers to other schemes.
    Ideally this would be based on [automated license-text comparison][automated-matching], but in order for that to work this API would have to expose the license text that the FSF considered for each ID.
    Currently, [the FSF's HTML page][fsf-list] links to license source, but not in a consistent enough way for me to extract the text.

Until these hacks are addressed, license IDs and the `identifiers` field should be taken with a grain of salt.

## Contributing

[Contributions](CONTRIBUTING.md) are welcome!

[automated-matching]: https://github.com/spdx/license-list-XML/issues/418
[fsf-afl]: https://www.gnu.org/licenses/license-list.html#AcademicFreeLicense
[fsf-api]: https://lists.spdx.org/pipermail/spdx-legal/2017-October/002281.html
[fsf-freebsd-fdl]: https://www.gnu.org/licenses/license-list.html#FreeBSDDL
[fsf-freebsd-gpl]: https://www.gnu.org/licenses/license-list.html#FreeBSD
[fsf-list]: https://www.gnu.org/licenses/license-list.html
[osi-api-non-canon-2]: https://github.com/OpenSourceOrg/licenses/issues/47
[osi-api-noncanon-1]: https://github.com/OpenSourceOrg/licenses/tree/f7ff223f9694ca0d5114fc82e43c74b5c5087891#is-this-authoritative
[osi-api]: https://api.opensource.org/
[spdx-list]: https://spdx.org/licenses/
