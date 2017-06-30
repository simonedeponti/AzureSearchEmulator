import asyncio
import json
import aiohttp
from logging import getLogger
from defusedxml.ElementTree import fromstring
from .solr import SOLR_URL


URL_TEMPLATES = {
    'status': '{solr_url}/admin/cores?action=STATUS',
    'create': (
        '{solr_url}/admin/cores?'
        'action=CREATE&name={index}&'
        'configSet=data_driven_schema_configs'
    ),
    'putschema': '{solr_url}/{index}/schema'
}

logger = getLogger(__name__)


async def get_cores_status(client):
    url = URL_TEMPLATES['status'].format(solr_url=SOLR_URL)
    cores = set()
    async with client.get(url) as resp:
        status = fromstring(await resp.text()).find("//lst[@name='status']")
        for core in status:
            cores.add(core.attrib['name'])
        return cores


async def create_core(client, name):
    url = URL_TEMPLATES['create'].format(solr_url=SOLR_URL, index=name)
    async with client.get(url) as resp:
        if resp.status == 200:
            return True
        else:
            return False


async def main(loop, indexes):
    async with aiohttp.ClientSession(loop=loop) as client:
        existing_cores = await get_cores_status(client)
        for index, definiton in indexes.items():
            if index not in existing_cores:
                logger.info("Creating core {}".format(index))
                created = await create_core(client, index)
                if not created:
                    logger.critical("Failed to create core {}".format(index))
                else:
                    logger.critical("Created core {}".format(index))



def recreate_indexes(stream):
    indexes = json.load(stream)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, indexes))