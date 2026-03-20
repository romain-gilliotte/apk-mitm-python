from colorama import Fore, Style, init

init()

_STYLE_MAP = {
    'red': Fore.RED,
    'green': Fore.GREEN,
    'yellow': Fore.YELLOW,
    'blue': Fore.BLUE,
    'bold': Style.BRIGHT,
    'dim': Style.DIM,
    'italic': '\033[3m',
    'inverse': '\033[7m',
}

_RESET = Style.RESET_ALL


def _codes_for_styles(style_names):
    return ''.join(_STYLE_MAP[s] for s in style_names if s in _STYLE_MAP)


class _ChalkChain:
    def __init__(self, styles=None):
        self._styles = styles or []

    def _add(self, style_name):
        return _ChalkChain(self._styles + [style_name])

    def _apply(self, text):
        codes = _codes_for_styles(self._styles)
        return f'{codes}{text}{_RESET}'

    def __call__(self, *args):
        if len(args) == 1 and isinstance(args[0], str):
            return self._apply(args[0])
        text = ' '.join(str(a) for a in args)
        return self._apply(text)

    @property
    def red(self):
        return self._add('red')

    @property
    def green(self):
        return self._add('green')

    @property
    def yellow(self):
        return self._add('yellow')

    @property
    def blue(self):
        return self._add('blue')

    @property
    def bold(self):
        return self._add('bold')

    @property
    def dim(self):
        return self._add('dim')

    @property
    def italic(self):
        return self._add('italic')

    @property
    def inverse(self):
        return self._add('inverse')


def _parse_template(template, parent_styles=None):
    if parent_styles is None:
        parent_styles = []
    result = ''
    i = 0
    while i < len(template):
        if template[i] == '{':
            brace_depth = 1
            j = i + 1
            while j < len(template) and brace_depth > 0:
                if template[j] == '{':
                    brace_depth += 1
                elif template[j] == '}':
                    brace_depth -= 1
                j += 1
            inner = template[i + 1:j - 1]
            space_idx = inner.find(' ')
            newline_idx = inner.find('\n')
            if space_idx == -1:
                sep_idx = newline_idx
            elif newline_idx == -1:
                sep_idx = space_idx
            else:
                sep_idx = min(space_idx, newline_idx)
            if sep_idx != -1:
                style_part = inner[:sep_idx]
                style_names = style_part.split('.')
                if all(s in _STYLE_MAP for s in style_names):
                    content = inner[sep_idx:]
                    if inner[sep_idx] == ' ':
                        content = inner[sep_idx + 1:]
                    combined_styles = parent_styles + style_names
                    parsed_content = _parse_template(content, combined_styles)
                    codes = _codes_for_styles(combined_styles)
                    result += f'{codes}{parsed_content}{_RESET}'
                    if parent_styles:
                        result += _codes_for_styles(parent_styles)
                else:
                    result += '{' + _parse_template(inner, parent_styles) + '}'
            else:
                result += '{' + _parse_template(inner, parent_styles) + '}'
            i = j
        else:
            result += template[i]
            i += 1
    return result


class _Chalk(_ChalkChain):
    def __call__(self, *args):
        if len(args) == 1 and isinstance(args[0], str):
            if '{' in args[0]:
                return _parse_template(args[0])
            return self._apply(args[0])
        text = ' '.join(str(a) for a in args)
        return self._apply(text)


chalk = _Chalk()
