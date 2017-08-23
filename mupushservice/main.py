import logging
from aiohttp import web
from aiosparql.client import SPARQLClient
from os import environ as ENV

from mupushservice import delta, handler, muclresources


logger = logging.getLogger(__name__)


if ENV.get("ENV", "prod").startswith("dev"):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


class Application(web.Application):
    heartbeat = 30
    # NOTE: override default timeout for SPARQL queries
    sparql_timeout = 60

    @property
    def sparql(self):
        """
        The SPARQL client
        """
        if not hasattr(self, '_sparql'):
            self._sparql = SPARQLClient(prefixes=self.prefixes, loop=self.loop,
                                        read_timeout=self.sparql_timeout)
        return self._sparql

    @property
    def muclresources(self):
        if not hasattr(self, '_muclresources'):
            self._muclresources = muclresources.MuClResourcesClient(
                loop=self.loop)
        return self._muclresources

    @property
    def prefixes(self):
        if not hasattr(self, '_prefixes'):
            with open("/config/repository.lisp") as fh:
                self._prefixes = \
                    muclresources.parse_repository(fh)
        return self._prefixes

    def _generate_resources(self, resources):
        for class_, name in resources.items():
            prefix, label = class_.split(':', 2)
            yield (self.prefixes[prefix] + label, name)

    @property
    def resources(self):
        if not hasattr(self, '_resources'):
            with open("/config/domain.lisp") as fh:
                resources = muclresources.parse_domain(fh)
            self._resources = dict(self._generate_resources(resources))
        return self._resources

    @property
    def queues(self):
        if not hasattr(self, '_queues'):
            self._queues = []
        return self._queues

    def filter_queues(self, resource):
        return filter(lambda x: resource in x.watch_list, self.queues)

    async def get_resource(self, subject):
        result = await self.sparql.query(
            """
            SELECT *
            FROM {{graph}}
            WHERE {
                {{}} mu:uuid ?uuid ;
                  a ?class .
            }
            """, subject)
        if not result['results']['bindings'] or \
                not result['results']['bindings'][0]:
            raise KeyError("Can not find resource for subject %s" % subject)
        return (
            result['results']['bindings'][0]['class']['value'],
            result['results']['bindings'][0]['uuid']['value'],
        )


async def cleanup_sessions(app):
    app.sparql.close()
    app.muclresources.close()


app = Application()
app.on_cleanup.append(cleanup_sessions)
app.router.add_get("/", handler.ws_handler)
app.router.add_post("/update", delta.update)
