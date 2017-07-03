import asyncio
import json
import aiohttp
import time
from logging import getLogger
from defusedxml.ElementTree import fromstring
from aiohttp.client_exceptions import ClientConnectorError
from .solr import SOLR_URL


URL_TEMPLATES = {
    'status': '{solr_url}/admin/cores?action=STATUS',
    'create': (
        '{solr_url}/admin/cores?'
        'action=CREATE&name={index}&'
        'instanceDir=%2Fopt%2Fsolr%2Fserver%2Fsolr%2Fmycores%2F{index}&'
        'configSet=data_driven_schema_configs'
    ),
    'putschema': '{solr_url}/{index}/schema'
}

TYPES = {
    'Edm.String': lambda tags: {
        'type': 'text_general' if 'searchable' in tags else 'string',
        'multiValued': False
    },
    'Collection(Edm.String)': lambda tags: {
        'type': 'text_general' if 'searchable' in tags else 'string',
        'multiValued': True
    },
    'Edm.Int32': lambda tags: {
        'type': 'int',
        'multiValued': False
    },
    'Edm.Int64': lambda tags: {
        'type': 'long',
        'multiValued': False
    },
    'Edm.Boolean': lambda tags: {
        'type': 'boolean',
        'multiValued': False
    },
    'Edm.Double': lambda tags: {
        'type': 'double',
        'multiValued': False
    },
    'Edm.DateTimeOffset': lambda tags: {
        'type': 'date',
        'multiValued': False
    }
}

MAX_RETRIES = 10

logger = getLogger(__name__)


async def get_cores_status(client):
    url = URL_TEMPLATES['status'].format(solr_url=SOLR_URL.rstrip('/'))
    cores = set()
    logger.debug("Calling endpoint {}".format(url))
    async with client.get(url) as resp:
        text_resp = await resp.text()
        logger.debug("Got {}".format(text_resp))
        status = fromstring(text_resp).find("./lst[@name='status']")
        if not status:
            status = []
        for core in status:
            cores.add(core.attrib['name'])
        return cores


async def create_core(client, name):
    url = URL_TEMPLATES['create'].format(
        solr_url=SOLR_URL.rstrip('/'),
        index=name
    )
    logger.debug('Calling GET {}'.format(url))
    async with client.get(url) as resp:
        logger.debug(await resp.text())
        return resp.status == 200


def schema_to_solrops(schema):
    ops = {
        'add-field': []
    }
    for field_id, field_def in schema.items():
        if field_def.get('is_primary', False):
            if field_id != 'id':
                ops['add-copy-field'] = {
                    'source': field_id,
                    'dest': 'id'
                }
            else:
                continue
        rule = {
            'name': field_id,
            'indexed': True
        }
        rule.update(
            TYPES[field_def['type']](
                field_def.get('tags', [])
            )
        )
        if 'retrievable' in field_def['tags']:
            rule['stored'] = True
        ops['add-field'].append(rule)
    return ops


async def create_schema(client, index, operations):
    url = URL_TEMPLATES['putschema'].format(
        solr_url=SOLR_URL.rstrip('/'),
        index=index
    )
    logger.debug('Calling POST {}'.format(url))
    async with client.post(url, json=operations) as resp:
        logger.debug(await resp.text())
        return resp.status == 200


async def main(loop, indexes):
    async with aiohttp.ClientSession(loop=loop) as client:
        tries = 0
        while tries < MAX_RETRIES:
            try:
                async with client.get(SOLR_URL) as resp:
                    await resp.text()
            except ClientConnectorError:
                logger.info("Cannot contact {}, waiting".format(SOLR_URL))
                time.sleep(1)
                tries += 1
            else:
                time.sleep(10)
                tries = MAX_RETRIES
        existing_cores = await get_cores_status(client)
        logger.debug("Existing cores: {}".format(existing_cores))
        for index, definition in indexes.items():
            if index not in existing_cores:
                logger.info("Creating core {}".format(index))
                created = await create_core(client, index)
                if not created:
                    logger.critical("Failed to create core {}".format(index))
                else:
                    logger.critical("Created core {}".format(index))
                    operations = schema_to_solrops(definition['schema'])
                    created = await create_schema(client, index, operations)
                    if created:
                        logger.info("Updated schema for {}".format(index))
                    else:
                        logger.critical(
                            "Failed to update schema for {}".format(index)
                        )


def recreate_indexes(stream):
    indexes = json.load(stream)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, indexes))
    return {
        index_id: [
            k for k, v in index_def['schema'].items()
            if v.get('is_primary', False)
        ][0]
        for index_id, index_def in indexes.items()
    }
