import requests
from django.conf import settings
from requests.exceptions import HTTPError

class BrasmolClient:
    def __init__(self):
        self.base = settings.BRASMOL_BASE_URL
        self.headers = {
            "apikey": settings.BRASMOL_API_KEY,
            "Content-Type": "application/json",
        }

    def _get(self, endpoint, params=None):
        url = f"{self.base}{endpoint}"
        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def fetch_clients(self):
        # Exemplo: rota GET /getClientes
        return self._get("/getClientes")

    def fetch_products(self):
        # Exemplo: rota GET /getProdutos
        return self._get("/getProdutos")
