#!/usr/bin/env python
from flask import Flask, render_template, jsonify
from bs4.element import Tag
from reader import Reader
from pathlib import Path


app = Flask(__name__)
reader = Reader(Path(__file__).parent / "data/CV.xml")


def get_cv_data():
    return {
        "first_name": reader.content_of("FirstName"),
        "surname": reader.content_of("Surname"),
        "address": "{addressline}, {postcode} {city}".format(
            addressline=reader.content_of("AddressLine"),
            postcode=reader.content_of("PostalCode"),
            city=reader.content_of("Municipality"),
        ),
        "phones": reader.find_all("Telephone"),
        "email": reader.element("Email").text,
        "sites": reader.soup.find("Identification").find_all("Website"),
        "experience": reader.find_all("WorkExperience"),
        "educations": reader.find_all("Education"),
        "mother_tongue": reader.element("MotherTongue").Label.text,
        "languages": reader.find_all("ForeignLanguage"),
        "jobrelated": reader.element("JobRelated").Description.text,
        "digital": reader.element("Computer").Description.text,
        "achievements": reader.find_all("Achievement"),
    }


def tag_to_dict(tag):
    # Convert a BeautifulSoup Tag into a nested dict or value
    data = {}
    # include attributes
    if tag.attrs:
        data.update(tag.attrs)
    # collect child tags
    children = [c for c in tag.children if isinstance(c, Tag)]
    # no child tags: return attrs or text
    if not children:
        text = tag.get_text(strip=True)
        if data:
            if text:
                data["text"] = text
            return data
        return text
    # build dict from child tags
    for child in children:
        name = child.name
        val = tag_to_dict(child)
        if name in data:
            if isinstance(data[name], list):
                data[name].append(val)
            else:
                data[name] = [data[name], val]
        else:
            data[name] = val
    return data


def serialize_cv_data(obj):
    if isinstance(obj, dict):
        return {k: serialize_cv_data(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_cv_data(v) for v in obj]
    if isinstance(obj, Tag):
        return tag_to_dict(obj)
    return obj


@app.route("/rest/cv")
def rest_cv():
    data = get_cv_data()
    return jsonify(serialize_cv_data(data))


@app.route("/")
def index():
    data = get_cv_data()
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
