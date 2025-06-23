#!/usr/bin/env python
from pathlib import Path
import base64
from typing import Tuple, Optional
from bs4 import BeautifulSoup as bs
import esco
import iso639
from html import unescape
from pypdf import PdfReader
from babel import Locale


class Reader:
    def __init__(self, path):
        # parse XML and detect format (old Europass v3 or new Europass v1)
        xml = self.read(path)
        self.soup = bs(xml, "xml")
        # detect version by root elements
        if self.soup.find("LearnerInfo"):
            # old format
            self.version = "old"
            langcode: str = self.soup.find("SkillsPassport").get("locale")  # type: ignore
            language = iso639.Language.from_part1(langcode)
            if language.macrolanguage:
                language = iso639.Language.from_part3(language.macrolanguage)
            self.language_code = str(language.part1)

            self.root = self.soup.find("LearnerInfo")
        elif self.soup.find("CandidatePerson"):
            # new format
            self.version = "new"
            self.language_code: str = self.soup.find("CandidateProfile").get("languageCode")  # type: ignore
            self.person = self.soup.find("CandidatePerson")
            self.profile = self.soup.find("CandidateProfile")
        else:
            raise ValueError("Unrecognized CV XML format")

    def read(self, path):
        f = open(path, "r")
        xml = ""
        for line in f.readlines():
            xml += line

        return xml

    def get_image_new_xml(self) -> Optional[Tuple[str, str]]:
        """
        Extract image data from new XML format.
        Returns a tuple of (mime_type, data).
        """
        sibling_candidates = self.soup.find_all("hr:Instructions")
        mime_type, b64_data = None, None
        for candidate in sibling_candidates:
            if candidate.string == "ProfilePicture":
                # Found the right sibling, now get the sibling with tag "oa:EmbeddedData"
                parent = candidate.parent
                data_sibling = parent.find("oa:EmbeddedData")
                if data_sibling:
                    data = data_sibling.string
                    decoded_data = base64.b64decode(data).decode("utf-8")
                    mime_type = decoded_data.split(";")[0]
                    mime_type = (
                        mime_type.split(":")[1] if ":" in mime_type else mime_type
                    )
                    mime_type = mime_type.strip()

                    b64_data = (
                        decoded_data.split(",")[1] if "," in decoded_data else None
                    )

        if mime_type and b64_data:
            return mime_type, b64_data

    def get_language_name(self, lang_code: str) -> str:
        """
        Get the language name for a given language code.
        Uses iso639 to get the language name in the specified language.
        Uses resume locale to get the language name in the correct format.
        """
        resume_language = iso639.Language.from_part1(self.language_code)
        resume_locale = Locale(resume_language.part1)
        language = iso639.Language.from_part3(lang_code)
        if language.macrolanguage:
            language = iso639.Language.from_part3(language.macrolanguage)
        name = resume_locale.languages[language.part1] or language.name

        return name.capitalize()

    def element(self, name):
        """
        Return a single Tag for given element name, mapping new XML to expected tags.
        """
        # old format: tags under LearnerInfo
        if getattr(self, "version", None) == "old":
            return self.root.find(name)
        # new format mapping
        if self.version == "new":
            # simple tag mappings
            if name == "FirstName":
                return self.person.find("GivenName")
            if name == "Surname":
                return self.person.find("FamilyName")
            if name == "AddressLine":
                return self.person.find("AddressLine")
            if name == "PostalCode":
                return self.person.find("PostalCode")
            if name == "Municipality":
                return self.person.find("CityName")
            # email
            if name == "Email":
                for comm in self.person.find_all("Communication"):
                    code = comm.find("ChannelCode")
                    if code and code.text.lower() == "email":
                        return comm.find("URI") or comm
                return None
            # mother tongue: map primary language
            if name == "MotherTongue":
                plc = self.person.find("PrimaryLanguageCode")
                mt = self.soup.new_tag("MotherTongue")
                desc = self.soup.new_tag("Description")
                code = self.soup.new_tag("Code")
                label = self.soup.new_tag("Label")
                if plc:
                    code.string = plc.text
                    label.string = self.get_language_name(plc.text)
                desc.append(code)
                desc.append(label)
                mt.append(desc)
                return mt
            # job-related and computer/digital skills under Others in CandidateProfile
            if name in ("JobRelated", "Computer"):
                # find Other blocks under CandidateProfile
                for sec in self.profile.find_all("Others"):
                    other = sec.find("Other")
                    if not other:
                        continue
                    title = other.find("Title")
                    if not title:
                        continue
                    txt = title.text.strip().lower()
                    # map: job-related uses 'work experience'
                    if name == "JobRelated" and "arbeidskompetanse" in txt:
                        desc = other.find("Description")
                    # map: digital skills uses 'digital competencies'
                    elif name == "Computer" and "digital kompetanse" in txt:
                        desc = other.find("Description")
                    else:
                        continue
                    tag = self.soup.new_tag(name)
                    dtag = self.soup.new_tag("Description")
                    if desc is not None:
                        dtag.string = desc.text
                    tag.append(dtag)
                    return tag
                # fallback empty
                tag = self.soup.new_tag(name)
                tag.append(self.soup.new_tag("Description"))
                return tag
            # image data
            if name == "Data":
                ed = self.soup.find("EmbeddedData")
                # In old XML it was just a simple EmbeddedData tag, in new XML it is under oa namespace
                # We need to ensure we're not using the new XML format, because that needs special handling
                # That means we need to check that the tag we found is not under the oa namespace
                if ed and not ed.namespace:
                    return ed

                img_data = self.get_image_new_xml()
                if img_data:
                    ed = self.soup.new_tag("EmbeddedData")
                    ed.string = img_data[1]
                    return ed

            if name == "MimeType":
                mt = self.soup.find("MimeType")
                if mt:
                    return mt

                img_data = self.get_image_new_xml()
                if img_data:
                    mt = self.soup.new_tag("MimeType")
                    mt.string = img_data[0]  # mime type
                    return mt

        # fallback: find by tag name
        return self.soup.find(name)

    def content_of(self, tag):
        return self.element(tag).contents[0]

    def find_all(self, tag):
        """
        Return list of Tags for given name, mapping new XML lists to expected tags.
        """
        if getattr(self, "version", None) == "old":
            if tag == "Website":
                person = self.soup.find("LearnerInfo")
                sites = person.find("ContactInfo").find_all("Website")
                return sites

            return self.soup.find_all(tag)

        if self.version == "new":
            # map legacy tag names to new XML structures
            if tag == "Telephone":
                phones = []
                for comm in self.person.find_all("Communication"):
                    code = comm.find("ChannelCode")
                    if code and code.text.lower() == "telephone":
                        # build Telephone tag
                        phone = self.soup.new_tag("Telephone")
                        # Use/Code
                        usecode = comm.find("UseCode")
                        use = self.soup.new_tag("Use")
                        ctag = self.soup.new_tag("Code")
                        if usecode:
                            ctag.string = usecode.text
                        use.append(ctag)
                        phone.append(use)
                        # Contact number
                        dn = comm.find("DialNumber")
                        contact = self.soup.new_tag("Contact")
                        if dn:
                            contact.string = dn.text
                        phone.append(contact)
                        phones.append(phone)
                return phones
            if tag == "Website":
                sites = []
                for comm in self.person.find_all("Communication"):
                    code = comm.find("ChannelCode")
                    if code and code.text.lower() == "web":
                        uri = comm.find("URI")
                        if uri:
                            site = self.soup.new_tag("Website")
                            # represent site URL as tag text
                            site.string = uri.text
                            sites.append(site)
                return sites
            if tag == "WorkExperience":
                wex = []
                if self.profile:
                    eh = self.profile.find("EmploymentHistory")
                    if eh:
                        for hist in eh.find_all("EmployerHistory"):
                            # build WorkExperience tag
                            we = self.soup.new_tag("WorkExperience")
                            # Period
                            ph = hist.find("PositionHistory")
                            if ph:
                                ep = (
                                    ph.find("EmploymentPeriod")
                                    or ph.find("eures:EmploymentPeriod")
                                    or ph.find("EmploymentPeriod")
                                )
                                if ep:
                                    period = self.soup.new_tag("Period")
                                    # From
                                    sd = ep.find("FormattedDateTime")
                                    if sd and sd.text:
                                        parts = sd.text.split("-")
                                        if len(parts) == 3:
                                            fr = self.soup.new_tag("From")
                                            fr["year"], m, d = parts
                                            fr["month"] = f"--{m}"
                                            fr["day"] = f"---{d}"
                                            period.append(fr)
                                    # To
                                    ed = ep.find("EndDate")
                                    if ed:
                                        edt = ed.find("FormattedDateTime")
                                        if edt and edt.text:
                                            parts = edt.text.split("-")
                                            if len(parts) == 3:
                                                to = self.soup.new_tag("To")
                                                to["year"], m2, d2 = parts
                                                to["month"] = f"--{m2}"
                                                to["day"] = f"---{d2}"
                                                period.append(to)
                                    # Current
                                    ci = ep.find("CurrentIndicator") or ep.find(
                                        "Current"
                                    )
                                    if ci:
                                        cur = self.soup.new_tag("Current")
                                        cur.string = ci.text
                                        period.append(cur)
                                    we.append(period)
                            # Position
                            pos = self.soup.new_tag("Position")
                            lbl = self.soup.new_tag("Label")
                            pt = hist.find("PositionTitle")
                            if pt:
                                lbl.string = pt.text
                                if pt.get("typeCode") == "URI":
                                    lbl.string = pt.text
                                    lbl.attrs["alternativeLabel"] = (
                                        esco.get_esco_occupation(
                                            pt.get("languageID"), self.language_code
                                        ).capitalize()
                                    )
                            pos.append(lbl)
                            we.append(pos)
                            # Activities
                            desc = hist.find("Description") or hist.find(
                                "oa:Description"
                            )
                            act = self.soup.new_tag("Activities")
                            if desc:
                                # preserve inner HTML
                                act.string = unescape(desc.decode_contents())
                                we.append(act)
                            # Employer
                            emp = self.soup.new_tag("Employer")
                            nm = self.soup.new_tag("Name")
                            org = hist.find("OrganizationName") or hist.find(
                                "hr:OrganizationName"
                            )
                            if org:
                                nm.string = org.text

                            site = hist.find("Website") or hist.find("oa:URI")
                            if site:
                                ws = self.soup.new_tag("Website")
                                contact = self.soup.new_tag("Contact")
                                address_line = self.soup.new_tag("AddressLine")
                                address_line.string = site.text
                                contact.append(address_line)
                                ws.append(contact)
                                emp.append(ws)

                            emp.append(nm)
                            # optional: nest contact info if needed
                            we.append(emp)
                            wex.append(we)
                return wex
            if tag == "Education":
                eds = []
                if self.profile:
                    eh = self.profile.find("EducationHistory")
                    if eh:
                        for ea in eh.find_all("EducationOrganizationAttendance"):
                            edu = self.soup.new_tag("Education")
                            # Period
                            ap = ea.find("AttendancePeriod")
                            if ap:
                                period = self.soup.new_tag("Period")
                                sd = ap.find("FormattedDateTime")
                                if sd and sd.text:
                                    parts = sd.text.split("-")
                                    if len(parts) == 3:
                                        fr = self.soup.new_tag("From")
                                        fr["year"], m, d = parts
                                        fr["month"] = f"--{m}"
                                        fr["day"] = f"---{d}"
                                        period.append(fr)
                                edt = ap.find("EndDate")
                                if edt:
                                    dt = edt.find("FormattedDateTime")
                                    if dt and dt.text:
                                        parts = dt.text.split("-")
                                        if len(parts) == 3:
                                            to = self.soup.new_tag("To")
                                            to["year"], m2, d2 = parts
                                            to["month"] = f"--{m2}"
                                            to["day"] = f"---{d2}"
                                            period.append(to)
                                og = ap.find("Ongoing")
                                if og:
                                    cur = self.soup.new_tag("Current")
                                    cur.string = og.text
                                    period.append(cur)
                                edu.append(period)
                            # Title
                            title = self.soup.new_tag("Title")
                            dn = ea.find("DegreeName") or ea.find("hr:DegreeName")
                            if dn:
                                title.string = dn.text
                            edu.append(title)
                            # Organisation
                            org_tag = self.soup.new_tag("Organisation")
                            nm = self.soup.new_tag("Name")
                            on = ea.find("OrganizationName") or ea.find(
                                "hr:OrganizationName"
                            )
                            if on:
                                nm.string = on.text
                            org_tag.append(nm)
                            edu.append(org_tag)
                            eds.append(edu)
                return eds
            if tag == "ForeignLanguage":
                langs = []
                if self.profile:
                    pq = self.profile.find("PersonQualifications")
                    if pq:
                        for pc in pq.find_all("PersonCompetency"):
                            tid = pc.find("TaxonomyID") or pc.find("hr:TaxonomyID")
                            if tid and tid.text.lower() == "language":
                                fl = self.soup.new_tag("ForeignLanguage")
                                # Description/Label
                                desc = self.soup.new_tag("Description")
                                lbl = self.soup.new_tag("Label")
                                cid = pc.find("CompetencyID")
                                if cid:
                                    lbl.string = self.get_language_name(cid.text)
                                desc.append(lbl)
                                fl.append(desc)
                                # ProficiencyLevel
                                pl = self.soup.new_tag("ProficiencyLevel")
                                for dim in pc.find_all("CompetencyDimension"):
                                    ccode = dim.find("CompetencyDimensionTypeCode")
                                    score = dim.find("ScoreText") or dim.find(
                                        "hr:ScoreText"
                                    )
                                    if ccode and score:
                                        # map to tag name
                                        text = ccode.text or ""
                                        key = text.split("-")[-1]
                                        if key.lower() == "interaction":
                                            key = "SpokenInteraction"
                                        elif (
                                            key.lower() == "production"
                                            and "writing" in text.lower()
                                        ):
                                            key = "Writing"
                                        elif key.lower() == "production":
                                            key = "SpokenProduction"
                                        # normalize first char uppercase
                                        tag_name = key[0].upper() + key[1:]
                                        nd = self.soup.new_tag(tag_name)
                                        nd.string = score.text
                                        pl.append(nd)
                                fl.append(pl)
                                langs.append(fl)
                return langs
            # no mapping: return empty list
            return []
        # fallback for unknown
        return self.soup.find_all(tag)


def pdf_to_xml(path_to_pdf: Path, path_to_xml: Path):
    """
    Convert a PDF CV to XML format.
    """
    reader = PdfReader(path_to_pdf)
    attachment = reader.attachments["attachment.xml"][0].decode("utf-8")
    with open(path_to_xml, "w+") as f:
        f.write(attachment)


if __name__ == "__main__":
    reader = Reader("data/CV.xml")
    soup = reader.soup
    data = soup.find("Data")
    data.extract()
    email = reader.element("Email")
    print(email.text)
