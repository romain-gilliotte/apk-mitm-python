import re


def _camel_case(s):
    is_camel_case = s != s.lower() and s != s.upper()
    if not is_camel_case:
        s = s.lower()
    if '-' not in s and '_' not in s:
        return s
    camelcase = ''
    next_chr_upper = False
    leading_hyphens = re.match(r'^-+', s)
    start = len(leading_hyphens.group(0)) if leading_hyphens else 0
    for i in range(start, len(s)):
        ch = s[i]
        if next_chr_upper:
            next_chr_upper = False
            ch = ch.upper()
        if i != 0 and (ch == '-' or ch == '_'):
            next_chr_upper = True
        elif ch != '-' and ch != '_':
            camelcase += ch
    return camelcase


class _Args(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self[name] = value

    def __missing__(self, key):
        return None


def parse(args, options=None):
    if options is None:
        options = {}

    string_opts = set(options.get('string', []) or [])
    boolean_opts = set(options.get('boolean', []) or [])

    result = _Args()
    result['_'] = []

    for key in boolean_opts:
        result[key] = False
        camel = _camel_case(key)
        if camel != key:
            result[camel] = False

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == '--':
            result['_'].extend(args[i + 1:])
            break

        if arg.startswith('--no-'):
            key = arg[5:]
            if key in boolean_opts or _camel_case(key) in boolean_opts:
                result[key] = False
                camel = _camel_case(key)
                if camel != key:
                    result[camel] = False
                i += 1
                continue

        if arg.startswith('--') and '=' in arg:
            key, value = arg[2:].split('=', 1)
            _set_arg(result, key, value, string_opts, boolean_opts)
            i += 1
            continue

        if arg.startswith('--'):
            key = arg[2:]

            if key in boolean_opts or _camel_case(key) in boolean_opts:
                next_val = args[i + 1] if i + 1 < len(args) else None
                if next_val is not None and re.match(r'^(true|false)$', next_val):
                    _set_arg(result, key, next_val, string_opts, boolean_opts)
                    i += 2
                else:
                    _set_arg(result, key, True, string_opts, boolean_opts)
                    i += 1
                continue

            if key in string_opts or _camel_case(key) in string_opts:
                if i + 1 < len(args):
                    _set_arg(result, key, args[i + 1], string_opts, boolean_opts)
                    i += 2
                else:
                    _set_arg(result, key, '', string_opts, boolean_opts)
                    i += 1
                continue

            if i + 1 < len(args) and not args[i + 1].startswith('-'):
                _set_arg(result, key, args[i + 1], string_opts, boolean_opts)
                i += 2
            else:
                _set_arg(result, key, True, string_opts, boolean_opts)
                i += 1
            continue

        result['_'].append(arg)
        i += 1

    return result


def _set_arg(result, key, value, string_opts, boolean_opts):
    if key in boolean_opts or _camel_case(key) in boolean_opts:
        if isinstance(value, str):
            value = value == 'true'

    if key in string_opts or _camel_case(key) in string_opts:
        if not isinstance(value, str):
            value = str(value)

    result[key] = value
    camel = _camel_case(key)
    if camel != key:
        result[camel] = value
