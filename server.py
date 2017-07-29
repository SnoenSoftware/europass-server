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
        "phones": reader.find_all("Telephone"),
        "email": reader.element("Email").string,
        "sites": reader.find_all("Website"),
        "experience": reader.find_all("WorkExperience"),
        "educations": reader.find_all("Education"),
        "mother_tongue": reader.element("MotherTongue").Label.string,
        "languages": reader.find_all("ForeignLanguage"),
        "organisational": reader.element("Organisational").Description.string,
        "jobrelated": reader.element("JobRelated").Description.string,
        "digital": reader.element("Computer").Description.string,
        "achievements": reader.find_all("Achievement")
    }
    return render_template("resume.html", data=data)


@app.route("/image")
def image():
    data = "data:"
    data += reader.element("MimeType").contents[0]
    data += ";base64,"
    data += reader.element("Data").contents[0]
    return data


if __name__ == "__main__":
    app.run()
