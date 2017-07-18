import aiohttp

from tests.unit.helpers import UnitTestCase, unittest_run_loop


class PingPongTestCase(UnitTestCase):
    heartbeat = 0.5

    @unittest_run_loop
    async def test_ping_pong_success(self):
        ws = await self.client.ws_connect('/', autoping=False)
        ws.ping()
        msg1 = await ws.receive()
        self.assertEqual(msg1.type, aiohttp.WSMsgType.PONG)
        msg2 = await ws.receive()
        self.assertEqual(msg2.type, aiohttp.WSMsgType.PING)
        ws.pong(msg2.data)

    @unittest_run_loop
    async def test_ping_pong_failure(self):
        ws = await self.client.ws_connect('/', autoping=False)
        msg1 = await ws.receive()
        self.assertEqual(msg1.type, aiohttp.WSMsgType.PING)
        ws.pong(msg1.data)
        msg2 = await ws.receive()
        self.assertEqual(msg2.type, aiohttp.WSMsgType.PING)
        msg3 = await ws.receive()
        self.assertEqual(msg3.type, aiohttp.WSMsgType.ERROR)
