def format(result, parameters):
    final = {}
    final['value'] = []
    for doc in result['response']['docs']:
        item = {
            '@search.score': doc['score']
        }
        item.update({
            k: v for k, v in doc.items()
            if k != 'score'
        })
    return final
