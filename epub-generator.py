from sys import meta_path
from zipfile import ZipFile
from datetime import datetime
import xml.etree.ElementTree as ET

CONTENT_ROOT = "EPUB/"
TOC_PATH = "toc.xhtml"
PACKAGE_PATH = CONTENT_ROOT + "package.opf"
TOC_ID = "toc"
TOC_NAME = "Table of contents"


def xml_to_str(xml: ET.Element) -> str:
    return ET.tostring(xml, encoding="unicode", method="xml", xml_declaration=True)


class EPUB:
    def __init__(self, title: str, author: str, language: str):
        self.metadata: ET.Element = self._generate_pkg_metadata(title, author, language)
        self.manifest: ET.Element = ET.Element("manifest")
        self.spine: ET.Element = ET.Element("spine")
        self.toc = ET.Element("ol")

        # Add the table of contents to the spine and the manifest
        self._add_to_manifest_and_spine(TOC_ID, TOC_PATH, properties="nav")

        self.page_counts: int = 0
        self.contents: list[tuple[str, str]] = [
            ("mimetype", "application/epub+zip"),
            ("META-INF/container.xml", self._generate_container()),
        ]

    def _generate_container(self) -> str:
        container = ET.Element(
            "container",
            attrib={
                "xmlns": "urn:oasis:names:tc:opendocument:xmlns:container",
                "version": "1.0",
            },
        )
        rootfiles = ET.SubElement(container, "rootfiles")
        ET.SubElement(
            rootfiles,
            "rootfile",
            attrib={
                "full-path": PACKAGE_PATH,
                "media-type": "application/oebps-package+xml",
            },
        )
        return xml_to_str(container)

    def _current_page_id_and_path(self) -> tuple[str, str]:
        page_id = f"page{self.page_counts}"
        path = f"{page_id}.xhtml"
        return (page_id, path)

    def insert_content_marker(self, title: str):
        li = ET.Element("li")
        _, path = self._current_page_id_and_path()
        link = ET.SubElement(li, "a", href=path)
        link.text = title
        self.toc.append(li)

    def _add_to_manifest_and_spine(self, page_id: str, path: str, **kwargs):
        ET.SubElement(
            self.manifest,
            "item",
            attrib={
                "id": page_id,
                "href": path,
                "media-type": "application/xhtml+xml",
                **kwargs,
            },
        )

        ET.SubElement(self.spine, "itemref", idref=page_id)

    def add_page(self, content: str):
        self.page_counts += 1
        page_id, path = self._current_page_id_and_path()

        page_t = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml")
        head_t = ET.SubElement(page_t, "head")
        title_t = ET.SubElement(head_t, "title")
        title_t.text = page_id

        body_t = ET.SubElement(page_t, "body")
        paragraph_t = ET.SubElement(body_t, "p")
        paragraph_t.text = content

        self.contents.append((CONTENT_ROOT + path, xml_to_str(page_t)))
        self._add_to_manifest_and_spine(page_id, path)

    # Returns the path of the table of contents
    def _generate_toc(self) -> str:
        html = ET.Element(
            "html",
            attrib={
                "xmlns": "http://www.w3.org/1999/xhtml",
                "xmlns:epub": "http://www.idpf.org/2007/ops",
            },
        )
        head = ET.SubElement(html, "head")
        title = ET.SubElement(head, "title")
        title.text = TOC_NAME

        body = ET.SubElement(html, "body")
        h1 = ET.SubElement(body, "h1")
        h1.text = TOC_NAME

        nav = ET.SubElement(
            body, "nav", attrib={"epub:type": "toc", "id": TOC_ID, "role": "doc-toc"}
        )

        nav.append(self.toc)

        return xml_to_str(html)

    def _generate_pkg_opf(self) -> str:
        pkg = ET.Element(
            "package",
            attrib={
                "xmlns": "http://www.idpf.org/2007/opf",
                "version": "3.0",
                "xmlns:dc": "http://purl.org/dc/elements/1.1/",
                "xmlns:dcterms": "http://purl.org/dc/terms/",
                "unique-identifier": "pub-identifier",
            },
        )
        pkg.append(self.metadata)
        pkg.append(self.manifest)
        pkg.append(self.spine)

        return xml_to_str(pkg)

    def _generate_pkg_metadata(
        self, title: str, author: str, language: str
    ) -> ET.Element:
        metadata = ET.Element("metadata")

        identifier_t = ET.SubElement(metadata, "dc:identifier", id="pub-identifier")
        identifier_t.text = "generated-id"

        title_t = ET.SubElement(metadata, "dc:title")
        title_t.text = title

        author_t = ET.SubElement(metadata, "dc:creator")
        author_t.text = author

        lang_t = ET.SubElement(metadata, "dc:language")
        lang_t.text = language

        now = datetime.now().strftime("%Y-%m-%dT%H:%m:%SZ")

        date_t = ET.SubElement(metadata, "dc:date")
        date_t.text = now

        meta_t = ET.SubElement(metadata, "meta", property="dcterms:modified")
        meta_t.text = now

        return metadata

    def generate_epub(self, path: str):
        contents = self.contents + [
            (CONTENT_ROOT + TOC_PATH, self._generate_toc()),
            (PACKAGE_PATH, self._generate_pkg_opf()),
        ]

        with ZipFile(path, "w") as zip:
            for path, content in contents:
                zip.writestr(path, content)


if __name__ == "__main__":
    book = EPUB("Test", "author-test", "en")
    book.add_page("first-page" + 10000 * "a")
    book.insert_content_marker("First chapter")
    book.add_page("second-page")
    book.add_page("third-page")
    book.insert_content_marker("Second chapter")
    book.generate_epub("test.epub")
