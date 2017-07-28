#!/usr/bin/env python
from flask import Flask, render_template
from reader import Reader


app = Flask(__name__)
reader = Reader("data/CV.xml")


@app.route("/")
def index():
    data = {
        "first_name": reader.content_of("FirstName"),
        "surname": reader.content_of("Surname"),
        "address": "{addressline}, {postcode} {city} ({country})".format(
            addressline=reader.content_of("AddressLine"),
            postcode=reader.content_of("PostalCode"),
            city=reader.content_of("Municipality"),
            country=reader.content_of("Label")
        ),
        "phones": reader.element("TelephoneList").find_all("Telephone"),
        "email": reader.element("Email").string,
        "sites": reader.element("WebsiteList").find_all("Website"),
        "experience":
            reader.element("WorkExperienceList").find_all("WorkExperience"),
        "divider": divider
    }
    return render_template("resume.html", data=data)


@app.route("/image")
def image():
    data = "data:"
    data += reader.element("MimeType").contents[0]
    data += ";base64,"
    data += reader.element("Data").contents[0]
    return data


def divider(section_name):
    html = """
    <div class=".container">
    <div class="row">
    <div class="col-4 text-right">
    <h4 class="text-uppercase">{section_name}</h4>
    </div>
    <div class="col-8 text-right">
    <hr>
    </div>
    </div>
    </div>
    """.format(section_name=section_name)
    return html


if __name__ == "__main__":
    app.run()
