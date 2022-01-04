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

from .Logo import Logo
from .Logos import Logos


class LogoScrapper:

    def __init__(self):
        self.useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
        self.last_error = None
        self.last_image_error = None
        self.last_url = None
        

    def getLogosFromPage(self,page):
        self.last_url = None
        response         = self.getHTTPResponse(page)
        logos           = self.extractLogosFromHTTPResponse(response)
        logos.download()
        logos.computeScore()

        return logos


    def getHTTPResponse(self, url):

        headers = {
                "User-Agent": self.useragent
        }
        try:
            response = requests.get(url, headers=headers)
            return response
        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            self.last_error = "requests.exceptions.Timeout"
        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            self.last_error = "requests.exceptions.TooManyRedirects"
        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            self.last_error = "requests.exceptions.RequestException"
            
        return None
        

    def extractLogosFromHTTPResponse(self,response):
       
        arrayLogos = Logos()

        if response == None:
            return arrayLogos

        content         = response.content   
        self.last_url   = response.url
        base_url        = urljoin(self.last_url , '.')   

        # content="<html><img class='logo' src='test.png' /></html>"
        soup = BeautifulSoup(content, features="html.parser")

        # balises SEO
        
        arrayLogos = self.appendLogosFromBS4Nodes(arrayLogos,   soup.findAll("link", rel="icon") ,"url_favicon_html",  base_url )
        arrayLogos = self.appendLogosFromBS4Nodes(arrayLogos,   soup.findAll("link", rel="icon") ,"url_favicon_html",  base_url )
        arrayLogos = self.appendLogosFromBS4Nodes(arrayLogos,   soup.findAll("link", rel="apple-touch-icon") ,"apple-touch-icon",  base_url )
        arrayLogos = self.appendLogosFromBS4Nodes(arrayLogos,   soup.findAll("meta", property="og:logo") ,"url_og_logo",  base_url )
        arrayLogos = self.appendLogosFromBS4Nodes(arrayLogos,   soup.findAll("meta", property="og:image"),"url_og_image",  base_url )
        arrayLogos = self.appendLogosFromBS4Nodes(arrayLogos,   soup.findAll("meta", property="twitter:image"),"url_twitter_image",  base_url )

        # img et/ou svg

        tags_images =["img", "svg"]
        for tag in tags_images:
        
            arrayLogos = self.appendLogosFromBS4Nodes(arrayLogos,   soup.findAll(tag, {"src":    re.compile("(?i).*logo.*")}) ,"url_src_contains_logo",  base_url )
            arrayLogos = self.appendLogosFromBS4Nodes(arrayLogos,   soup.findAll(tag, {"class" : re.compile('(?i).*logo.*')}) ,"class_contains_logo",  base_url )
            arrayLogos = self.appendLogosFromBS4Nodes(arrayLogos,   soup.findAll(tag, {"alt" : re.compile('(?i).*logo.*')})   ,"alt_contains_logo",  base_url )
            arrayLogos = self.appendLogosFromBS4Nodes(arrayLogos,   soup.findAll(tag, itemprop="logo")                        ,"url_schema_org",  base_url )


            for img in soup.findAll(tag):
                for img_parents in img.find_parents():
                    if img_parents.has_attr('class') and "logo" in str(img_parents.get("class")).lower():
                            arrayLogos.append(Logo("url_class_logo_in_parents", str(img), base_url))
                    if img_parents.name == "header":
                            arrayLogos.append(Logo("url_has_header_in_parents", str(img), base_url))
                    if img_parents.has_attr('id') and "logo" in str(img_parents.get("id")).lower():
                            arrayLogos.append(Logo("url_has_a_parents_with_logo_in_id", str(img), base_url))
                    if img_parents.name == "a":
                        if img_parents.has_attr('href'):
                            # print("url parent = " + urljoin(base_url,img_parents["href"  ]) + " vs " + base_url)
                            # blnHasALinkInParents = True
                            
                            if img_parents.has_attr('title') and (
                                    "logo" in str(img_parents["title"]).lower()
                                or 
                                    "homepage" in str(img_parents["title"]).lower()
                                    or 
                                    "accueil" in str(img_parents["title"]).lower()
                                ):
                                arrayLogos.append(Logo("url_has_link_in_parents_with_logo_in_title", str(img), base_url))

                        if img_parents.has_attr('href') and (
                            urljoin(base_url,img_parents["href"  ])  == base_url
                            or urljoin(base_url,img_parents["href"])  == base_url + "/home"
                            or urljoin(base_url,img_parents["href"])  == base_url + "/home.html"
                            or urljoin(base_url,img_parents["href"])  == base_url + "/index.html"
                            or urljoin(base_url,img_parents["href"])  == base_url + "/index.php"
                        ) :
                            # print("url parent = " + urljoin(base_url,img_parents["href"  ]) + " vs " + base_url)
                            arrayLogos.append(Logo("url_has_link_in_parent_to_home", str(img), base_url))
                        
        

        # fichiers externes

        url_manifest = soup.find("link", rel="manifest")
        if url_manifest:
            # print("manifest ! ", urljoin(base_url, url_manifest['href']))
            response_manifest = self.getHTTPResponse(urljoin(base_url, url_manifest['href']))
            js = json.loads(response_manifest.content)
            if "icons" in js:
                for icon in js["icons"]:
                    arrayLogos.append(Logo("url_manifest_image", urljoin(base_url,icon["src"]), base_url))

        for item in soup.findAll("link", type="application/rss+xml"):
            try:
                response_rss = self.getHTTPResponse(urljoin(base_url, item['href']))
                soup_rss = BeautifulSoup(response_rss.content, 'lxml')
                channel = soup_rss.find("channel")
                image = channel.find("image")
                url_rss_image = image.find("url").text
                arrayLogos.append(Logo("url_rss_image", url_rss_image, base_url))
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
                            arrayLogos.append(Logo("url_json_ld_logo", str(item['logo']), base_url))
                except:
                    a=1


        return arrayLogos

    def appendLogosFromBS4Nodes(self, logos, nodes, type, base_url):
        
        for node in nodes:
            try:
                logo = Logo(type, str(node), base_url)
                logos.append(logo)
            except:
                a=1
                
        return logos

