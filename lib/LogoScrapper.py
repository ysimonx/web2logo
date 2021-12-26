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

import base64
import operator


# from utils import fix_links, getBaseFromUrl, getTextContents, getFullText, getTestPath






class LogoScrapper:
    def __init__(self):
    
        self.useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
 



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
        

    def get_image(self, url):
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


    def scrap_URLImages(self, items, attribute, type, base_url):
        
        dict=[]
        for item in items:

            try:
                dict.append({ "image": {"type": type, "url": urljoin(base_url, item[attribute]) }})
            except:
                a=1
        return dict


    def get_logos(self,response):
        
        content = response.content
        # print(content)
        url = response.url
        base_url = urljoin(url, '.')   

        arrayLogos=[]

        # content="<html><img class='logo' src='test.png' /></html>"
        soup = BeautifulSoup(content, features="html.parser")

        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("link", rel="icon"), "href" ,"url_favicon_html",        base_url )
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("meta", property="og:logo"), "content" ,"url_og_logo",  base_url )
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("meta", property="og:image"), "content" ,"url_og_image", base_url )
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("img", itemprop="logo"), "src" ,"url_schema_org",       base_url )
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("meta", property="twitter:image"), "content" ,"url_twitter_image",       base_url )
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("img", {"src":    re.compile("(?i).*logo.*")}), "src" ,"url_src_contains_logo",       base_url )
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("img", {"class" : re.compile('(?i).*logo.*')}), "src" ,"class_contains_logo",       base_url )
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("svg", {"class" : re.compile('(?i).*logo.*')}), "src" ,"svg_class_contains_logo",       base_url )
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("link", rel="apple-touch-icon"), "href", "apple-touch-icon",  base_url)
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("img", {"alt" : re.compile('(?i).*logo.*')}), "src", "alt_contains_logo",  base_url)
        arrayLogos = arrayLogos + self.scrap_URLImages(soup.findAll("img", {"alt" : re.compile('(?i).*logo.*')}), "src", "alt_contains_logo",  base_url)


        url_manifest = soup.find("link", rel="manifest")
        if url_manifest:
            # print("manifest ! ", urljoin(base_url, url_manifest['href']))
            response_manifest = self.get_url_content(urljoin(base_url, url_manifest['href']))
            js = json.loads(response_manifest.content)
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

        for item in soup.findAll('script', {'type':'application/ld+json'}):

                tab_json=[]
                print(item)
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
            blnHasAHeaderTagInParents = False
            blnHasALinkInParents = False

            if img.has_attr('src'):
                for img_parents in img.find_parents():
                    if img_parents.has_attr('class') and "logo" in img_parents.get("class"):
                            blnHasLogoClassNameInParents = True
                    if img_parents.name == "header":
                            blnHasAHeaderTagInParents = True
                    if img_parents.name == "a":
                        if img_parents.has_attr('href') and  urljoin(base_url,img_parents["href"  ])  == base_url :
                            print("url parent = " + urljoin(base_url,img_parents["href"  ]) + " vs " + base_url)
                            blnHasALinkInParents = True
                        
                if blnHasLogoClassNameInParents:
                    arrayLogos.append({ "image": {"type": "url_class_logo_in_parents", "url": urljoin(base_url,img["src"]) }})    

                if blnHasAHeaderTagInParents:
                    arrayLogos.append({ "image": {"type": "url_has_header_in_parents", "url": urljoin(base_url,img["src"]) }})  

                if blnHasALinkInParents:
                    arrayLogos.append({ "image": {"type": "url_has_link_in_parents", "url": urljoin(base_url,img["src"]) }})  



        return arrayLogos

    def getDownloads(self, arrayLogos):
        result_size = {}

        result= []
        for item in arrayLogos:
            item_image = item["image"]
            if item_image:
                try:
                    url = item_image["url"]
                    print(url)
                    if url.startswith("data:"):
                        contentbase64= re.sub("data:image\/[^,]+,","",url)
                        print(contentbase64)
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

        return result

    def getScores(self, arrayLogos):
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
            "url_has_header_in_parents": 1,
            "url_has_link_in_parents": 1
        }
        
        for item in arrayLogos:
            print(" ")
            print("-----------------")
            image = item["image"]
                
            if image:
                score = scores[image["type"]]
                url = image["url"]
                print(image["type"], image["url"], score)
                if url in result_scores:
                    result_scores[url] = result_scores[url] + score * 10
                    result_rules[url]= result_rules[url] + " | " + image["type"] + " (+" + str(score) + ")"

                else:
                    result_scores[url] = score * 10
                    result_rules[url] = image["type"] + " (+" + str(score) + ")"

        print(" ")
        print(result_scores)

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
            if item["width"] and item["height"]:
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
                
            result_pondere.append(item)

        # tri desc
        result_scores_sorted = sorted(result_pondere, key=operator.itemgetter("score"), reverse=True)

        return result_scores_sorted
