import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import requests


def get_sitemap_urls(base_url: str, sitemap_filename: str = "sitemap.xml") -> list[str]:
    try:
        sitemap_url = urljoin(base_url, sitemap_filename)
        response = requests.get(sitemap_url, timeout=10)

        if response.status_code == 404:
            return [base_url.rstrip("/")]

        response.raise_for_status()
        root = ET.fromstring(response.content)
        namespaces = (
            {"ns": root.tag.split("}")[0].strip("{")} if "}" in root.tag else ""
        )

        if namespaces:
            urls = [elem.text for elem in root.findall(".//ns:loc", namespaces)]
        else:
            urls = [elem.text for elem in root.findall(".//loc")]

        return urls

    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch sitemap: {e!s}")
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse sitemap XML: {e!s}")
    except Exception as e:
        raise ValueError(f"Unexpected error processing sitemap: {e!s}")
