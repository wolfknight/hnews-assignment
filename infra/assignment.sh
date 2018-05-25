#!/bin/bash
DOCKER_COMPOSE_CMD="docker-compose"
DOCKER_CMD="docker"
INFRA_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# If user isn't root
if [ "$(id -u)" != "0" ]; then
    DOCKER_COMPOSE_CMD="sudo $DOCKER_COMPOSE_CMD"
    DOCKER_CMD="sudo $DOCKER_CMD"
fi

case "$1" in
  start)
    echo "Starting HNews Assignment"
    $DOCKER_COMPOSE_CMD -f $INFRA_DIR/docker/docker-compose.yml up --build -d
    echo "The server is available at port 8080 in the following IP $($DOCKER_CMD inspect docker_backend_1 | grep \"IPAddress\")"
    ;;
  stop)
    echo "Stopping HNews Assignment"
    $DOCKER_COMPOSE_CMD -f $INFRA_DIR/docker/docker-compose.yml down
    ;;
  *)
    echo "Usage: $0 {start|stop}"
    exit 1
    ;;
esac
