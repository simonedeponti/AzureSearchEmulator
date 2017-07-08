from logging import getLogger
from urllib.parse import urlencode


logger = getLogger(__name__)


def format(request, result, raw_parameters, is_post):
    final = {}
    logger.debug("Got response from SOLR: {}".format(result))
    if is_post:
        count = raw_parameters.get('count', False)
        if isinstance(count, str):
            count = count.lower() == 'true'
        skip = raw_parameters.get('skip', 0)
        limit = raw_parameters.get('top', 50)
    else:
        count = raw_parameters.get('$count', 'false').lower() == 'true'
        skip = int(raw_parameters.get('$skip', '0'))
        limit = int(raw_parameters.get('$top', '50'))
    result_count = result['response']['numFound']
    if count:
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
    if (skip + limit) < result_count:
        if is_post:
            final['@odata.nextLink'] = str(request.url)
            next_params = raw_parameters.copy()
            next_params['skip'] = skip + limit
            final['@odata.nextPageParameters'] = next_params
        else:
            next_params = request.query.copy()
            next_params['$skip'] = str(skip + limit)
            final['@odata.nextLink'] = str(request.url.with_query(
                list(next_params.items())
            ))
    return final
