# Europass CV server
### A flask server for your Eurpass generated CV

This server takes your CV from [europass](https://europa.eu/europass/eportfolio/screen/dashboard?lang=en) and turn it into a web page.

## How to use it:
In the same folder as server.py, create a folder named data, and place your CV.pdf file into it.
Note that the file must be named `CV.pdf` and it must be a valid Europass CV. If it does not work then you probably have a too old version of the Europass CV, or you have not downloaded it from the Europass website.
In a terminal, `cd` to the server's directory, then
```
$ uv sync --python 3.9
$ export FLASK_APP=server.py
$ uv run flask run --port=5000
```
and configure your server to forward incoming requests to localhost:5000.
If this will be the only thing running on your server, you can instead do
```
$ uv sync --python 3.9
$ export FLASK_APP=server.py
$ flask run --host=0.0.0.0 --port=80
```
however depending on your sever you may need to change some permissions around to allow flask to run a server on port 80.

## How to style it 
If you would rather have your CV styled differently, you can override the css file in `static/style.css`.
You also have the option of replacing the frontend entirely and grabbing the CV data from the `/rest/cv` endpoint.
