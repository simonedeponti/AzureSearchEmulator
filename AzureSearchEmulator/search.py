import traceback
from aiohttp import web
from . import solr
from . import azquery
from . import azresponse


async def search(request):
    index = request.match_info['index']
    try:
        if request.method == "POST":
            request_data = await request.json()
            is_post = True
            raw_parameters = request_data
        else:
            is_post = False
            raw_parameters = request.query
        parameters = azquery.parse(raw_parameters, is_post)
        result = await solr.search(index, parameters)
        return web.json_response(
            azresponse.format(
                request,
                result,
                raw_parameters,
                is_post
            )
        )
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
    except ValueError as e:
        return web.json_response(
            {
                'error': 'parse_fail',
                'message': (
                    'Error while parsing query'
                ),
                'detail': str(e),
                'traceback': traceback.format_exc()
            },
            status=400
        )
    except Exception as e:
        return web.json_response(
            {
                'error': 'failure',
                'message': (
                    'Error while searching'
                ),
                'detail': str(e),
                'traceback': traceback.format_exc()
            },
            status=500
        )
