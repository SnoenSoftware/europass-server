#!/usr/bin/env python
from bs4 import BeautifulSoup as bs


class Reader:
    def __init__(self, path):
        self.soup = bs(self.read(path), "xml")

    def read(self, path):
        f = open(path, 'r')
        xml = ""
        for line in f.readlines():
            xml += line

        return xml

    def element(self, name):
        return self.soup.LearnerInfo.find(name)

    def content_of(self, tag):
        return self.element(tag).contents[0]

    def find_all(self, tag):
        return self.soup.find_all(tag)


if __name__ == "__main__":
    reader = Reader("data/CV.xml")
    soup = reader.soup
    data = soup.find("Data")
    data.extract()
    email = reader.element('Email')
    print(email.text)
