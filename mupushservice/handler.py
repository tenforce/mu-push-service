import asyncio
import json
import logging
from aiohttp import WSMsgType, web


logger = logging.getLogger(__name__)


class Queue(asyncio.Queue):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.watch_list = []

    def update_watch_list(self, l):
        if not isinstance(l, list):
            raise TypeError("Invalid type for watch list: %r" % type(l))
        self.watch_list[:] = l


async def ws_feed(app, ws, queue):
    try:
        while True:
            job = await queue.get()
            ws.send_json(job)
    except asyncio.CancelledError:
        logger.debug("Stop sending push notifications to %r", ws)
    except Exception:
        logger.exception("WebSocket feed critical failure")


async def ws_handler(request):
    app = request.app
    ws = web.WebSocketResponse(autoping=True, heartbeat=app.heartbeat)
    await ws.prepare(request)
    queue = Queue()
    app.queues.append(queue)
    try:
        feed_task = app.loop.create_task(ws_feed(app, ws, queue))
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        watch_list = json.loads(msg.data)
                    except Exception as exc:
                        logger.error("Cannot parse JSON message: %r", msg.data)
                        continue
                    try:
                        queue.update_watch_list(watch_list)
                    except Exception as exc:
                        logger.error(str(exc))
                        continue
        finally:
            feed_task.cancel()
            await feed_task
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("WebSocket critical failure")
    finally:
        await ws.close()
        app.queues.remove(queue)
        return ws
