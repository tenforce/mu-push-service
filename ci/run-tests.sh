#!/bin/bash

set -e

cd `dirname $0`
cd ..

if [ -z "$1" ]; then
	commands=(tox)
else
	commands=("$@")
fi

exec docker run -it --rm \
	--net mupushservice_test --net-alias push-service \
	-e TOX=true \
	-e MU_APPLICATION_GRAPH=http://mu.semte.ch/test \
	-e MU_SPARQL_ENDPOINT=http://delta:8890/sparql \
	-e MU_CL_RESOURCES_ENDPOINT=http://resources \
	-v "$PWD":/src \
	-v "$PWD"/ci/resources:/config \
	tenforce/push-service:latest "${commands[@]}"
