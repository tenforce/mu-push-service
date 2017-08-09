[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build Status](https://travis-ci.org/tenforce/push-service.svg?branch=master)](https://travis-ci.org/tenforce/push-service)
[![codecov](https://codecov.io/gh/tenforce/push-service/branch/master/graph/badge.svg)](https://codecov.io/gh/tenforce/push-service)

Mu Push Service
===============

Service that provides WebSocket for the client to be notified when changes
happen to the database.

Usage
-----

You need to have the [Delta
service](https://github.com/mu-semtech/mu-delta-service) and
[mu-cl-resources](https://github.com/mu-semtech/mu-cl-resources) to be running:

```
docker run -it --rm --name push-service -p 8080:80 \
    -e MU_SPARQL_ENDPOINT=http://delta:8890/sparql \
    -e MU_CL_RESOURCES_ENDPOINT=http://resources \
    -v <path_to_mu_cl_resource_config>:/config \
    tenforce/push-service
```

Also: don't forget to register this service in the subscribers of the Delta
service:

```
subscribers.json:

{
  "potentials":[
    "http://push-service/update"
  ],
  "effectives":[
  ]
}
```
