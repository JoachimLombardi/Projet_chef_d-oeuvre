COMPOSE_FILE="pubmed_analyze/docker/docker-compose.yml"

if [ -f .env ]; then
  docker-compose -f $COMPOSE_FILE --env-file .env up --build -d
else
  docker-compose -f $COMPOSE_FILE up --build -d
fi
