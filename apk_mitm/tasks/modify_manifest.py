from apk_mitm.utils import fs
from apk_mitm.dependencies import xml_js


async def modify_manifest(
    path: str,
    debuggable: bool = False,
    maps_api_key: str = '',
):
    document = xml_js.xml2js(await fs.read_file(path, 'utf-8'))

    manifest = next(el for el in (document.get('elements') or []) if el.get('name') == 'manifest')
    application = next(el for el in (manifest.get('elements') or []) if el.get('name') == 'application')

    application['attributes'] = {
        **(application.get('attributes') or {}),

        # Configure app to use custom Network Security Config
        'android:networkSecurityConfig': '@xml/nsc_mitm',

        # Make app debuggable when `--debuggable` flag is used
        **(({'android:debuggable': 'true'}) if debuggable else {}),
    }

    uses_app_bundle = any(
        el.get('name') == 'meta-data' and
        (el.get('attributes') or {}).get('android:name') == 'com.android.vending.splits'
        for el in (application.get('elements') or [])
    )

    if maps_api_key:
        for el in (application.get('elements') or []):
            if el.get('name') == 'meta-data':
                name = str((el.get('attributes') or {}).get('android:name', '')) + ''
                maps_api_name = [
                    'com.google.android.maps.v2.API_KEY',
                    'com.google.android.geo.API_KEY',
                ]
                if name in maps_api_name:
                    el['attributes']['android:value'] = maps_api_key

    await fs.write_file(path, xml_js.js2xml(document, {'spaces': 4}))

    return {'usesAppBundle': uses_app_bundle}
