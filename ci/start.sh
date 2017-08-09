#!/bin/bash

set -e

cd `dirname $0`

docker network create mupushservice_test

docker run -d --name=mupushservice_test_db \
	--net mupushservice_test \
	--network-alias database \
	-e SPARQL_UPDATE=true \
	-e DEFAULT_GRAPH=http://mu.semte.ch/test \
	-p 8890:8890 \
	tenforce/virtuoso:1.2.0-virtuoso7.2.2

docker run -d --name=mupushservice_test_delta \
	--net mupushservice_test \
	--network-alias delta \
	-e CONFIGFILE=/config/config.properties \
	-e SUBSCRIBERSFILE=/config/subscribers.json \
	-v "$PWD"/delta:/config \
	-p 8891:8890 \
	semtech/mu-delta-service:beta-0.9

docker run -d --name=mupushservice_test_resources \
	--net mupushservice_test \
	--network-alias resources \
	-e MU_APPLICATION_GRAPH=http://mu.semte.ch/test \
	-v "$PWD"/resources:/config \
	-p 8880:80 \
	semtech/mu-cl-resources:1.15.0

docker pull tenforce/push-service:latest
