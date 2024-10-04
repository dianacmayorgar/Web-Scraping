import requests
from bs4 import BeautifulSoup, Comment, NavigableString
from urllib.parse import urljoin
import re
import json

#Fixear tablas
#https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/prepare/minor-children.html
#

pageMain = "https://www.canada.ca/en/services/immigration-citizenship.html"


def custom_text_with_links(soup):
    if soup is None:
        return ""

    soup = clean_html_spaces(soup)

    # Recorre todos los <li>
    for li in soup.find_all("li"):
        if li.find_parent("ul") and li.find_parent("ul").find_parent("ul"):
            li.insert_before(f" - - ")
        else:
            li.insert_before(f" - ")

    # Unir todo en una cadena final
    return soup.get_text().strip()

def remove_newlines(text):
    # Usamos re.sub para eliminar todos los saltos de línea (\r y \n)
    return re.sub(r'[\n\n]+', '\n', text)

def clean_text(text):
    # Reemplazar múltiples saltos de línea (\r o \n) por un espacio
    text = re.sub(r'[\r\n]+', ' ', text)
    # Reemplazar más de dos espacios consecutivos por un solo espacio
    text = re.sub(r' {2,}', ' ', text)
    # Eliminar espacios extra al principio y al final
    return text.strip()

# Función para limpiar el contenido del HTML
def clean_html_spaces(soup):
    # Limpiar el texto dentro de cada párrafo <p>
    for p in soup.find_all('p'):
        cleaned_text = clean_text(p.get_text())
        p.string = cleaned_text  # Reemplaza el texto con el texto limpio
    
    return soup

