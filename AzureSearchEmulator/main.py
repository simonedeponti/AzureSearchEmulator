import os
import sys
from logging import basicConfig, getLogger
from aiohttp import web
from .search import search
from .index import Indexer
from .tools import recreate_indexes


LOGFMT = '[%(asctime)s %(levelname)s] %(name)s %(message)s'
INDEXES_FILE = '/srv/azuresearch/indexes.json'
logger = getLogger(__name__)


async def hello(request):
    return web.json_response({
        'id': 'AzureSearchEmulator',
        'message': "Hello, I'm a SOLR pretending to be Azure Search",
        'usage': "Any supplied API key will be accepted, really"
    })


def main():
    debug_mode = (
        os.environ.get('AZEMULATOR_DEBUG', '').lower() in ('true', 'on', '1')
    )
    if debug_mode:
        basicConfig(level='DEBUG', format=LOGFMT, stream=sys.stdout)
    else:
        basicConfig(level='INFO', format=LOGFMT, stream=sys.stdout)
    if os.path.isfile(INDEXES_FILE):
        logger.info('Checking indexes to re-create')
        with open(INDEXES_FILE, 'r', encoding='utf-8') as stream:
            indexes_primary = recreate_indexes(stream)
    indexer = Indexer(indexes_primary)
    app = web.Application(debug=debug_mode)
    app.router.add_get('/', hello)
    app.router.add_get('/indexes/{index}/docs', search)
    app.router.add_post('/indexes/{index}/docs', search)
    app.router.add_get('/indexes/{index}/docs/search', search)
    app.router.add_post('/indexes/{index}/docs/search', search)
    app.router.add_post('/indexes/{index}/docs/index', indexer.index)
    web.run_app(app)
