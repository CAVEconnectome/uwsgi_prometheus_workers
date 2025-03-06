docker buildx build --platform linux/amd64 -t caveconnectome/uwsgi-export-workers:v${1} .
docker push caveconnectome/uwsgi-export-workers:v${1}