import os
import json
from logging import getLogger
from urllib.parse import urljoin
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError


logger = getLogger(__name__)


SOLR_URL = os.environ.get('SOLR_URL', 'http://solr:8983/solr/')


class SolrError(Exception):
    """An exception occurred while talking to SOLR.

    He doesn't like what we asked him.
    """

    def __init__(self, reason, response):
        self.reason = reason
        self.response = response

    def __str__(self):
        return '{}: {}'.format(self.reason, self.response)


async def search(index, params):
    endpoint_url = urljoin(SOLR_URL, '{}/query'.format(index))
    logger.debug('Contacting endpoint {}'.format(endpoint_url))
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
        solr_query['offset'] = params['skip']
    if params['limit']:
        solr_query['limit'] = params['limit']
    if params['filter_query']:
        solr_query['filter'] = params['filter_query']
    if params['facets']:
        solr_query['facet'] = params['facets']
    async with ClientSession() as session:
        async with session.post(endpoint_url, json=solr_query) as resp:
            try:
                response_payload = await resp.text()
                resp.raise_for_status()
                return json.loads(response_payload)
            except ClientResponseError:
                logger.debug(await resp.text())
                raise SolrError(
                    "SOLR returned an error",
                    response_payload
                )
            except json.decoder.JSONDecodeError as e:
                raise SolrError(
                    "Cannot decode JSON from SOLR",
                    response_payload
                )
