from aiohttp import web
from os import environ as ENV

from mupushservice.main import app


web.run_app(app, port=(int(ENV['PORT']) if 'PORT' in ENV else None))
