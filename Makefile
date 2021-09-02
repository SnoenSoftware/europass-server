.DEFAULT_GOAL := prod

.PHONY: prod push

registry = ghcr.io/bjornsnoen

prod:
	docker build . -f docker/Dockerfile --target=runner -t $(registry)/europass-server:latest

push: prod
	docker push $(registry)/brbcoffee/site:cv

