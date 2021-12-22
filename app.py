from flask import Flask, render_template, request, redirect
from flask_cors import CORS
from flask_caching import Cache
from PIL import Image
import requests
import io
from bs4 import BeautifulSoup
import lxml
from urllib.parse import urljoin
import json
import re
import webview

app = Flask(__name__)

# window = webview.create_window('Woah dude!', "https://www.carrefour.fr")
# webview.start()

config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}
app.config.from_mapping(config)

cache = Cache(app)

@app.route('/')
def hello():
    return redirect("/logo/ldlc.com", code=302)


@app.route('/logo/<domain>', methods=('GET', 'POST'))
@cache.cached(timeout=27)
def find_logo(domain):
    home = 'https://%s/' % (domain)  
    print(home)
    
    response = get_url_content(home)
    data = get_logos(response)
    response = app.response_class(
        response=json.dumps(data),
        mimetype='application/json'
    )
    return response




def get_param_url(path, query_string):
    if not query_string:
        return path
    return '%s?%s' % (path, query_string) 


def get_url_content(url):



    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
            # "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3"   ,
            # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"     ,
            # "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0"

            # "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

    }
    response = requests.get(url, headers=headers)
   
    return response
    

def get_image(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
    response = requests.get(url, headers=headers)
    image_bytes = io.BytesIO(response.content)
    img = Image.open(image_bytes)

    return img

def scrap_URLImages(items, attribute, type, base_url):
    if (type == "class_contains_logo"):
        print("test") 
        print(items)
    dict=[]
    for item in items:

        try:
            dict.append({ "image": {"type": type, "url": urljoin(base_url, item[attribute]) }})
        except:
            a=1
    return dict


def get_logos(response):
       
    content = response.content
    # print(content)
    url = response.url
    base_url = urljoin(url, '.')   

    arrayLogos=[]

    # content="<html><img class='logo' src='test.png' /></html>"
    soup = BeautifulSoup(content, features="html.parser")

    arrayLogos = arrayLogos + scrap_URLImages(soup.findAll("link", rel="icon"), "href" ,"url_favicon_html",        base_url )
    arrayLogos = arrayLogos + scrap_URLImages(soup.findAll("meta", property="og:logo"), "content" ,"url_og_logo",  base_url )
    arrayLogos = arrayLogos + scrap_URLImages(soup.findAll("meta", property="og:image"), "content" ,"url_og_logo", base_url )
    arrayLogos = arrayLogos + scrap_URLImages(soup.findAll("img", itemprop="logo"), "src" ,"url_schema_org",       base_url )
    arrayLogos = arrayLogos + scrap_URLImages(soup.findAll("meta", property="twitter:image"), "content" ,"url_twitter_image",       base_url )
    arrayLogos = arrayLogos + scrap_URLImages(soup.findAll("img", {"src":    re.compile(".*logo.*")}), "src" ,"url_src_contains_logo",       base_url )
    arrayLogos = arrayLogos + scrap_URLImages(soup.findAll("img", {"class" : re.compile('.*logo.*')}), "src" ,"class_contains_logo",       base_url )
    arrayLogos = arrayLogos + scrap_URLImages(soup.findAll("svg", {"class" : re.compile('.*logo.*')}), "src" ,"svg_class_contains_logo",       base_url )
    arrayLogos = arrayLogos + scrap_URLImages(soup.findAll("link", rel="apple-touch-icon"), "href", "apple-touch-icon",  base_url)
 

    url_manifest = soup.find("link", rel="manifest")
    if url_manifest:
        # print("manifest ! ", urljoin(base_url, url_manifest['href']))
        response_manifest = get_url_content(urljoin(base_url, url_manifest['href']))
        js = json.loads(response_manifest.content)
        print(js["icons"])
        for icon in js["icons"]:
            print(icon["src"])
            arrayLogos.append({ "image": {"type": "url_manifest_image",  "url": urljoin(base_url,icon["src"]) }})


    for item in soup.findAll("link", type="application/rss+xml"):
        try:
            response_rss = get_url_content(urljoin(base_url, item['href']))
            soup_rss = BeautifulSoup(response_rss.content, 'lxml')
            channel = soup_rss.find("channel")
            image = channel.find("image")
            url_rss_image = image.find("url").text
            arrayLogos.append({ "image": {"type": "url_rss_image",  "url": url_rss_image }})
        except:
            a=1

    for item in soup.findAll('script', {'type':'application/ld+json'}):

            tab_json=[]
            # print(item)
            try:
                x = json.loads("".join(item.contents))

                if type(x) == list:                 # un script json-ld peut contenir un array de json-ld
                    for item in x:
                        tab_json.append(item)
                else:
                    tab_json.append(x)

                for item in tab_json:
                    if "logo" in item:
                        arrayLogos.append({ "image": {"type": "url_json_ld_logo", "url": x['logo']}})
            except:
                a=1


    for img in soup.findAll("img"):
        blnHasLogoClassNameInParents = False
        for img_parents in img.find_parents():
            if img_parents.has_attr('class') and "logo" in img_parents.get("class"):
                    blnHasLogoClassNameInParents = True
        if blnHasLogoClassNameInParents:
            arrayLogos.append({ "image": {"type": "url_class_logo_in_parents", "url": urljoin(base_url,img["src"]) }})    


    return arrayLogos