"""JPEG metadata handler using XMP sidecar blocks and EXIF via piexif."""

from pathlib import Path

import piexif
from defusedxml import ElementTree as ET
from PIL import Image

from .base import BaseFormatHandler

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
    """Sanitize a string into a valid XML element name.

    XML names must start with a letter or underscore. Subsequent characters
    may include letters, digits, hyphens, underscores, and periods.
    """
    import re

    # Replace invalid characters with underscores
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    # Ensure it starts with a letter or underscore
    if sanitized and not re.match(r"[a-zA-Z_]", sanitized[0]):
        sanitized = f"_{sanitized}"
    return sanitized or "_"


def _build_xmp(entries: dict[str, str]) -> bytes:
    """Build an XMP packet from a dict of key-value pairs."""
    lines = []
    for key, value in entries.items():
        safe_key = _sanitize_xml_name(key)
        lines.append(f"  <mw:{safe_key}>{_escape_xml(value)}</mw:{safe_key}>")
    body = "\n".join(lines) + "\n" if lines else ""
    return _XMP_TEMPLATE.format(entries=body).encode("utf-8")


def _parse_xmp(xmp_bytes: bytes) -> dict[str, str]:
    """Parse an XMP packet and return MetaWriter (mw:*) entries."""
    result: dict[str, str] = {}
    try:
        root = ET.fromstring(xmp_bytes)
    except Exception:
        return result

    # Walk all elements looking for mw namespace entries
    for elem in root.iter():
        tag = elem.tag
        if "{" in tag:
            ns, local = tag.split("}", 1)
            ns = ns.lstrip("{")
            if ns == _MW_NS and elem.text:
                result[local] = elem.text
    return result


class JpegHandler(BaseFormatHandler):
    """Read and write JPEG metadata via XMP blocks and EXIF."""

    def read_metadata(self, path: Path) -> dict[str, str]:
        """Read EXIF and XMP metadata from a JPEG file.

        Args:
            path: Path to the JPEG file.

        Returns:
            Dict of metadata key-value pairs.
        """
        result: dict[str, str] = {}

        with Image.open(path) as img:
            # Read EXIF data via piexif
            exif_data = img.info.get("exif", b"")
            if exif_data:
                try:
                    exif_dict = piexif.load(exif_data)
                    for ifd_name in exif_dict:
                        if ifd_name == "thumbnail":
                            continue
                        ifd = exif_dict[ifd_name]
                        if isinstance(ifd, dict):
                            for tag, val in ifd.items():
                                tag_name = piexif.TAGS.get(ifd_name, {}).get(
                                    tag, {}
                                ).get("name", str(tag))
                                if isinstance(val, bytes):
                                    try:
                                        val = val.decode("utf-8", errors="replace")
                                    except Exception:
                                        val = repr(val)
                                result[f"exif:{tag_name}"] = str(val)
                except Exception:
                    pass

            # Read XMP data
            xmp_data = img.info.get("xmp", b"")
            if isinstance(xmp_data, bytes) and xmp_data:
                result.update(_parse_xmp(xmp_data))

        return result

    def write_metadata(
        self,
        source_path: Path,
        output_path: Path,
        metadata: dict[str, str],
    ) -> None:
        """Copy a JPEG file with metadata appended via XMP.

        EXIF data from the source is carried forward. New MetaWriter entries
        are stored in an XMP block.

        Args:
            source_path: Original JPEG file.
            output_path: Destination path for new copy.
            metadata: New key-value entries to append.
        """
        with Image.open(source_path) as img:
            # Preserve existing EXIF
            exif_bytes = img.info.get("exif", b"")

            # Read existing XMP entries and merge with new
            existing_xmp = img.info.get("xmp", b"")
            merged: dict[str, str] = {}
            if isinstance(existing_xmp, bytes) and existing_xmp:
                merged.update(_parse_xmp(existing_xmp))
            merged.update(metadata)

            xmp_packet = _build_xmp(merged)

            save_kwargs: dict = {"format": "JPEG"}
            if exif_bytes:
                save_kwargs["exif"] = exif_bytes
            save_kwargs["xmp"] = xmp_packet

            img.save(str(output_path), **save_kwargs)
