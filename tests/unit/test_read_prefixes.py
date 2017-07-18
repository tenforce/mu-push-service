import mupushservice.main


def test_read_prefixes():
    app = mupushservice.main.Application()

    assert app.prefixes == {
        "dct": "http://purl.org/dc/terms/",
        "mu": "http://mu.semte.ch/vocabularies/core/",
        "push": "http://mu.semte.ch/vocabularies/push/",
    }


def test_read_resources():
    app = mupushservice.main.Application()

    assert app.resources == {
        "http://mu.semte.ch/vocabularies/push/Resource1": "resource1",
        "http://mu.semte.ch/vocabularies/push/Resource2": "resource2",
    }
