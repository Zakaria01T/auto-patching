def paragraph(text):
    from bs4 import BeautifulSoup
    return BeautifulSoup(f"<p>{text}</p>", "html.parser")