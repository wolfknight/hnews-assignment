#!/bin/bash
DOCKER_CMD="docker"
INFRA_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# If user isn't root
if [ "$(id -u)" != "0" ]; then
    alias docker='sudo docker'
    DOCKER_CMD="sudo $DOCKER_CMD"
fi


$DOCKER_CMD build -t rest-server $INFRA_DIR/docker/rest-server/
$DOCKER_CMD run -i -v $INFRA_DIR/../:/code -t rest-server python test/run_tests.py
