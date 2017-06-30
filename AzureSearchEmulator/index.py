from aiohttp import web
from . import solr


def strip_action(item):
    return {
        k: v for k, v in item.items()
        if k != '@search.action'
    }


class Indexer(object):

    def __init__(self, indexes_primary):
        self.indexes_primary = indexes_primary

    async def index(self, request):
        index = request.match_info['index']
        index_primary = self.indexes_primary[index]
        payload = await request.json()
        inserts = [
            strip_action(i) for i in payload['value']
            if i['@search.action'] in ('upload', 'merge', 'mergeOrUpload')
        ]
        deletes = [
            i[index_primary] for i in payload['value']
            if i['@search.action'] in 'delete'
        ]
        succeeded, failed = await solr.index(
            index,
            inserts,
            deletes,
            index_primary
        )
        return web.json_response(
            {
                'value': [
                    {
                        'key': i,
                        'status': True,
                        'errorMessage': None
                    }
                    for i in succeeded
                ] + [
                    {
                        'key': i,
                        'status': False,
                        'errorMessage': "An error occurred during indexing"
                    }
                    for i in failed
                ]
            },
            status=(200 if len(failed) == 0 else 207)
        )
