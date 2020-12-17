.DEFAULT_GOAL := prod

.PHONY: prod push

registry = registry.digitalocean.com

prod:
	docker build . -f docker/Dockerfile --target=runner -t $(registry)/brbcoffee/site:cv

push: prod
	docker push $(registry)/brbcoffee/site:cv

