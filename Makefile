.DEFAULT_GOAL := prod

.PHONY: prod push

registry = ghcr.io/bjornsnoen
repository = europass-server

prod:
	docker build . -f docker/Dockerfile --target=runner -t $(registry)/$(repository)

push: prod
	docker push $(registry)/$(repository)
