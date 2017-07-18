import aiohttp
import re
from aiosparql.syntax import IRI
from os import environ as ENV


re_resource = re.compile(
    r"""
    \(define-resource\s+(?P<resource>[\w-]+)\s*\(\)     # parse the resource
    \s+:class\s+\(s-prefix\s+"(?P<class>[^"]+)"         # parse the class
    """, flags=(re.VERBOSE + re.ASCII))

re_prefix = re.compile(
    r"""
    \(add-prefix\s+
    "(?P<prefix>[^"]+)"\s+      # parse prefix label
    "(?P<iri>[^"]+)"            # parse prefix IRI
    """, flags=(re.VERBOSE + re.ASCII))


def parse_domain(fileobj):
    return {
        match.group('class'): match.group('resource')
        for match in re_resource.finditer(fileobj.read())
    }


def parse_repository(fileobj):
    return {
        match.group('prefix'): IRI(match.group('iri'))
        for match in re_prefix.finditer(fileobj.read())
    }


class MuClResourcesClient(aiohttp.ClientSession):
    base_url = ENV["MU_CL_RESOURCES_ENDPOINT"]

    def _make_url(self, path):
        return "%s/%s" % (self.base_url, path)

    async def get(self, type_, id_):
        async with super().get(self._make_url("%s/%s" % (type_, id_))) as resp:
            resp.raise_for_status()
            return await resp.json()