class CanadaInmigration:
    def __init__(self) -> None:
        self.all_links_scraped = []

    def get_type(self, soup):
        return "container" if soup.find("section", "gc-srvinfo") else "page"

    def search(self, soup):
        title = soup.find("div", "mwsgeneric-base-html parbase section").find("h1")
        links = []
        
        if title:
            title = title
            description = title.find_next("p").text.strip()
            title = title.text.strip()

            for subpage in soup.find("section", "gc-srvinfo").find_all("div", "col-md-4"):
                title = subpage.find("h3").text.strip()
                link = subpage.find("a").get("href")
                if link[0] == "/":
                    link = "https://www.canada.ca" + link

                if "www.canada.ca" not in link:
                    continue

                subpage.find("h3").decompose()
                description = subpage.text.strip()
                links.append({"title": title, "link": link, "description": description})
        else:
            title = soup.find("div", "mwstitle section").find("h1")
            description = title.find_next().text.strip()
            title = title.text.strip()

            for subpage in soup.find("section", "gc-srvinfo").find_all("div", "col-lg-4 col-md-6"):
                title = subpage.find("h4").text.strip()
                link = subpage.find("a").get("href")
                if link[0] == "/":
                    link = "https://www.canada.ca" + link

                if "www.canada.ca" not in link:
                    continue

                subpage.find("h4").decompose()
                description = subpage.text.strip()
                links.append({"title": title, "link": link, "description": description})
        
        return links

    def get_information_cards(self, soup):
        #https://www.canada.ca/en/immigration-refugees-citizenship/services/new-immigrants/pr-travel-document.html

        cards = []
        for card in soup.find_all("div", "row mrgn-bttm-lg"):
            title_ = card.find("h2")
            links = []

            for a in card.find_all("a"):
                href = a.get("href")
                if href:
                    # Si el href es relativo, lo convertimos en absoluto usando la página principal
                    if not href.startswith(("http://", "https://")):
                        href = urljoin("https://www.canada.ca", href)

                        if "www.canada.ca" not in href:
                            continue

                        links.append(href)

            if title_:
                title = title_.text.strip()
                title_.decompose()
            else:
                title_ = card.find("h3")

                if title_:
                    title = title_.text.strip()
                    title_.decompose()

            text = card.text.strip()
            try:
                cards.append({"title": title, "text": text, "links": links})
            except:
                pass
            card.decompose()

        for card in soup.find_all("section", class_ ="brdr-rds-0"):
            for l in card.find_all("section"):
                l.decompose()

            title_ = card.find("h2")
            links = []

            for a in card.find_all("a"):
                href = a.get("href")
                if href:
                    # Si el href es relativo, lo convertimos en absoluto usando la página principal
                    if not href.startswith(("http://", "https://")):
                        href = urljoin("https://www.canada.ca", href)

                        if "www.canada.ca" not in href:
                            continue

                        links.append(href)

            if title_ == None:
                title_ = card.find("h3")
            
            if title_ == None:
                title_ = card.find("p", "mrgn-bttm-0 mrgn-tp-sm")

            if title_:
                title = title_.text.strip()
                title_.decompose()
            else:
                title = None

            text = card.text.strip()

            if title == None and text == None or title == None and text == '':
                continue

            cards.append({"title": title, "text": text, "links": links})
            card.decompose()

        for card in soup.find_all("section", class_="panel-primary"):
            title_ = card.find("h2", "panel-title")
            links = []

            for a in card.find_all("a"):
                href = a.get("href")
                if href:
                    # Si el href es relativo, lo convertimos en absoluto usando la página principal
                    if not href.startswith(("http://", "https://")):
                        href = urljoin("https://www.canada.ca", href)

                        if "www.canada.ca" not in href:
                            continue

                        links.append(href)

            if title_ == None:
                title_ = card.find("h3")

            if title_ == None:
                title_ = card.find("h4")

            if title_ == None:
                title_ = card.find(class_= "panel-title")

            title = title_.text.strip()
            title_.decompose()
            text = card.text.strip()
            cards.append({"title": title, "text": text, "links": links})
            card.decompose()

        return cards

    def get_seccions(self, link_, soup):
        seccions = []
        for seccion in soup.find_all("nav", "gc-subway", recursive=False):
            if seccion.find("dl") == False:
                continue

            for title, description in zip(
                seccion.find("dl").find_all("dt"), seccion.find("dl").find_all("dd")
            ):
            
                link = title.find("a").get("href")
                if not link.startswith(("http://", "https://")):
                    link = urljoin("https://www.canada.ca", link)

                if "www.canada.ca" not in link:
                    continue

                title = title.text.strip()
                description = description.text.strip().split("\r\n")[0]
                seccions.append(
                    {
                        "title": title,
                        "link": link,
                        "description": description
                    }
                )

            seccion.decompose()

        for seccion in soup.find_all("a", "list-group-item"):
            link = seccion.get("href")
            title = seccion.text.strip()

            if title[0].isdigit():
                title = title.split(".", 1)[-1].strip()

            if link == None:
                link = link_

            if not link.startswith(("http://", "https://")):
                link = urljoin("https://www.canada.ca", link)

            if "www.canada.ca" not in link:
                continue

            seccions.append(
                    {
                        "title": title,
                        "link": link
                    }
                )
            seccion.parent.decompose()
        return seccions
    
    def get_panels(self, soup):
        panels = []

        for panel in soup.find_all("section", "panel-default"):
            titleTag = panel.find("h2")

            if titleTag == None:
                titleTag = panel.find("h3")
                
            if titleTag == None:
                titleTag = panel.find("p", "h3")

            if titleTag == None:
                titleTag = panel.find(class_ = "panel-title")
                

            title = custom_text_with_links(titleTag)
            titleTag.decompose()
            panels.append(
                {
                    "title": title,
                    "description": custom_text_with_links(panel),
                }
            )
            panel.decompose()
        return panels

    def get_alerts(self, soup):
        alerts = []
        alertsDiv = soup.find_all("div", "alert")

        if alertsDiv == []:
            alertsDiv = soup.find_all("section", "alert")

        for alert in alertsDiv:
            if "alert-info" in alert.get("class"):
                alertType = "information"
            elif "alert-warning" in alert.get("class"):
                alertType = "warning"
            elif "alert-danger" in alert.get("class"):
                alertType = "danger"
            else:
                print("ERROR INFO:", alert)
                print(alert)
                exit()

            titleTag = alert.find("h2")

            if titleTag == None:
                titleTag = alert.find("h3")
                
            if titleTag == None:
                titleTag = alert.find("p", "h3")

            if titleTag:
                title = custom_text_with_links(titleTag)
                titleTag.decompose()
            else:
                title = None

            alerts.append(
                {
                    "type": alertType,
                    "title": title,
                    "description": custom_text_with_links(alert),
                }
            )
            alert.decompose()
        return alerts

    def delete_navegation(self, soup):
        nav = soup.find("nav", {"role": "navigation"})
        
        if nav:
            print("borrar nav")
            nav.decompose()

    def delete_forms(self, soup):
        for tag in soup.find_all("form"):
            print("borrar forms")
            tag.decompose()

    def delete_sections_rigth(self, soup):
        #https://www.canada.ca/en/immigration-refugees-citizenship/services/biometrics/who-needs-to-give.html
        for tag in soup.find_all("nav", "gc-subway"):
            if tag.find("dl") == None:
                print("borrar sections")
                tag.decompose()
    
    def delete_panels(self, soup):
        for tag in soup.find_all("section", "panel panel-info"):
            print("borrar panels")
            tag.decompose()

    def delete_text_invsibile(self, soup):
        tags_to_hidden = []
        for tag in soup.find_all(True):  # 'True' encuentra todos los elementos
            if tag.attrs:
                for attr, value in tag.attrs.items():
                    if "data-wb" in attr:
                        try:
                            value = json.loads(value)
                        except:
                            continue

                        if "hideelm" in value:
                            print("Borrado invisile: ", value)
                            values = value["hideelm"].split(", ")
                            
                            for x in values:
                                if x not in tags_to_hidden:
                                    tags_to_hidden.append(x)

        for tagname in tags_to_hidden:
            for tag in soup.select(tagname):
                tag.decompose()

        """for tag in soup.find_all(class_="wb-inv"):
            tag.decompose()

        for tag in soup.find_all(class_="mfp-hide"):
            tag.decompose()

        for tag in soup.find_all(class_="rslt"):
            tag.decompose()

        for tag in soup.find_all(class_="mwscolumns"):
            tag.decompose()

        for tag in soup.find_all("div", {"id": "forms"}):
            tag.decompose()
"""
    def get_text(self, page):
        response = requests.get(page)
        soup = BeautifulSoup(response.content, "html.parser").find("main", "container")

        if soup == None:
            return "", []

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        for a in soup.find_all("a"):
            href = a.get("href")

            if href:
                # Si el href es relativo, lo convertimos en absoluto usando la página principal
                if not href.startswith(("http://", "https://")):
                    href = urljoin("https://www.canada.ca", href)
                # Reemplazar el texto del enlace por "texto [href]"
                a.insert_after(f" [{href}]")

        Text = ""
        title = soup.find("h1").text.strip()
        soup.find("h1").decompose()
        Text += f"{title}\n"
        self.delete_text_invsibile(soup)
        self.delete_sections_rigth(soup)
        self.delete_forms(soup)
        self.delete_navegation(soup)
        self.delete_panels(soup)

        moreLinks = []
        for x in soup.find_all(recursive=False):
            cards = self.get_information_cards(x)
            seccions = self.get_seccions(page, x)
            alerts = self.get_alerts(x)
            panels = self.get_panels(x)
            print(cards)
            print(seccions)

            for section in seccions:
                moreLinks.append({"type": "section", "link":  section["link"]})

            for alert in alerts:
                Text += f"------------- init {alert['type']} ------------\n"
                if alert["title"]:
                    Text += f"Title: {alert['title']}\n"
                Text += f"Description: {alert['description']}\n"
                Text += f"------------- end {alert['type']} ------------\n"

            for panel in panels:
                Text += f"------------- init panel ------------\n"
                Text += f"Title: {panel['title']}\n"
                Text += f"Description: {panel['description']}\n"
                Text += f"------------- end panel ------------\n"

            for card in cards:
                if card["links"]:
                    for link in card['links']:
                        moreLinks.append({"type": "card", "link":  link})

                Text += f"""------------- init card information ------------
Title: {card["title"]}
Description: {card["text"]}
------------- end card information ------------
"""

            if isinstance(x, Comment):
                continue

            elif x.name == "section":
                break

            elif x.name == "ul":
                for li in x.find_all("li"):
                    res = custom_text_with_links(li)

                    if res:
                        Text += f"  - {res}\n"

            else:
                res = custom_text_with_links(x)
                if res:
                    Text += f"{res}\n"

        Text = remove_newlines(Text)

        with open("text.txt", "w", encoding='utf8') as fp:
            fp.write(Text)

        return Text, moreLinks

    def get_all_text(self, page_url):
        response = requests.get(page_url)
        soup = BeautifulSoup(response.content, "html.parser")
        page_type = self.get_type(soup)
        all_text = ""

        if page_type == "page":
            print("page: ", page_url)

            new_text, moreLinks = self.get_text(page_url) 
            all_text += new_text+ "\n"

            if moreLinks:
                for x in moreLinks:
                    if x["link"] in self.all_links_scraped:
                        continue
                    self.all_links_scraped.append(x["link"])

                    new_text, moreLinks = self.get_text(x["link"]) 
                    all_text += f"---------------------- new page into {x['type']} ----------------------\n"
                    all_text += self.get_all_text(x["link"]) + "\n"
                    all_text += f"---------------------- end {x['type']} ----------------------\n"


        elif page_type == "container":
            print("container: ", page_url)
            links = self.search(soup)
            for link in links:
                if link["link"] in self.all_links_scraped:
                    continue
                self.all_links_scraped.append(link["link"])

                all_text += f"---------------------- new page ----------------------\n"
                all_text += f"page title: {link['title']}\n"
                all_text += f"page description {link['description']}\n"
                all_text += f"page link {link['link']}\n"
                all_text += f"---------------------- subpages ----------------------\n"
                all_text += self.get_all_text(link['link']) + "\n"
                all_text += f"---------------------- end subpages ----------------------\n"


                with open("All_text44.txt", "w", encoding='utf8') as fp:
                    fp.write(all_text)

        return all_text



import time
if __name__ == '__main__':
    pageMain = "https://www.canada.ca/en/services/immigration-citizenship.html"
    start = time.time()
    Object = CanadaInmigration()

    #text = Object.get_text(soup)
    #with open("prueba.txt", "w", encoding='utf8') as fp:
    #    fp.write(text)
 
    #exit()
    
    All_text = Object.get_all_text(pageMain)

    with open("data.txt", "w", encoding='utf8') as fp:
        fp.write(All_text)

    print(time.time() - start)
