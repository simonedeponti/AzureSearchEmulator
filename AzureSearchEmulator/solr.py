import os
from urllib.parse import urljoin
from aiohttp import ClientSession


SOLR_URL = os.environ.get('SOLR_URL', 'http://solr:8983/solr/')


async def search(index, params):
    endpoint_url = urljoin(SOLR_URL, index, 'query')
    with ClientSession() as session:
        with session.post(endpoint_url, json=params) as resp:
            resp.json()
