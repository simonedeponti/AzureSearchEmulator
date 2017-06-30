# Development emulator for Azure Search

This is a small wrapper over SOLR that exposes the [Azure Search REST API]() for development purposes.

**It is absolutely not intended to ever run in replacement of Azure Search**.

To use it you must first download and install [docker](https://www.docker.com/).

The container expects to be linked to a SOLR container named `solr`,
listening on a default port (`8983`), with an already created core with indexed data in it.

The SOLR endpoint can be configured via the `SOLR_URL` environment variable:
if SOLR is reachable from the container at `mysolr.example.com`,
then pass the environment variable `SOLR_URL=http://mysolr.example.com:8983/`.

For other details, see the surce code or the included `docker-compose.yml`.

This has been tested with SOLR 6.

## Unsupported features

These are the main features currently unsupported:

 - index creation
 - indexing content
 - suggestions
 - document lookup
 - document count with `$count` endpoint

The search feature does not support the following sub-features (and will return 400 Bad Request):

 - `minimumCoverage`, `scoringParameter`, `scoringProfile`, `highlight*`
 - geo functions in OData filter queries
 - geo sorting
 - `any()` / `all` in OData filter query
 - ascending sorts on facet count or descending on facet value (`-count` and `-value`)
 - `values` option in facets
 - `interval` option in facets
 - `timeoffset` option in facets

Error messages do not comply with the standard Azure Search, they are custom.

## Tools

