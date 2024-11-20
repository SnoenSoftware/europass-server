# Notice of archival
This project is no longer maintained, and has been archived. It is kept here for historical purposes, and may be used as a reference for future projects.
Europass has come out with a new version of their service, where you can no longer export your CV as an XML file. This means that this project is no longer useful, and has been archived.

# Europass CV server
### A flask server for your Eurpass generated CV

This server used to take your CV from [europass(defunct)](https://europass.cedefop.europa.eu/nb) and turn it into a web page.

## How to use it:
In the same folder as server.py, create a folder named data, and place your CV.xml file into it.
In a terminal, `cd` to the server's directory, then
```
$ pip install --user pipenv
$ pipenv install
$ ./server.py
```
and configure your server to forward incoming requests to localhost:5000.
If this will be the only thing running on your server, you can instead do
```
$ pip install --user pipenv
$ pipenv install
$ export FLASK_APP=server.py
$ flask run --host=0.0.0.0 --port=80
```
however depending on your sever you may need to change some permissions around to allow flask to run a server on port 80.
