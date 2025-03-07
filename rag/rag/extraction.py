from pathlib import Path
from typing import Any

from docling.document_converter import DocumentConverter


class DocumentExtractor:
    def __init__(self):
        self.converter = DocumentConverter()

    def extract_from_file(self, file_path: str | Path) -> dict[str, Any]:
        result = self.converter.convert(str(file_path))
        return {
            "document": result.document,
            "markdown": result.document.export_to_markdown(),
            "metadata": {
                "title": result.document.title,
                "source": str(file_path)
            }
        }

    def extract_from_url(self, url: str) -> dict[str, Any]:
        result = self.converter.convert(url)
        return {
            "document": result.document,
            "markdown": result.document.export_to_markdown(),
            "metadata": {
                "title": result.document.title,
                "source": url
            }
        }

    def extract_from_sitemap(self, base_url: str) -> list[dict[str, Any]]:
        from rag.sitemap import get_sitemap_urls

        sitemap_urls = get_sitemap_urls(base_url)
        results = []

        for result in self.converter.convert_all(sitemap_urls):
            if result.document:
                results.append({
                    "document": result.document,
                    "markdown": result.document.export_to_markdown(),
                    "metadata": {
                        "title": result.document.title,
                        "source": result.document.meta.get("source", "Unknown")
                    }
                })

        return results

    def extract_from_text(self, text: str, source: str | None = None) -> dict[str, Any]:
        return {
            "document": text,
            "markdown": text,
            "metadata": {
                "title": source or "Text Input",
                "source": source or "Text Input"
            }
        }
