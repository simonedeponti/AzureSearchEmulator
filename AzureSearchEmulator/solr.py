import os
from urllib.parse import urljoin
from aiohttp import ClientSession


SOLR_URL = os.environ.get('SOLR_URL', 'http://solr:8983/solr/')


async def search(index, params):
    endpoint_url = urljoin(SOLR_URL, index, 'query')
    solr_query = {
        'query': params['query'],
        'params': {
            'q.op': 'AND' if params['mode'] == 'all' else 'OR'
        }
    }
    if params['fields']:
        solr_query['params']['df'] = (
            params['fields'][0]
            if isinstance(params, list) else params['fields']
        )
    if params['select']:
        solr_query['fields'] = [f for f in params['select']]
        solr_query['fields'].append('score')
    else:
        solr_query['fields'] = ['*', 'score']
    if params['order_by']:
        solr_query['sort'] = params['order_by']
    if params['skip']:
        solr_query['offset'] = int(params['skip'])
    if params['limit']:
        solr_query['limit'] = int(params['limit'])
    if params['filter_query']:
        solr_query['filter'] = params['filter_query']
    if params['facets']:
        solr_query['facet'] = params['facets']
    with ClientSession() as session:
        with session.post(endpoint_url, json=solr_query) as resp:
            return resp.json()
