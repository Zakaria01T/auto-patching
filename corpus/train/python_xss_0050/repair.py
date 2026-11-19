def build_tag_list(tags: list[str]) -> str:
    import xml.etree.ElementTree as ET
    ul = ET.Element("ul")
    for t in tags:
        li = ET.SubElement(ul, "li")
        li.text = str(t)
    return ET.tostring(ul, encoding="unicode", method="html")