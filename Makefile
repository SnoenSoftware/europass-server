.DEFAULT_GOAL := prod

.PHONY: prod push

registry = ghcr.io/snoensoftware
repository = europass-server

prod:
	docker build . -f docker/Dockerfile --target=runner -t $(registry)/$(repository)

push: prod
	docker push $(registry)/$(repository)

deps:
	uv sync --python 3.9

dev: deps
	FLASK_APP=server.py uv run flask run --port 5000 --reload

docker_test: prod
	docker run --rm -it -p 5000:5000 -v $(pwd)/data/:/app/data/ ghcr.io/snoensoftware/europass-server 
