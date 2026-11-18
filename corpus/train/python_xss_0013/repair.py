def paragraph(text):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup("", "html.parser")
    p = soup.new_tag("p")
    p.string = text
    return p