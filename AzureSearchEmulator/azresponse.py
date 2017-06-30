from logging import getLogger
from urllib.parse import urlencode


logger = getLogger(__name__)


def format(request, result, parameters, is_post):
    final = {}
    logger.debug("Got response from SOLR: {}".format(result))
    result_count = result['response']['numFound']
    if parameters.get('count', False):
        final['@odata.count'] = result_count
    final['value'] = []
    for doc in result['response']['docs']:
        item = {
            '@search.score': doc['score']
        }
        item.update({
            k: v for k, v in doc.items()
            if k not in ('score', '_version_')
        })
        final['value'].append(item)
    if 'facets' in result:
        final_facets = {}
        final['@search.facets'] = final_facets
        for k, v in result['facets'].items():
            if k == 'count':
                continue
            final_facets[k[4:]] = [
                {'value': i['val'], 'count': i['count']}
                for i in v['buckets']
            ]
    if (parameters['skip'] + parameters['limit']) < result_count:
        if is_post:
            final['@odata.nextLink'] = '{}?{}'.format(
                request.url,
                urlencode(
                    (k, v) for k, v in request.query.items()
                    if k == 'api-version'
                )
            )
            next_params = parameters.copy()
            next_params['skip'] = parameters['skip'] + parameters['limit']
            final['@odata.nextPageParameters'] = next_params
        else:
            next_params = request.query.copy()
            next_params['$skip'] = str(
                parameters['skip'] + parameters['limit']
            )
            final['@odata.nextLink'] = '{}?{}'.format(
                request.url,
                urlencode(next_params.items())
            )
    return final
