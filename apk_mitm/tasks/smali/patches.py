from typing import List

from apk_mitm.tasks.smali.types import SmaliPatch, SmaliPatchSelector, SmaliMethodPatch

# `return void;` in Smali.
RETURN_VOID_SMALI = ['.locals 0', 'return-void']

# `return true;` in Smali.
RETURN_TRUE_SMALI = ['.locals 1', 'const/4 v0, 0x1', 'return v0']

# `return new java.security.cert.X509Certificate[] {};` in Smali.
RETURN_EMPTY_CERT_ARRAY_SMALI = [
    '.locals 1',
    'const/4 v0, 0x0',
    'new-array v0, v0, [Ljava/security/cert/X509Certificate;',
    'return-object v0',
]

#
# A declarative list of all the patches that are
# applied to Smali code to disable certificate pinning.
#
smali_patches: List[SmaliPatch] = [
    SmaliPatch(
        selector=SmaliPatchSelector(
            type='interface',
            name='javax/net/ssl/X509TrustManager',
        ),
        methods=[
            SmaliMethodPatch(
                name='X509TrustManager#checkClientTrusted (javax)',
                signature='checkClientTrusted([Ljava/security/cert/X509Certificate;Ljava/lang/String;)V',
                replacement_lines=RETURN_VOID_SMALI,
            ),
            SmaliMethodPatch(
                name='X509TrustManager#checkServerTrusted (javax)',
                signature='checkServerTrusted([Ljava/security/cert/X509Certificate;Ljava/lang/String;)V',
                replacement_lines=RETURN_VOID_SMALI,
            ),
            SmaliMethodPatch(
                name='X509TrustManager#getAcceptedIssuers (javax)',
                signature='getAcceptedIssuers()[Ljava/security/cert/X509Certificate;',
                replacement_lines=RETURN_EMPTY_CERT_ARRAY_SMALI,
            ),
        ],
    ),
    SmaliPatch(
        selector=SmaliPatchSelector(
            type='interface',
            name='javax/net/ssl/HostnameVerifier',
        ),
        methods=[
            SmaliMethodPatch(
                name='HostnameVerifier#verify (javax)',
                signature='verify(Ljava/lang/String;Ljavax/net/ssl/SSLSession;)Z',
                replacement_lines=RETURN_TRUE_SMALI,
            ),
        ],
    ),
    SmaliPatch(
        selector=SmaliPatchSelector(
            type='class',
            name='com/squareup/okhttp/CertificatePinner',
        ),
        methods=[
            SmaliMethodPatch(
                name='HostnameVerifier#check (OkHttp 2.5)',
                # Inspired by: https://github.com/Fuzion24/JustTrustMe/blob/152557d/app/src/main/java/just/trust/me/Main.java#L456-L478
                signature='check(Ljava/lang/String;Ljava/util/List;)V',
                replacement_lines=RETURN_VOID_SMALI,
            ),
        ],
    ),
    SmaliPatch(
        selector=SmaliPatchSelector(
            type='class',
            name='okhttp3/CertificatePinner',
        ),
        methods=[
            SmaliMethodPatch(
                name='CertificatePinner#check (OkHttp 3.x)',
                # Inspired by: https://github.com/Fuzion24/JustTrustMe/blob/152557d/app/src/main/java/just/trust/me/Main.java#L480-L499
                signature='check(Ljava/lang/String;Ljava/util/List;)V',
                replacement_lines=RETURN_VOID_SMALI,
            ),
            SmaliMethodPatch(
                name='CertificatePinner#check (OkHttp 4.2)',
                # Inspired by: https://github.com/Fuzion24/JustTrustMe/blob/152557d/app/src/main/java/just/trust/me/Main.java#L539-L558
                signature='check$okhttp(Ljava/lang/String;Lkotlin/jvm/functions/Function0;)V',
                replacement_lines=RETURN_VOID_SMALI,
            ),
        ],
    ),
]
