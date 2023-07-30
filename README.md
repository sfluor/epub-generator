# epub-generator

Small library to generate epub files easily

## Usage:

```python
from epubgen import EPUB
import xml.etree.ElementTree as ET

book = EPUB("Test EPUB", "author-test", "en")
first_page = ET.Element("p")
first_page.text = "first-page" + 10000 * "hello "
book.add_page(first_page, toc_title="First chapter")

second_page = ET.Element("p")
second_page.text = "second-page" + 10000 * "good morning ! "
book.add_page(second_page, toc_title="Second chapter")
book.generate_epub("test.epub")
```
