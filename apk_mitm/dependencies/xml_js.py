import re
import xml.sax
import xml.sax.handler
from typing import Any, Optional, TypedDict


class Element(TypedDict, total=False):
    declaration: dict
    instruction: str
    attributes: dict[str, Any]
    cdata: str
    doctype: str
    comment: str
    text: Any
    type: str
    name: str
    elements: list["Element"]


class _Xml2JsHandler(xml.sax.handler.ContentHandler, xml.sax.handler.LexicalHandler):
    def __init__(self):
        super().__init__()
        self._root: Element = {}
        self._current: Element = self._root
        self._stack: list[Element] = []
        self._locator = None
        self._in_cdata = False
        self._cdata_buffer = ""

    def setDocumentLocator(self, locator):
        self._locator = locator

    def startElement(self, name, attrs):
        element: Element = {}
        element["type"] = "element"
        element["name"] = name
        attributes = {}
        for attr_name in attrs.getNames():
            attributes[attr_name] = attrs.getValue(attr_name)
        if attributes:
            element["attributes"] = attributes
        if "elements" not in self._current:
            self._current["elements"] = []
        self._current["elements"].append(element)
        self._stack.append(self._current)
        self._current = element

    def endElement(self, name):
        self._current = self._stack.pop()

    def characters(self, content):
        if self._in_cdata:
            self._cdata_buffer += content
            return
        if not content.strip():
            return
        elements = self._current.get("elements")
        if elements and elements[-1].get("type") == "text":
            elements[-1]["text"] = str(elements[-1].get("text", "")) + content
            return
        text_element: Element = {}
        text_element["type"] = "text"
        text_element["text"] = content
        if "elements" not in self._current:
            self._current["elements"] = []
        self._current["elements"].append(text_element)

    def comment(self, content):
        comment_element: Element = {}
        comment_element["type"] = "comment"
        comment_element["comment"] = content
        if "elements" not in self._current:
            self._current["elements"] = []
        self._current["elements"].append(comment_element)

    def startCDATA(self):
        self._in_cdata = True
        self._cdata_buffer = ""

    def endCDATA(self):
        cdata_element: Element = {}
        cdata_element["type"] = "cdata"
        cdata_element["cdata"] = self._cdata_buffer
        if "elements" not in self._current:
            self._current["elements"] = []
        self._current["elements"].append(cdata_element)
        self._in_cdata = False

    def processingInstruction(self, target, data):
        if target.lower() == "xml":
            return
        instruction_element: Element = {}
        instruction_element["type"] = "instruction"
        instruction_element["name"] = target
        instruction_element["instruction"] = data
        if "elements" not in self._current:
            self._current["elements"] = []
        self._current["elements"].append(instruction_element)

    def startDTD(self, name, public_id, system_id):
        doctype_str = name
        if public_id:
            doctype_str += f' PUBLIC "{public_id}"'
            if system_id:
                doctype_str += f' "{system_id}"'
        elif system_id:
            doctype_str += f' SYSTEM "{system_id}"'
        doctype_element: Element = {}
        doctype_element["type"] = "doctype"
        doctype_element["doctype"] = doctype_str
        if "elements" not in self._current:
            self._current["elements"] = []
        self._current["elements"].append(doctype_element)

    def endDTD(self):
        pass

    def get_result(self):
        return self._root


