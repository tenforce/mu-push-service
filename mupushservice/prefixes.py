from aiosparql.syntax import IRI, Namespace, PrefixedName


class Mu(Namespace):
    __iri__ = IRI("http://mu.semte.ch/vocabularies/core/")

    uuid = PrefixedName
