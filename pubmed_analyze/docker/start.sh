if [ -f .env ]; then
  docker-compose --env-file .env up --build -d
else
  docker-compose up --build -d
fi
