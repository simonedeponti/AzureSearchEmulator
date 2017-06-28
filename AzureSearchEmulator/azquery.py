import re
from pyparsing import (
    Word, White, alphanums, Keyword, Group, Forward,
    Suppress, OneOrMore, oneOf, ParseResults, ParseException
)


OP_REGEXPS = {
    ' !': re.compile(r'\s(?<!\\)(-)'),
    ' AND ': re.compile(r'\s?(?<!\\)(\+)\s?'),
    ' OR ': re.compile(r'\s?(?<!\\)(\|)\s?'),
}


UNSUPPORTED_PARAMS = (
    'minimumCoverage',
    'scoringParameter',
    'scoringProfile',
    'highlightPostTag',
    'highlightPreTag',
    'highlight'
)


def simple_to_lucene(query):
    """Turns an Azure Search simple query to a SOLR one.

    See https://docs.microsoft.com/en-us/rest/api/searchservice/
        simple-query-syntax-in-azure-search
    and https://lucene.apache.org/solr/guide/6_6/the-standard-query-parser.html
        #TheStandardQueryParser-BooleanOperatorsSupportedbytheStandardQueryParser

    Example::

        >>> simple_to_lucene("wifi+luxury")
        'wifi AND luxury'
        >>> simple_to_lucene("wifi | luxury")
        'wifi OR luxury'
        >>> simple_to_lucene("wifi -luxury")
        'wifi !luxury'
        >>> simple_to_lucene("luxury\\+hotel")
        'luxury\\\\+hotel'
        >>> simple_to_lucene("wi-fi")
        'wi-fi'
    """
    for replacement, regexp in OP_REGEXPS.items():
        query = regexp.sub(replacement, query)
    return query


class ODataQueryParser(object):

    def __init__(self):
        self._parser = self.parser()

    def parser(self):
        operatorOr = Forward()

        operatorWord = Group(
            Word(alphanums + '.')
        ).setResultsName('word')

        operatorQuotesContent = Forward()
        operatorQuotesContent << (
            (operatorWord + operatorQuotesContent) | operatorWord
        )

        operatorQuotes = Group(
            Suppress('"') + operatorQuotesContent + Suppress('"')
        ).setResultsName("quotes") | Group(
            Suppress("'") + operatorQuotesContent + Suppress("'")
        ).setResultsName("quotes") | operatorWord

        ws = White()

        operatorEq = Group(
            operatorQuotes + Suppress(ws) +
            Suppress(Keyword('eq', caseless=True)) +
            Suppress(ws) + operatorQuotes
        ).setResultsName('eq')
        operatorNeq = Group(
            operatorQuotes + Suppress(ws) +
            Suppress(Keyword('neq', caseless=True)) +
            Suppress(ws) + operatorQuotes
        ).setResultsName('neq')

        operatorLt = Group(
            operatorQuotes + Suppress(ws) +
            Suppress(Keyword('lt', caseless=True)) +
            Suppress(ws) + operatorQuotes
        ).setResultsName('lt')
        operatorLte = Group(
            operatorQuotes + Suppress(ws) +
            Suppress(Keyword('lte', caseless=True)) +
            Suppress(ws) + operatorQuotes
        ).setResultsName('lte')

        operatorGt = Group(
            operatorQuotes + Suppress(ws) +
            Suppress(Keyword('gt', caseless=True)) +
            Suppress(ws) + operatorQuotes
        ).setResultsName('gt')
        operatorGte = Group(
            operatorQuotes + Suppress(ws) +
            Suppress(Keyword('gte', caseless=True)) +
            Suppress(ws) + operatorQuotes
        ).setResultsName('gte')

        operatorCondition = (
            operatorEq | operatorNeq |
            operatorLt | operatorLte |
            operatorGt | operatorGte
        )

        operatorParenthesis = Group(
            Suppress("(") + OneOrMore(operatorOr) + Suppress(")")
        ).setResultsName("parenthesis") | operatorCondition

        operatorNot = Forward()
        operatorNot << (Group(
            Suppress(Keyword("not", caseless=True)) + operatorNot
        ).setResultsName("not") | operatorParenthesis)

        operatorAnd = Forward()
        operatorAnd << (Group(
            operatorNot + Suppress(Keyword("and", caseless=True)) + operatorAnd
        ).setResultsName("and") | Group(
            operatorNot + OneOrMore(~oneOf("and or") + operatorAnd)
        ).setResultsName("and") | operatorNot)

        operatorOr << (Group(
            operatorAnd + Suppress(Keyword("or", caseless=True)) + operatorOr
        ).setResultsName("or") | operatorAnd)

        return operatorOr.parseString

    def _transform(self, value):
        if not isinstance(value, ParseResults):
            return value
        name = value.getName()
        if name in ('and', 'or'):
            return '{} {} {}'.format(
                self._transform(value[0]),
                name.upper(),
                self._transform(value[1])
            )
        if name == 'not':
            return 'NOT {}'.format(
                self._transform(value[0])
            )
        if name == 'parenthesis':
            return '({})'.format(
                ''.join(self._transform(i) for i in value)
            )
        if name == 'gt':
            return '{}:{{{} TO *]'.format(
                self._transform(value[0]),
                self._transform(value[1])
            )
        if name == 'gte':
            return '{}:[{} TO *]'.format(
                self._transform(value[0]),
                self._transform(value[1])
            )
        if name == 'lt':
            return '{}:[* TO {}}}'.format(
                self._transform(value[0]),
                self._transform(value[1])
            )
        if name == 'lte':
            return '{}:[* TO {}]'.format(
                self._transform(value[0]),
                self._transform(value[1])
            )
        if name == 'neq':
            return 'NOT {}:{}'.format(
                self._transform(value[0]),
                self._transform(value[1])
            )
        if name == 'eq':
            return '{}:{}'.format(
                self._transform(value[0]),
                self._transform(value[1])
            )
        if name == 'quotes':
            return '"{}"'.format(
                ''.join(self._transform(i) for i in value)
            )
        return self._transform(value[0])

    def transform(self, value):
        result = self._parser(value)
        return ''.join(self._transform(i) for i in result)