def _parse_declaration(xml_string: str) -> Optional[dict]:
    match = re.match(r'<\?xml\s+(.*?)\?>', xml_string)
    if not match:
        return None
    body = match.group(1)
    attrs = {}
    attr_re = re.compile(r'([\w:-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')')
    for m in attr_re.finditer(body):
        attrs[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return {"attributes": attrs} if attrs else {}


def xml2js(xml_string: str, options: Optional[dict] = None) -> Element:
    result: Element = {}

    declaration = _parse_declaration(xml_string)
    if declaration is not None:
        result["declaration"] = declaration

    handler = _Xml2JsHandler()

    try:
        parser = xml.sax.make_parser()
        parser.setContentHandler(handler)
        parser.setFeature(xml.sax.handler.feature_external_ges, False)
        try:
            parser.setProperty(xml.sax.handler.property_lexical_handler, handler)
        except xml.sax.SAXNotSupportedException:
            pass
        parser.feed(xml_string)
        parser.close()
    except xml.sax.SAXParseException:
        pass

    parsed = handler.get_result()
    if "elements" in parsed:
        result["elements"] = parsed["elements"]

    return result


def _write_attributes(attributes: Optional[dict]) -> str:
    if not attributes:
        return ""
    parts = []
    for key, value in attributes.items():
        if value is None:
            continue
        val_str = str(value)
        val_str = val_str.replace('"', '&quot;')
        parts.append(f' {key}="{val_str}"')
    return "".join(parts)


def _write_text(text: Any) -> str:
    text_str = str(text)
    text_str = text_str.replace("&amp;", "&")
    text_str = text_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text_str


def _has_content(element: Element) -> bool:
    elements = element.get("elements")
    if elements and len(elements) > 0:
        for child in elements:
            child_type = child.get("type", "")
            if child_type in ("doctype", "comment", "element"):
                return True
            if child_type in ("text", "cdata", "instruction"):
                continue
            return True
    return False


def _write_indentation(spaces: str, depth: int, first_line: bool) -> str:
    return (("" if first_line else "\n") if spaces else "") + (spaces * depth)


def _write_element(element: Element, options: dict, depth: int) -> str:
    spaces = options.get("spaces", "")
    xml_parts = []
    name = element.get("name", "")
    xml_parts.append(f"<{name}")
    if element.get("attributes"):
        xml_parts.append(_write_attributes(element["attributes"]))
    child_elements = element.get("elements")
    with_closing_tag = bool(
        (child_elements and len(child_elements) > 0)
        or (element.get("attributes") and element["attributes"].get("xml:space") == "preserve")
    )
    if not with_closing_tag:
        with_closing_tag = options.get("fullTagEmptyElement", False)
    if with_closing_tag:
        xml_parts.append(">")
        if child_elements and len(child_elements) > 0:
            xml_parts.append(_write_elements(child_elements, options, depth + 1))
        if spaces and _has_content(element):
            xml_parts.append("\n" + (spaces * depth))
        xml_parts.append(f"</{name}>")
    else:
        xml_parts.append("/>")
    return "".join(xml_parts)


def _write_elements(elements: list[Element], options: dict, depth: int, first_line: bool = False) -> str:
    spaces = options.get("spaces", "")
    result = ""
    for element in elements:
        indent = _write_indentation(spaces, depth, first_line and not result)
        el_type = element.get("type", "")
        if el_type == "element":
            result += indent + _write_element(element, options, depth)
        elif el_type == "comment":
            result += indent + f'<!--{element.get("comment", "")}-->'
        elif el_type == "doctype":
            result += indent + f'<!DOCTYPE {element.get("doctype", "")}>'
        elif el_type == "cdata":
            cdata_val = element.get("cdata", "")
            cdata_val = cdata_val.replace("]]>", "]]]]><![CDATA[>")
            result += f"<![CDATA[{cdata_val}]]>"
        elif el_type == "text":
            result += _write_text(element.get("text", ""))
        elif el_type == "instruction":
            instr_name = element.get("name", "")
            instr_value = element.get("instruction", "")
            if instr_value:
                result += f"<?{instr_name} {instr_value}?>"
            else:
                result += f"<?{instr_name}?>"
    return result


def js2xml(obj: Element, options: Optional[dict] = None) -> str:
    if options is None:
        options = {}

    spaces = options.get("spaces", "")
    if isinstance(spaces, int):
        spaces = " " * spaces
    opts = {**options, "spaces": spaces}

    xml_parts = []

    declaration = obj.get("declaration")
    if declaration is not None:
        xml_parts.append("<?" + "xml" + _write_attributes(declaration.get("attributes")) + "?>")

    elements = obj.get("elements")
    if elements and len(elements) > 0:
        xml_parts.append(_write_elements(elements, opts, 0, not xml_parts))

    return "".join(xml_parts)
