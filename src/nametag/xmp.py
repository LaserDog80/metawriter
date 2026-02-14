"""XMP build/parse helpers for Nametag.

Standalone reimplementation of XMP utilities — no imports from metawriter.
"""

import re

from defusedxml import ElementTree as ET

# XMP template for embedding key-value metadata.
_XMP_TEMPLATE = (
    '<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
    '<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
    '<rdf:Description rdf:about=""\n'
    '  xmlns:mw="http://metawriter.dev/ns/1.0/">\n'
    "{entries}"
    "</rdf:Description>\n"
    "</rdf:RDF>\n"
    "</x:xmpmeta>\n"
    '<?xpacket end="w"?>'
)

_MW_NS = "http://metawriter.dev/ns/1.0/"


def _escape_xml(text: str) -> str:
    """Escape special XML characters in text."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _sanitize_xml_name(name: str) -> str:
    """Sanitize a string into a valid XML element name."""
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    if sanitized and not re.match(r"[a-zA-Z_]", sanitized[0]):
        sanitized = f"_{sanitized}"
    return sanitized or "_"


def build_xmp(entries: dict[str, str]) -> bytes:
    """Build an XMP packet from a dict of key-value pairs."""
    lines = []
    for key, value in entries.items():
        safe_key = _sanitize_xml_name(key)
        lines.append(f"  <mw:{safe_key}>{_escape_xml(value)}</mw:{safe_key}>")
    body = "\n".join(lines) + "\n" if lines else ""
    return _XMP_TEMPLATE.format(entries=body).encode("utf-8")


def parse_xmp(xmp_bytes: bytes) -> dict[str, str]:
    """Parse an XMP packet and return MetaWriter (mw:*) entries."""
    result: dict[str, str] = {}
    try:
        root = ET.fromstring(xmp_bytes)
    except Exception:
        return result

    for elem in root.iter():
        tag = elem.tag
        if "{" in tag:
            ns, local = tag.split("}", 1)
            ns = ns.lstrip("{")
            if ns == _MW_NS and elem.text:
                result[local] = elem.text
    return result
