import uuid
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiosparql.test_utils import TestSPARQLClient

import mupushservice.main
from mupushservice import delta, handler

__all__ = ['UnitTestCase', 'unittest_run_loop']


class Application(mupushservice.main.Application):
    @property
    def sparql(self):
        if not hasattr(self, '_sparql'):
            self._sparql = TestSPARQLClient(self)
        return self._sparql

    @property
    def muclresources(self):
        raise RuntimeError("Can not do Docker queries during unit test")


class UnitTestCase(AioHTTPTestCase):
    heartbeat = 5

    async def get_application(self):
        app = Application()
        app.router.add_get("/", handler.ws_handler)
        app.router.add_post("/update", delta.update)
        app.heartbeat = self.heartbeat
        return app

    def uuid4(self):
        return str(uuid.uuid4()).replace("-", "").upper()
