# fun-api

To locally test changes:
```bash
docker-compose build && docker-compose up
```

To make a new version:
```bash
docker build . -t eu.gcr.io/nube-hub/roald-api:latest
docker push eu.gcr.io/nube-hub/roald-api:latest
```
