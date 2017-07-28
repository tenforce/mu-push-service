import asyncio
import logging
from aiohttp import web


logger = logging.getLogger(__name__)


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
    queue = asyncio.Queue()
    app.queues.append(queue)
    try:
        feed_task = app.loop.create_task(ws_feed(app, ws, queue))
        try:
            async for _ in ws:  # noqa
                pass
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
