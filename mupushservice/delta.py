import logging
from aiohttp import web
from aiosparql.syntax import IRI, Literal, RDF
from itertools import groupby

from mupushservice.prefixes import Mu


logger = logging.getLogger(__name__)


class Triple:
    """
    A triple: subject (s), predicate (p) and object (o)
    """
    def __init__(self, data):
        assert isinstance(data, dict)
        assert "s" in data
        assert isinstance(data['s'], dict) and data['p']['type'] == "uri"
        assert "p" in data
        assert isinstance(data['p'], dict) and data['p']['type'] == "uri"
        assert "o" in data
        assert isinstance(data['o'], dict)
        self.s = IRI(data['s']['value'])
        self.p = IRI(data['p']['value'])
        if data['o']['type'] == "uri":
            self.o = IRI(data['o']['value'])
        elif data['o']['type'] in ("literal", "typed-literal"):
            self.o = Literal(data['o']['value'])
        else:
            raise NotImplementedError("object type %s" % data['o']['type'])

    def __repr__(self):  # pragma: no cover
        return "<%s s=%s p=%s o=%s>" % (
            self.__class__.__name__, self.s, self.p, self.o)

    def __hash__(self):
        return hash((hash(self.s), hash(self.p), hash(self.o)))

    def __eq__(self, other):
        if isinstance(other, Triple):
            return hash(self) == hash(other)
        else:
            return False


class UpdateData:
    """
    A Delta service update: all its inserts, all its deletes
    """
    def __init__(self, data):
        assert isinstance(data['graph'], str)
        assert isinstance(data['inserts'], list)
        assert isinstance(data['deletes'], list)
        self.graph = data['graph']
        inserts = set(map(Triple, data['inserts']))
        deletes = set(map(Triple, data['deletes']))
        null_operations = inserts & deletes
        self.inserts = list(inserts - null_operations)
        self.deletes = list(deletes - null_operations)

    def __repr__(self):  # pragma: no cover
        return "<%s graph=%s inserts=%s deletes=%s>" % (
            self.__class__.__name__, self.graph, self.inserts, self.deletes)

    def filter_inserts(self, func):
        """
        Filter inserts that func(x) match where x is a singe triple of the
        update
        """
        assert callable(func)
        return (x for x in self.inserts if func(x))

    def filter_deletes(self, func):
        """
        Filter deletes that func(x) match where x is a singe triple of the
        update
        """
        assert callable(func)
        return (x for x in self.deletes if func(x))


def select_to_triples(result):
    """
    Transform the query result of a SELECT query to a list of triples.
    """
    return [Triple(x) for x in result['results']['bindings']]


def groupby_subject(triples):
    """
    Group a list of triples by subject and return a dict where the keys are the
    subjects and the values are lists of triples
    """
    return {
        s: list(group)
        for s, group in groupby(triples, lambda x: x.s)
    }


def filter_updates(data, resource_type):
    """
    Filter updates for a resource type
    """
    inserts = groupby_subject(data.filter_inserts(
        lambda x: x.s.value.startswith(resource_type.value)))
    deletes = groupby_subject(data.filter_deletes(
        lambda x: x.s.value.startswith(resource_type.value)))
    return (inserts, deletes)


async def generate_jobs_data(app, inserts, deletes):
    for s, group in groupby_subject(inserts).items():
        class_, id_ = await app.get_resource(s)
        type_ = app.resources[class_]
        data = await app.muclresources.get(type_, id_)
        yield (type_, {'push': data})

    for s, group in groupby_subject(deletes).items():
        values = {
            triple.p: triple.o
            for triple in group
        }
        if Mu.uuid not in values or RDF.type not in values:
            continue
        id_ = values[Mu.uuid].value
        type_ = app.resources[values[RDF.type]]
        yield (type_, {'delete': {'id': id_, 'type': type_}})


async def update(request):
    """
    The API entry point for the Delta service callback
    """
    graph = request.app.sparql.graph
    try:
        data = await request.json()
    except Exception:
        raise web.HTTPBadRequest(body="invalid json")
    try:
        data = [UpdateData(x) for x in data['delta']]
    except Exception:
        request.app.logger.exception("Cannot parse delta payload")
        raise web.HTTPBadRequest(body="cannot parse deltas received")
    try:
        first_data = next(x for x in data if x.graph == graph)
    except StopIteration:
        raise web.HTTPNoContent()

    async for type_, job in generate_jobs_data(request.app, first_data.inserts,
                                               first_data.deletes):
        for queue in request.app.filter_queues(type_):
            logger.debug("Added job %r to queue %r", job, queue)
            await queue.put(job)

    raise web.HTTPNoContent()
