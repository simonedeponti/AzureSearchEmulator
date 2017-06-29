# Development emulator for Azure Search

To be used with [docker](https://www.docker.com/) only.



## Unsupported features

These are the features currently unsupported:

 - index creation
 - indexing content
 - `minimumCoverage`, `scoringParameter`, `scoringProfile`, `highlight*`
 - geo functions in OData filter queries
 - geo sorting
 - `any()` / `all` in OData filter query
 - ascending sorts on facet count or descending on facet value (`-count` and `-value`)
 - `values` option in facets
 - `interval` option in facets
 - `timeoffset` option in facets