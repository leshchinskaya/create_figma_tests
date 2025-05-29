import requests
import re
from logger_setup import setup_logger

logger = setup_logger(__name__)

class FigmaClient:
    BASE_URL = "https://api.figma.com/v1"

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({"X-Figma-Token": token})

    def get(self, endpoint: str, **params) -> dict:
        try:
            response = self.session.get(f"{self.BASE_URL}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Figma API request failed: {e}")
            raise

    def get_file_tree(self, file_key: str) -> dict:
        return self.get(f"files/{file_key}")

    def get_nodes(self, file_key: str, ids: str) -> dict:
        return self.get(f"files/{file_key}/nodes", ids=ids)

    def get_image_url(self, file_key: str, node_id: str, scale: float | int) -> str | None:
        try:
            data = self.get(f"images/{file_key}", ids=node_id, format="png", scale=scale)
            return data["images"].get(node_id)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Image not found for node {node_id} in file {file_key}: {e}")
                return None
            raise
        except KeyError: # If 'images' key is missing
            logger.warning(f"\'images\' key not found in response for node {node_id} in file {file_key}")
            return None


    def download_image_data(self, image_url: str) -> bytes:
        try:
            # Using a new requests.get as image_url might be S3 or other external URL
            response = requests.get(image_url)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            raise

def parse_file_key(url: str) -> str:
    """Извлекает FILE_KEY из URL Figma."""
    m = re.search(r"/(?:file|design|proto)/([^/]+)/", url)
    if m: return m.group(1)
    q = re.search(r"[?&]file-id=([^&]+)", url)
    if q: return q.group(1)
    raise ValueError("Не удалось извлечь FILE_KEY из URL Figma")

def sanitize(name: str) -> str:
    """Оставляет в имени только буквы, цифры и подчёркивания."""
    return re.sub(r'[^0-9A-Za-z_]+', '_', name) 