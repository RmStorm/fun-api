build:
	 docker build . -t eu.gcr.io/nube-hub/roald-api:latest

push:
	docker push eu.gcr.io/nube-hub/roald-api:latest
