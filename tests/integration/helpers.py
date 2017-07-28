import asyncio
import socket
import uuid
from aiohttp.test_utils import (
    AioHTTPTestCase, TestClient, TestServer, setup_test_loop,
    unittest_run_loop)
from aiosparql.client import SPARQLClient
from aiosparql.syntax import escape_any, IRI, Triples
from copy import copy
from yarl import URL

import mupushservice.main

__all__ = ['IntegrationTestCase', 'unittest_run_loop']


_sentinel = object()


# NOTE: temporary fix: ensure a child watcher is set before running test
def setup_test_loop(loop_factory=asyncio.new_event_loop):  # noqa
    """Create and return an asyncio.BaseEventLoop
    instance.

    The caller should also call teardown_test_loop,
    once they are done with the loop.
    """
    loop = loop_factory()
    asyncio.set_event_loop(None)
    policy = asyncio.get_event_loop_policy()
    watcher = asyncio.SafeChildWatcher()
    watcher.attach_loop(loop)
    policy.set_child_watcher(watcher)
    return loop


class FixedPortTestServer(TestServer):
    @asyncio.coroutine
    def start_server(self, loop=None, **kwargs):
        if self.server:
            return
        self._loop = loop
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("0.0.0.0", 80))
        self.port = self._socket.getsockname()[1]
        self._ssl = None
        self.scheme = 'http'
        self._root = URL('{}://{}:{}'.format(self.scheme,
                                             self.host,
                                             self.port))

        handler = yield from self._make_factory(**kwargs)
        self.server = yield from self._loop.create_server(
            handler, ssl=self._ssl, sock=self._socket)

    # NOTE: temporary fix: ensure that the event loop is set in the app before
    #       firing on_startup
    @asyncio.coroutine
    def _make_factory(self, **kwargs):
        self.app._set_loop(self._loop)  # here
        yield from self.app.startup()
        self.handler = self.app.make_handler(loop=self._loop, **kwargs)
        return self.handler


class IntegrationTestCase(AioHTTPTestCase):
    sparql_timeout = 5
    heartbeat = 5

    async def get_application(self):
        app = copy(mupushservice.main.app)
        app.sparql_timeout = self.sparql_timeout
        app.heartbeat = self.heartbeat
        return app

    def uuid4(self):
        return str(uuid.uuid4()).replace("-", "").upper()

    def resource(self, type_, id):
        return (
            IRI("http://mu.semte.ch/test/resources/") + "%s/%s" % (type_, id)
        )

    async def triple_exists(self, s=None, p=None, o=None):
        s = escape_any(s) if s is not None else "?s"
        p = escape_any(p) if p is not None else "?p"
        o = escape_any(o) if o is not None else "?o"
        result = await self.app.sparql.query(
            "ASK FROM {{graph}} WHERE { {{}} {{}} {{}} }", s, p, o)
        return result['boolean']

    async def prepare_triples(self, triples):
        await self.db.update(
            "INSERT DATA { GRAPH {{graph}} { {{}} } }", Triples(triples))

    async def insert_triples(self, triples):
        await self.app.sparql.update(
            "INSERT DATA { GRAPH {{graph}} { {{}} } }", Triples(triples))

    async def prepare_node(self, node):
        await self.prepare_triples([node])

    async def insert_node(self, node):
        await self.insert_triples([node])

    async def describe(self, subject):
        return await self.app.sparql.query("DESCRIBE {{}} FROM {{graph}}",
                                           subject)

    async def delete_node(self, subject):
        return await self.app.sparql.update(
            """
            WITH {{graph}}
            DELETE {
                {{subject}} ?p ?o
            }
            WHERE {
                {{subject}} ?p ?o
            }
            """, subject=subject)

    async def prepare_database(self):
        await self.db.update("CLEAR GRAPH {{graph}}")

    def setUp(self):
        self.loop = setup_test_loop()

        self.db = SPARQLClient(endpoint="http://database:8890/sparql",
                               loop=self.loop,
                               read_timeout=self.sparql_timeout)
        self.loop.run_until_complete(self.prepare_database())

        self.app = self.loop.run_until_complete(self.get_application())

        self.server = FixedPortTestServer(self.app)
        self.client = self.loop.run_until_complete(
            self._get_client(self.server))

        self.loop.run_until_complete(self.client.start_server())

    def tearDown(self):
        self.loop.run_until_complete(self.db.close())
        super().tearDown()

    # NOTE: temporary fix, will be fixed with the next aiohttp release
    @asyncio.coroutine
    def _get_client(self, app):
        """Return a TestClient instance."""
        return TestClient(app, loop=self.loop)

    async def assertNode(self, subject, values):
        result = await self.describe(subject)
        self.assertTrue(result and result[subject])
        for p, o in values.items():
            found_values = [x['value'] for x in result[subject][p]]
            self.assertEqual(
                len(found_values), 1,
                "multiple predicates {} in node's subject {}: {!r}".format(
                    p, subject, found_values))
            self.assertEqual(
                found_values[0], o,
                "predicate {} in node {} has value {}, expected {}".format(
                    p, subject, found_values[0], o))

    async def assertExists(self, s=None, p=None, o=None):
        self.assertTrue(await self.triple_exists(s, p, o))

    async def assertNotExists(self, s=None, p=None, o=None):
        self.assertFalse(await self.triple_exists(s, p, o))
