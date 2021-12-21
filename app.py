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

app = Flask(__name__)

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
    home = 'https://%s' % (domain)  
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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
    response = requests.get(url, headers=headers)
   
    return response
    

def get_image(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
    response = requests.get(url, headers=headers)
    image_bytes = io.BytesIO(response.content)
    img = Image.open(image_bytes)

    return img

def get_logos(response):
       
    content = response.content
    # print(content)
    url = response.url
    base_url = urljoin(url, '.')   

    dict=[]

    soup = BeautifulSoup(content, features="html.parser")

    url_manifest = soup.find("link", rel="manifest")
    if url_manifest:
        # print("manifest ! ", urljoin(base_url, url_manifest['href']))
        response_manifest = get_url_content(urljoin(base_url, url_manifest['href']))
        # print(response_manifest.content)


    url_rss_image = None
    for item in soup.findAll("link", type="application/rss+xml"):
        try:
            response_rss = get_url_content(urljoin(base_url, item['href']))
            soup_rss = BeautifulSoup(response_rss.content, 'lxml')
            channel = soup_rss.find("channel")
            image = channel.find("image")
            url_rss_image = image.find("url").text
            dict.append({ "image": {"type": "url_rss_image",  "url": url_rss_image }})
        except:
            a=1

    url_json_ld_logo = None
    for item in soup.findAll('script', {'type':'application/ld+json'}):
            try:
                x = json.loads("".join(item.contents))
                if "logo" in x:
                    dict.append({ "image": {"type": "url_json_ld_logo", "url": x['logo']}})
            except:
                a=1

    url_og_logo = soup.find("meta", property="og:logo")
    if url_og_logo and url_og_logo.has_attr("src"):
        dict.append({ "image": {"type": "url_og_logo", "url": urljoin(base_url, url_og_logo['src']) }})


    url_twitter_image = soup.find("meta", property="twitter:image")
    if url_twitter_image  and url_twitter_image.has_attr("src"):
        dict.append({ "image": {"type": "url_twitter_image", "url": urljoin(base_url, url_twitter_image['content']) }})


    url_schema_org = soup.find("img", itemprop="logo")
    if url_schema_org  and url_schema_org.has_attr("src"):
        dict.append({ "image": {"type": "url_schema_org",  "url":urljoin(base_url, url_schema_org['src']) }})

    for p in soup.find_all('svg'):
        for c in p.get_attribute_list('class'):
            if c:
                if "logo" in c:
                    s=""
                    for child in p.children:
                        s=s+str(child)
                    dict.append({ "image": {"type": "url_logo_in_svg", "content": s }})




    for p in soup.find_all('img'):
        try:
            if "logo" in p['src']:
                dict.append({ "image": {"type": "url_logo_in_src", "url":urljoin(base_url, p['src']) }})
        except KeyError:
            a=1


        try:
            if "logo" in p['data-src']:
                dict.append({ "image": {"type": "url_logo_in_data_src", "url":urljoin(base_url, p['data-src']) }})
        except KeyError:
            a=1
    
        try:
            if "logo" in p['class']:
                dict.append({ "image": {"type": "url_class_logo", "url":urljoin(base_url, p['src']) }})
        except KeyError:
            a=1    


    for item in soup.findAll("meta", property="og:image"):
            try:
                 dict.append({ "image": {"type": "url_og_image", "url": urljoin(base_url, item['content']) }})
            except:
                a=1


    return dict