from aiohttp import web
from .search import search


async def hello(request):
    return web.json_response({
        'id': 'AzureSearchEmulator',
        'message': "Hello, I'm a SOLR pretending to be Azure Search",
        'usage': "Any supplied API key will be accepted, really"
    })


def main():
    app = web.Application()
    app.router.add_get('/', hello)
    app.router.add_get('/indexes/{index}/docs', search)
    app.router.add_post('/indexes/{index}/docs', search)
    web.run_app(app)