class ODataParseFailure(Exception):

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __str__(self):
        return 'Parsing failed at line {} character {} near: {}'.format(
            self.wrapped.lineno,
            self.wrapped.col,
            self.wrapped.line
        )


def odata_to_lucene(query):
    parser = ODataQueryParser()
    try:
        return parser.transform(query)
    except ParseException as e:
        raise ODataParseFailure()


def parse(request, is_post=False):
    for unsupported in UNSUPPORTED_PARAMS:
        if unsupported in request:
            raise NotImplementedError(
                'Parameter {} not implemented'.format(unsupported)
            )
    query_type = request.get('queryType', 'simple')
    mode = request.get('searchMode', 'any')
    search_fields = request.get('searchFields')
    if search_fields is not None:
        search_fields = search_fields.split(',')
    query = request.get('search', '*')
    if query_type == 'simple':
        query = simple_to_lucene(query)
    skip = request.get('skip' if is_post else '$skip')
    limit = request.get('top' if is_post else '$top')
    count = request.get('count' if is_post else '$count', False)
    if not count or count.lower() == 'false':
        count = False
    else:
        count = True
    order_by = request.get('orderby' if is_post else '$orderby')
    if order_by is not None:
        order_by = order_by.split(',')
    select = request.get('select' if is_post else '$select')
    if select is not None:
        select = select.split(',')
    if is_post:
        facets = request.get('facets')
    else:
        facets = request.get('facet')
        if facets is not None:
            facets = facets.split(',')
    filter_query = request.get('filter' if is_post else '$filter')
    return {
        'mode': mode,
        'search_fields': search_fields,
        'query': query,
        'skip': skip,
        'limit': limit,
        'count': count,
        'order_by': order_by,
        'select': select,
        'facets': facets,
        'filter_query': odata_to_lucene(filter_query)
    }