#!/bin/bash

docker rm -vf mupushservice_test_resources
docker rm -vf mupushservice_test_delta
docker rm -vf mupushservice_test_db
docker network rm mupushservice_test
