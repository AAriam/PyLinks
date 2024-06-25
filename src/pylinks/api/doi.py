# Standard libraries
import re
import unicodedata
import datetime
from typing import Optional

# Non-standard libraries
import pylinks as _pylinks


class DOI:
    """

    References
    ----------
    https://citation.crosscite.org/docs.html
    https://www.doi.org/hb.html
    https://support.datacite.org/docs/doi-basics
    """

    def __init__(self, doi: str):
        """
        Parameters
        ----------
        doi : str
            Digital Object Identifier (DOI) of a publication,
            either as a URL (optionally starting with either 'http://' or 'https://',
            followed by either 'dx.doi.org/' or 'doi.org/', and then the identifier),
            or the identifier alone (starting with '10.'). For example:
            * '10.3762/bjoc.17.8'
            * 'https://doi.org/10.1039/d2sc03130b'
            * 'dx.doi.org/10.1093/nar/gkac267'
        """
        match = re.match(r"(?:https?://)?(?:dx\.)?(?:doi\.org/)?(10\.\d+/\S+)", doi)
        if not match:
            raise ValueError(f"Invalid DOI: {doi}")
        self.doi = match.group(1)
        self.url = f"https://doi.org/{self.doi}"  # See also: https://api.crossref.org/works/{doi}
        return

    def text(self, style: Optional[str] = None, locale: Optional[str] = None) -> str:
        """
        Formatted text citation for the DOI, with an optional citation style and locale.

        The citation is generated by the [Citation Style Language](https://citationstyles.org/)
        (CSL) processor (citeproc).

        Parameters
        ----------
        style : str, optional
            Citation style, e.g. APA, Harvard, Angewandte Chemie etc.
            More than 1000 styles are available; see https://github.com/citation-style-language/styles.
        locale : str, optional
            Locale to use for the citation; see https://github.com/citation-style-language/locales.
        """
        accept = "text/x-bibliography"
        if style:
            accept += f"; style={style}"
        if locale:
            accept += f"; locale={locale}"
        return _pylinks.http.request(
            self.url, headers={"accept": accept}, encoding="utf-8", response_type="str"
        )

    @property
    def bibtex(self) -> str:
        return _pylinks.http.request(
            self.url,
            headers={"accept": "application/x-bibtex"},
            encoding="utf-8",
            response_type="str",
        )

    @property
    def ris(self) -> str:
        return _pylinks.http.request(
            self.url,
            headers={"accept": "application/x-research-info-systems"},
            encoding="utf-8",
            response_type="str",
        )

    @property
    def citeproc_dict(self) -> dict:
        """
        Citation data as a dictionary with Citeproc JSON schema.
        """
        return _pylinks.http.request(
            self.url,
            headers={"accept": "application/citeproc+json"},
            encoding="utf-8",
            response_type="json",
        )

    @property
    def curated(self):
        data = self.citeproc_dict
        journal = data["container-title"] or None
        journal_abbr = (
            (
                data.get("container-title-short") or _pylinks.http.request(
                f"https://abbreviso.toolforge.org/abbreviso/a/{journal}",
                    response_type="str",
                ).title()
            )
            if journal else None
        )
        date = self._get_date(data)
        curated = {
            "doi": self.doi,
            "url": f"https://doi.org/{self.doi}",
            "type": data["type"],  # e.g. 'journal-article', 'posted-content'
            "subtype": data.get("subtype"),  # e.g. 'preprint' for 'posted-content' type
            "cite": {
                "BibTex": self.bibtex,
                "RIS": self.ris,
            },  # bibtex citation string
            "journal": journal,  # journal name
            "journal_abbr": journal_abbr,  # journal abbreviation
            "publisher": data.get("publisher"),  # publisher name
            "title": data.get("title"),  # title of the publication
            "pages": data.get("page"),  # page numbers
            "volume": data.get("volume"),  # volume number
            "issue": data.get("issue"),  # issue number
            "date_tuple": date,  # tuple of (year, month, day)
            "year": date[0],
            "date": datetime.date(*date).strftime("%e %B %Y").lstrip(),
            "abstract": self.jats_to_html(data["abstract"]) if data.get("abstract") else None,
        }
        return curated

    @staticmethod
    def jats_to_html(string):
        convert = {
            r"<jats:sub>(.*?)</jats:sub>": r"<sub>\1</sub>",
        }
        norm = unicodedata.normalize("NFKC", string)
        paragraph_match = re.search("<jats:p>(.*?)</jats:p>", norm)
        paragraph = paragraph_match.group(1) if paragraph_match else norm
        for pattern, repl in convert.items():
            paragraph = re.sub(pattern, repl, paragraph)
        return paragraph

    @staticmethod
    def _get_date(data):
        year = None
        month = None
        day = None
        for choice in (
                "pubished",
                "published-online",
                "published-print",
                "published-other",
                "issued",
                "created",
                "deposited",
                "indexed",
        ):
            if year and month and day:
                break
            date = data.get(choice, dict()).get("date-parts", [None])[0]
            if date:
                year = year or date[0]
                if not month:
                    if len(date) == 2:
                        month = date[1]
                    if len(date) == 3:
                        month = date[1]
                        day = date[2]
        return year, month or 1, day or 1
