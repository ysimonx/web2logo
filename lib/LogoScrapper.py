#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import requests
from urllib.parse import urljoin
import json

import io
from bs4 import BeautifulSoup

from   urllib.parse   import urlencode
from   urllib.request import Request
import json

from PIL import Image
from io import BytesIO

from cairosvg import svg2png


import base64
import operator


# from utils import fix_links, getBaseFromUrl, getTextContents, getFullText, getTestPath






class LogoScrapper:
    def __init__(self):
    
        self.useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
 
    def get_logos(self,page):
        response         = self.get_url_content(page)
        logos            = self.get_logos_from_response(response)
        # print(logos)
        logos_downloaded = self.download_logos(logos)
        logos_scored     = self.compute_scores(logos_downloaded)
        return logos_scored



    def get_url_content(self, url):



        headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
                # "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3"   ,
                # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"     ,
                # "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0"

                # "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

        }
        response = requests.get(url, headers=headers)

        return response
        
    def convert_svgtag_to_image(self, text):
        try:
            svgsoup = BeautifulSoup(text, features="html.parser")
            svg = svgsoup.find("svg")
            if svg.has_attr("viewbox"):
                viewbox = svg["viewbox"]
                x0,y0,x1,y1 = viewbox.split(" ")
            else:
                if svg.has_attr("height") and svg.has_attr("width"):
                    x0=0
                    y0=0
                    x1=int(svg["width"])
                    y1=int(svg["height"])
            png = svg2png(bytestring=bytes(text, 'utf-8'),parent_width=int(x1)-int(x0), parent_height=int(y1)-int(y0))
            pil_img = Image.open(BytesIO(png))
            return pil_img
        except:
            return None

    def get_image(self, url):
        # print(" - - - - - - - - - - - -")
        # print("url image = " + url )
        if url.startswith('<svg'):
            return self.convert_svgtag_to_image(url)

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
        try:
            response = requests.get(url, headers=headers)
        except:
            return None

        # print(response.status_code)
        if response.status_code == 200:
            if ('<svg' in str(response.content)):
                 return self.convert_svgtag_to_image(response.content)

            image_bytes = io.BytesIO(response.content)
            try:
                img = Image.open(image_bytes)
                return img
            except: 
                print("erreur sur chargement image ", url)
                print(response.content)
                return None
        
        else:
            return None


    def scrap_URLImages(self, items, attribute, type, base_url):
        
        dict=[]
        for item in items:

            try:
                if item.has_attr(attribute):
                    dict.append({ "image": {"type": type, "url": urljoin(base_url, item[attribute]) }})
                else:
                    dict.append({ "image": {"type": type, "url": str(item) }})
            except:
                a=1
        return dict


    def get_logos_from_response(self,response):
        
        content = response.content
        # print(content)
        url = response.url
        base_url = urljoin(url, '.')   

        arrayLogos=[]

        # content="<html><img class='logo' src='test.png' /></html>"
        soup = BeautifulSoup(content, features="html.parser")

        # balises SEO
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("link", rel="icon"), "href" ,"url_favicon_html",        base_url )
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("link", rel="apple-touch-icon"), "href", "apple-touch-icon",  base_url)
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("meta", property="og:logo"), "content" ,"url_og_logo",  base_url )
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("meta", property="og:image"), "content" ,"url_og_image", base_url )
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("meta", property="twitter:image"), "content" ,"url_twitter_image",       base_url )

        # img et/ou svg

        tags_images =["img", "svg"]
        for tag in tags_images:
            arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll(tag, {"src":    re.compile("(?i).*logo.*")}), "src" ,"url_src_contains_logo",       base_url )
            arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll(tag, {"class" : re.compile('(?i).*logo.*')}), "src" ,"class_contains_logo",       base_url )
            arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll(tag, {"alt" : re.compile('(?i).*logo.*')}),   "src", "alt_contains_logo",  base_url)
            arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll(tag, itemprop="logo"),                        "src" ,"url_schema_org",       base_url )
        


            for img in soup.findAll(tag):
                blnHasLogoClassNameInParents = False
                blnHasAHeaderTagInParents = False
                blnHasALinkInParents = False
                blnHasALinkInParentsWithLogoInTitle = False
                blnHasAParentWithLogoInId = False
                
                if img.has_attr('src'):
                    for img_parents in img.find_parents():
                        if img_parents.has_attr('class') and "logo" in str(img_parents.get("class")).lower():
                                blnHasLogoClassNameInParents = True
                        if img_parents.name == "header":
                                blnHasAHeaderTagInParents = True
                        if img_parents.has_attr('id') and "logo" in str(img_parents.get("id")).lower():
                                blnHasAParentWithLogoInId = True
                        if img_parents.name == "a":
                            if img_parents.has_attr('href') and (
                                urljoin(base_url,img_parents["href"  ])  == base_url
                                or urljoin(base_url,img_parents["href"])  == base_url + "/home"
                                or urljoin(base_url,img_parents["href"])  == base_url + "/home.html"
                            ) :
                                # print("url parent = " + urljoin(base_url,img_parents["href"  ]) + " vs " + base_url)
                                blnHasALinkInParents = True
                                if img_parents.has_attr('title') and "logo" in str(img_parents["title"]).lower():
                                    blnHasALinkInParentsWithLogoInTitle = True
                            
                    if blnHasLogoClassNameInParents:
                        arrayLogos.append({ "image": {"type": "url_class_logo_in_parents", "url": urljoin(base_url,img["src"]) }})    

                    if blnHasAHeaderTagInParents:
                        arrayLogos.append({ "image": {"type": "url_has_header_in_parents", "url": urljoin(base_url,img["src"]) }})  

                    if blnHasALinkInParents:
                        arrayLogos.append({ "image": {"type": "url_has_link_in_parents", "url": urljoin(base_url,img["src"]) }})  

                    if blnHasALinkInParentsWithLogoInTitle:
                        arrayLogos.append({ "image": {"type": "url_has_link_in_parents_with_logo_in_title", "url": urljoin(base_url,img["src"]) }})  

                    if blnHasAParentWithLogoInId:
                        arrayLogos.append({ "image": {"type": "url_has_a_parents_with_logo_in_id", "url": urljoin(base_url,img["src"]) }})  

                else:
                    arrayLogos.append({ "image": {"type": "inline_image",  "url": str(img) }})


        # fichiers externes

        url_manifest = soup.find("link", rel="manifest")
        if url_manifest:
            # print("manifest ! ", urljoin(base_url, url_manifest['href']))
            response_manifest = self.get_url_content(urljoin(base_url, url_manifest['href']))
            js = json.loads(response_manifest.content)
            if "icons" in js:
                for icon in js["icons"]:
                    arrayLogos.append({ "image": {"type": "url_manifest_image",  "url": urljoin(base_url,icon["src"]) }})


        for item in soup.findAll("link", type="application/rss+xml"):
            try:
                response_rss = self.get_url_content(urljoin(base_url, item['href']))
                soup_rss = BeautifulSoup(response_rss.content, 'lxml')
                channel = soup_rss.find("channel")
                image = channel.find("image")
                url_rss_image = image.find("url").text
                arrayLogos.append({ "image": {"type": "url_rss_image",  "url": url_rss_image }})
            except:
                a=1


        # json-ld
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




        return arrayLogos

    def download_logos(self, arrayLogos):
        result_size = {}

        # print(arrayLogos)

        result= []
        for item in arrayLogos:
            item_image = item["image"]
            if item_image:
                try:
                    url = item_image["url"]
                    # print("url >", url)
                    if url == None:
                        print("none")
                    
                    if url.startswith("data:"):
                        contentbase64= re.sub("data:image\/[^,]+,","",url)
                        # print(contentbase64)
                        image_downloaded = Image.open(BytesIO(base64.b64decode(contentbase64)))
                    else:
                        image_downloaded = self.get_image(url)

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

                if "<svg" in url:
                    item["is_svg"] = True
                    
                result.append(item)
                

        return result

    def compute_scores(self, arrayLogos):
        result_scores= {}
        result_rules= {}

        scores = {
            "url_class_logo_in_parents": 3,
            "url_json_ld_logo": 10,
            "url_manifest_image": 5,
            "apple-touch-icon": 4,
            "url_src_contains_logo": 2,
            "url_og_image": 2,
            "url_og_logo": 10,
            "url_favicon_html": 3,
            "class_contains_logo": 3, 
            "url_rss_image": 5,
            "url_twitter_image":8,
            "alt_contains_logo": 5,
            "url_has_link_in_parents_with_logo_in_title":5,
            "url_has_a_parents_with_logo_in_id": 5,
            "url_has_header_in_parents": 1,
            "url_has_link_in_parents": 1,
            "inline_image": 1
        }
        
        for item in arrayLogos:

            image = item["image"]
                
            if image:
                score = scores[image["type"]]
                url = image["url"]
                # print(image["type"], image["url"], score)
                if url in result_scores and not image["type"] in result_rules[url]:
                    result_scores[url] = result_scores[url] + score * 10
                    result_rules[url]= result_rules[url] + " | " + image["type"] + " (+" + str(score) + ")"
                    
                else:
                    result_scores[url] = score * 10
                    result_rules[url] = image["type"] + " (+" + str(score) + ")"

        # print(" ")
        # print(result_scores)

        # dedoublonne
        result_dict= dict()
        for item in arrayLogos:
            image = item["image"]
            if image:
                url = image["url"]
                item["score"] =  result_scores[url]
                item["score_rules"] = result_rules[url]
            result_dict[url] = item
        result=[]
        for key in result_dict:
            result.append(result_dict[key])

        # pondere score en fonction des dimensions
        result_pondere = []
        for item in result:
            
            if "width" in item and "height" in item and not "is_svg" in item:
                if item["width"]<80 or item["height"]<80:
                    item["score"] = item["score"] / 2
                    item["score_rules"]= item["score_rules"] + " | " + "/2 because < 80px "
                if item["width"]>130 or item["height"]>130:
                    item["score"] = item["score"] * 2
                    item["score_rules"]= item["score_rules"]   + " | " + "*2 because > 130px "
                if item["width"]>300 or item["height"]>300:
                    item["score"] = item["score"] * 2
                    item["score_rules"]= item["score_rules"] + " | " + "*2 because > 300px "
            else:
                score = 0

            if "is_svg" in item and len(item["image"]["url"]) > 6000:
                item["score"] = item["score"] * 4
                item["score_rules"]= item["score_rules"] + " | " + "*4 because is_svg "
                print(item)
            result_pondere.append(item)

        # tri desc
        result_scores_sorted = sorted(result_pondere, key=operator.itemgetter("score"), reverse=True)

        return result_scores_sorted
