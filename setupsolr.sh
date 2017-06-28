#!/bin/bash

docker-compose up -d solr
docker-compose exec solr bin/solr create_core -c gettingstarted
docker-compose exec solr bin/post -c gettingstarted example/exampledocs/books.json