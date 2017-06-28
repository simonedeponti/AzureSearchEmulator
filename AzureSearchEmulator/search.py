from aiohttp import web
from . import solr
from . import azquery
from . import azresponse


async def search(request):
    index = request.match_info['index']
    try:
        if request.method == "POST":
            request_data = await request.json()
            parameters = azquery.parse(request_data, True)
        else:
            parameters = azquery.parse(request.query, False)
        result = await solr.search(index, parameters)
        return web.json_response(azresponse.format(result))
    except NotImplementedError as e:
        return web.json_response(
            {
                'error': 'unsupported_param',
                'message': (
                    'The emulator does not currently support this parameter'
                ),
                'detail': str(e)
            },
            status=400
        )
    except azquery.ODataParseFailure as e:
        return web.json_response(
            {
                'error': 'odata_parse_fail',
                'message': (
                    'Error while parsing filter query'
                ),
                'detail': str(e)
            },
            status=400
        )
