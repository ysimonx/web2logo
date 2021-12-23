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
import operator
import base64
from io import BytesIO

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
@cache.cached(timeout=10)
def find_logo(domain):
    home = 'https://%s/' % (domain)  
    
    #print(home)
    
    response = get_url_content(home)

    logos = get_logos(response)
    
    logos_downloaded = getDownloads(logos)

    logos_scored = getScores(logos_downloaded)

    

    if len(logos_scored) > 0:
        print(logos_scored[0])
        if not request.args.get('debug'): 
            return redirect(logos_scored[0]["image"]["url"], code=302)

    result= {
        "logo": logos_scored[0]["image"]["url"],
        "logos_details": logos,
        "logos_scores": logos_scored
        
    }
    response = app.response_class(
        response=json.dumps(result),
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
    print("url image = " + url )
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        image_bytes = io.BytesIO(response.content)
        try:
            img = Image.open(image_bytes)
        except:
            print("erreur sur chargement image ", url)
            return None
        # print(img)
        return img
    else:
        return None

def scrap_URLImages(items, attribute, type, base_url):
       
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
        for icon in js["icons"]:
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

def getDownloads(arrayLogos):
    result_size = {}

    result= []
    for item in arrayLogos:
        item_image = item["image"]
        if item_image:
            try:
                url = item_image["url"]
                print(url)
                if url.startswith("data:"):
                    contentbase64= re.sub("data:image\/gif,","",url)
                    print(contentbase64)
                    image_downloaded = Image.open(BytesIO(base64.b64decode(contentbase64)))
                else:
                    image_downloaded = get_image(url)

                if (image_downloaded):
                    result_size[url] = image_downloaded.size
            except:
                a=1

    
    for item in arrayLogos:
        item_image = item["image"]
        if item_image:
            url = item_image["url"]
            if url in result_size:
                 width, height = result_size[url]
                 item["width"] = width
                 item["height"] = height
                 result.append(item)

    return result

def getScores(arrayLogos):
    result_scores= {}

    scores = {
        "url_class_logo_in_parents": 1,
        "url_json_ld_logo": 10,
        "url_manifest_image": 5,
        "apple-touch-icon": 3,
        "url_src_contains_logo": 2,
        "url_og_logo": 4,
        "url_favicon_html": 2,
        "class_contains_logo": 3, 
        "url_rss_image": 5
    }
    
    for item in arrayLogos:
        image = item["image"]
            
        if image:
            score = scores[image["type"]]
            url = image["url"]

            if url in result_scores:
                result_scores[url] = result_scores[url] + score
            else:
                result_scores[url] = score

    

    # dedoublonne
    result_dict= dict()
    for item in arrayLogos:
        image = item["image"]
        if image:
            url = image["url"]
            item["score"] =  result_scores[url]
        result_dict[url] = item
    result=[]
    for key in result_dict:
        result.append(result_dict[key])

    # pondere score en fonction des dimensions
    result_pondere = []
    for item in result:
        if item["width"] and item["height"]:
            if item["width"]<80 or item["height"]<80:
                item["score"] = item["score"] / 2
            if item["width"]>130 and item["height"]>130:
                item["score"] = item["score"] * 2
            if item["width"]>400 and item["height"]>400:
                item["score"] = item["score"] * 2
        else:
            score = 0
            
        result_pondere.append(item)

    # tri desc
    result_scores_sorted = sorted(result_pondere, key=operator.itemgetter("score"), reverse=True)

    return result_scores_sorted
