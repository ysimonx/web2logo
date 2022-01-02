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


class LogoScrapper:

    def __init__(self):
        self.useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
        self.last_error = None
        self.last_image_error = None
        self.last_url = None

    def getLogosFromPage(self,page):
        self.last_url = None
        response         = self.getHTTPResponse(page)
        logos            = self.extractLogosFromHTTPResponse(response)
        logos2           = self.extractLogosFromHTTPResponse2(response)
        for logo in logos2:
            print(logo.to_JSON())
        # print(logos)

        logos_downloaded = self.download_logos(logos)
        logos_scored     = self.compute_scores(logos_downloaded)
        return logos_scored



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
        
    def getImageFromTag(self, url):
        # print(" - - - - - - - - - - - -")
        # print("url image = " + url )
        if url.startswith('<svg'):
            return self.convertSVGtoImage(url)

        headers = {
            "User-Agent":self.useragent
        }
        
        try:
            response = requests.get(url, headers=headers)
            # print (response.status_code)
            if response.status_code == 200:
                if ('<svg' in str(response.content)):
                    # print("contains svg xml")
                    # print(response.content)
                    return self.convertSVGtoImage(response.content)

                image_bytes = io.BytesIO(response.content)
                img = Image.open(image_bytes)
                return img
        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            self.last_image_error = "requests.exceptions.Timeout"
        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            self.last_image_error = "requests.exceptions.TooManyRedirects"
        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            self.last_image_error = "requests.exceptions.RequestException : %s" % (e) 
            
        return None

    
    def convertSVGtoImage(self, text):
        try:
            svgsoup = BeautifulSoup(text, features="html.parser")
            svg = svgsoup.find("svg")
            if svg.has_attr("viewbox"):
                viewbox = svg["viewbox"]
                x0,y0,x1,y1 = viewbox.split(" ")
                x0 =int(float(x0))                  # peut etre "100.32" -> float 100.32 -> int 100
                y0 = int(float(y0))
                x1 = int(float(x1))
                y1 = int(float(y1))

            else:
                if svg.has_attr("height") and svg.has_attr("width"):
                    x0=0
                    y0=0
                    x1=int(float(svg["width"]))
                    y1=int(float(svg["height"]))

            if isinstance(text, bytes): # cf : https://stackoverflow.com/questions/39778978/how-to-identify-a-string-as-being-a-byte-literal
               
                png = svg2png(text, parent_width=int(x1)-int(x0), parent_height=int(y1)-int(y0))
                
            else:
               
                png = svg2png(bytestring=bytes(text, 'utf-8'),parent_width=int(x1)-int(x0), parent_height=int(y1)-int(y0))

            pil_img = Image.open(BytesIO(png))


            new_image = Image.new("RGBA", pil_img.size, "#808080") # Create a white rgba background
            new_image.paste(pil_img, (0, 0), pil_img)              # Paste the image on the background. Go to the links given below for details.
            new_image.convert('RGB').save('test.jpg', "JPEG")  # Save as JPEG

            return new_image
        except:
            return None

 

    def extractURLImageFromBS4Nodes(self, nodes, attribute, type, base_url):
        
        dict=[]
        for node in nodes:

            try:
                if node.has_attr(attribute): # ex : "src"
                    
                    dict.append({ "image": {"type": type, "url": urljoin(base_url, node[attribute]), "tag":str(node) }})
                    if "logo" in node[attribute].lower():
                        dict.append({ "image": {"type": "url_src_contains_logo", "url": urljoin(base_url, node[attribute]), "tag":str(node) }})
                        
                else:
                    dict.append({ "image": {"type": type, "url": str(node), "tag":str(node) }})
            except:
                a=1
                
        return dict


    def extractLogosFromBS4Nodes(self, nodes, type, base_url):
        dict=[]
        for node in nodes:
            try:
                logo = Logo(type, str(node), base_url)
                dict.append(logo)
            except:
                a=1
                
        return dict


    def extractLogosFromHTTPResponse(self,response):
        
        arrayLogos=[]
      
        if response == None:
            return arrayLogos

        content = response.content
        # print(content)
        url = response.url
        base_url = urljoin(url, '.')   

        self.last_url = url

        # content="<html><img class='logo' src='test.png' /></html>"
        soup = BeautifulSoup(content, features="html.parser")

        # balises SEO
        arrayLogos = arrayLogos + self.extractURLImageFromBS4Nodes(soup.findAll("link", rel="icon"), "href" ,"url_favicon_html",        base_url )
        arrayLogos = arrayLogos + self.extractURLImageFromBS4Nodes(soup.findAll("link", rel="apple-touch-icon"), "href", "apple-touch-icon",  base_url)
        arrayLogos = arrayLogos + self.extractURLImageFromBS4Nodes(soup.findAll("meta", property="og:logo"), "content" ,"url_og_logo",  base_url )
        arrayLogos = arrayLogos + self.extractURLImageFromBS4Nodes(soup.findAll("meta", property="og:image"), "content" ,"url_og_image", base_url )
        arrayLogos = arrayLogos + self.extractURLImageFromBS4Nodes(soup.findAll("meta", property="twitter:image"), "content" ,"url_twitter_image",       base_url )

      
        # img et/ou svg

        tags_images =["img", "svg"]
        for tag in tags_images:
            arrayLogos = arrayLogos + self.extractURLImageFromBS4Nodes(soup.findAll(tag, {"src":    re.compile("(?i).*logo.*")}), "src" ,"url_src_contains_logo",       base_url )
            arrayLogos = arrayLogos + self.extractURLImageFromBS4Nodes(soup.findAll(tag, {"class" : re.compile('(?i).*logo.*')}), "src" ,"class_contains_logo",       base_url )
            arrayLogos = arrayLogos + self.extractURLImageFromBS4Nodes(soup.findAll(tag, {"alt" : re.compile('(?i).*logo.*')}),   "src", "alt_contains_logo",  base_url)
            arrayLogos = arrayLogos + self.extractURLImageFromBS4Nodes(soup.findAll(tag, itemprop="logo"),                        "src" ,"url_schema_org",       base_url )
        

      

            for img in soup.findAll(tag):
                blnHasLogoClassNameInParents = False
                blnHasAHeaderTagInParents = False
                blnHasALinkInParents = False
                blnHasALinkInParentsWithLogoInTitle = False
                blnHasAParentWithLogoInId = False
                blnHasALinkInParentsToHome = False
                
                #if img.has_attr('src'):
                for img_parents in img.find_parents():
                    if img_parents.has_attr('class') and "logo" in str(img_parents.get("class")).lower():
                            # print(str(img_parents.get("class")).lower())
                            blnHasLogoClassNameInParents = True
                    if img_parents.name == "header":
                            blnHasAHeaderTagInParents = True
                    if img_parents.has_attr('id') and "logo" in str(img_parents.get("id")).lower():
                            blnHasAParentWithLogoInId = True
                    if img_parents.name == "a":
                        # print(img_parents)
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
                                #print("accueil ")
                                blnHasALinkInParentsWithLogoInTitle = True
      
                        if img_parents.has_attr('href') and (
                            urljoin(base_url,img_parents["href"  ])  == base_url
                            or urljoin(base_url,img_parents["href"])  == base_url + "/home"
                            or urljoin(base_url,img_parents["href"])  == base_url + "/home.html"
                            or urljoin(base_url,img_parents["href"])  == base_url + "/index.html"
                            or urljoin(base_url,img_parents["href"])  == base_url + "/index.php"
                        ) :
                            # print("url parent = " + urljoin(base_url,img_parents["href"  ]) + " vs " + base_url)
                            blnHasALinkInParentsToHome = True
                        
                if img.has_attr("src"):
                    reference = urljoin(base_url,img["src"])
                else:
                    reference = str(img)

                # print("---------------- ")
                # print(reference)
                # print(type(reference))

                if blnHasLogoClassNameInParents:
                    arrayLogos.append({ "image": {"type": "url_class_logo_in_parents", "url": reference, "tag": str(img) }})    
                    
                if blnHasAHeaderTagInParents:
                    arrayLogos.append({ "image": {"type": "url_has_header_in_parents", "url": reference, "tag": str(img) }})  

                if blnHasALinkInParents:
                    arrayLogos.append({ "image": {"type": "url_has_link_in_parents", "url": reference, "tag": str(img)}})  

                if blnHasALinkInParentsWithLogoInTitle:
                    arrayLogos.append({ "image": {"type": "url_has_link_in_parents_with_logo_in_title", "url": reference, "tag": str(img) }})  

                if blnHasAParentWithLogoInId:
                    arrayLogos.append({ "image": {"type": "url_has_a_parents_with_logo_in_id", "url": reference, "tag": str(img) }})  

                if blnHasALinkInParentsToHome:
                    arrayLogos.append({ "image": {"type": "url_has_link_in_parent_to_home", "url": reference, "tag": str(img) }})  


            #else:
            #        arrayLogos.append({ "image": {"type": "inline_image",  "url": str(img) }})


        # fichiers externes

        url_manifest = soup.find("link", rel="manifest")
        if url_manifest:
            # print("manifest ! ", urljoin(base_url, url_manifest['href']))
            response_manifest = self.getHTTPResponse(urljoin(base_url, url_manifest['href']))
            js = json.loads(response_manifest.content)
            if "icons" in js:
                for icon in js["icons"]:
                    arrayLogos.append({ "image": {"type": "url_manifest_image",  "url": urljoin(base_url,icon["src"]) }})
      
        for item in soup.findAll("link", type="application/rss+xml"):
            try:
                response_rss = self.getHTTPResponse(urljoin(base_url, item['href']))
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
                            arrayLogos.append({ "image": {"type": "url_json_ld_logo", "url": item['logo']}})
                except:
                    a=1


        # print(json.dumps(arrayLogos2))
        return arrayLogos


    def extractLogosFromHTTPResponse2(self,response):
        
        arrayLogos2 = []

        if response == None:
            return arrayLogos2

        content = response.content
        # print(content)
        url = response.url
        base_url = urljoin(url, '.')   

        self.last_url = url

        # content="<html><img class='logo' src='test.png' /></html>"
        soup = BeautifulSoup(content, features="html.parser")

        # balises SEO
        
        arrayLogos2 = arrayLogos2 + self.extractLogosFromBS4Nodes(soup.findAll("link", rel="icon") ,"url_favicon_html",  base_url )
        arrayLogos2 = arrayLogos2 + self.extractLogosFromBS4Nodes(soup.findAll("link", rel="apple-touch-icon") ,"apple-touch-icon",  base_url )
        arrayLogos2 = arrayLogos2 + self.extractLogosFromBS4Nodes(soup.findAll("meta", property="og:logo") ,"url_og_logo",  base_url )
        arrayLogos2 = arrayLogos2 + self.extractLogosFromBS4Nodes(soup.findAll("meta", property="og:image"),"url_og_image",  base_url )
        arrayLogos2 = arrayLogos2 + self.extractLogosFromBS4Nodes(soup.findAll("meta", property="twitter:image"),"url_twitter_image",  base_url )

        # img et/ou svg

        tags_images =["img", "svg"]
        for tag in tags_images:
        
            arrayLogos2 = arrayLogos2 + self.extractLogosFromBS4Nodes(soup.findAll(tag, {"src":    re.compile("(?i).*logo.*")}) ,"url_src_contains_logo",  base_url )
            arrayLogos2 = arrayLogos2 + self.extractLogosFromBS4Nodes(soup.findAll(tag, {"class" : re.compile('(?i).*logo.*')}) ,"class_contains_logo",  base_url )
            arrayLogos2 = arrayLogos2 + self.extractLogosFromBS4Nodes(soup.findAll(tag, {"alt" : re.compile('(?i).*logo.*')})   ,"alt_contains_logo",  base_url )
            arrayLogos2 = arrayLogos2 + self.extractLogosFromBS4Nodes(soup.findAll(tag, itemprop="logo")                        ,"url_schema_org",  base_url )


            for img in soup.findAll(tag):
                for img_parents in img.find_parents():
                    if img_parents.has_attr('class') and "logo" in str(img_parents.get("class")).lower():
                            arrayLogos2.append(Logo("url_class_logo_in_parents", str(img), base_url))
                    if img_parents.name == "header":
                            arrayLogos2.append(Logo("url_has_header_in_parents", str(img), base_url))
                    if img_parents.has_attr('id') and "logo" in str(img_parents.get("id")).lower():
                            arrayLogos2.append(Logo("url_has_a_parents_with_logo_in_id", str(img), base_url))
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
                                arrayLogos2.append(Logo("url_has_link_in_parents_with_logo_in_title", str(img), base_url))

                        if img_parents.has_attr('href') and (
                            urljoin(base_url,img_parents["href"  ])  == base_url
                            or urljoin(base_url,img_parents["href"])  == base_url + "/home"
                            or urljoin(base_url,img_parents["href"])  == base_url + "/home.html"
                            or urljoin(base_url,img_parents["href"])  == base_url + "/index.html"
                            or urljoin(base_url,img_parents["href"])  == base_url + "/index.php"
                        ) :
                            # print("url parent = " + urljoin(base_url,img_parents["href"  ]) + " vs " + base_url)
                            arrayLogos2.append(Logo("url_has_link_in_parent_to_home", str(img), base_url))
                        
        

        # fichiers externes

        url_manifest = soup.find("link", rel="manifest")
        if url_manifest:
            # print("manifest ! ", urljoin(base_url, url_manifest['href']))
            response_manifest = self.getHTTPResponse(urljoin(base_url, url_manifest['href']))
            js = json.loads(response_manifest.content)
            if "icons" in js:
                for icon in js["icons"]:
                    arrayLogos2.append(Logo("url_manifest_image", urljoin(base_url,icon["src"]), base_url))

        for item in soup.findAll("link", type="application/rss+xml"):
            try:
                response_rss = self.getHTTPResponse(urljoin(base_url, item['href']))
                soup_rss = BeautifulSoup(response_rss.content, 'lxml')
                channel = soup_rss.find("channel")
                image = channel.find("image")
                url_rss_image = image.find("url").text
                arrayLogos2.append(Logo("url_rss_image", url_rss_image, base_url))
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
                            arrayLogos2.append(Logo("url_json_ld_logo", str(item['logo']), base_url))
                except:
                    a=1


        # print(json.dumps(arrayLogos2))
        return arrayLogos2


    def download_logos(self, arrayLogos):
        result_size = {}
        result_error = []
        result_image = {}

        # print(arrayLogos)

        result= []
        for item in arrayLogos:
            item_image = item["image"]
            if item_image:
                try:
                    url = item_image["url"]
                   
                    if url.startswith("data:"):
                        contentbase64= re.sub("data:image\/[^,]+,","",url)
                        # print(contentbase64)
                        image_downloaded = Image.open(BytesIO(base64.b64decode(contentbase64)))
                    else:
                        image_downloaded = self.getImageFromTag(url)

                    result_image[url] = image_downloaded

                    if (image_downloaded):
                        result_size[url] = image_downloaded.size    
                    else:
                        if item.has_attr("src"):
                            print("in error : ", url)
                            result_error.append(url)
                except:
                    a=1

        
        for item in arrayLogos:
            item_image = item["image"]
            if item_image:
                url = item_image["url"]
                
                if url in result_error:
                    item["error"]=True

                if url in result_size:
                    width, height = result_size[url]
                    item["width"] = width
                    item["height"] = height
                    

                if "<svg" in url:
                    item["is_svg"] = True
                    
                if ".svg" in url:
                    item["is_svg"] = True
                    
                result.append(item)
                

        # print(result)
        return result

    def compute_scores(self, arrayLogos):
        result_scores= {}
        result_rules= {}

        scores = {
            "url_class_logo_in_parents": 3,
            "url_json_ld_logo": 50,
            "url_manifest_image": 5,
            "apple-touch-icon": 4,
            "url_src_contains_logo": 2,
            "url_og_image": 2,
            "url_og_logo": 50,
            "url_favicon_html": 3,
            "class_contains_logo": 3, 
            "url_rss_image": 5,
            "url_twitter_image":8,
            "alt_contains_logo": 5,
            "url_has_link_in_parents_with_logo_in_title":5,
            "url_has_a_parents_with_logo_in_id": 5,
            "url_has_header_in_parents": 1,
            "url_has_link_in_parents": 1,
            "inline_image": 1,
            "url_has_link_in_parent_to_home": 5
        }
        
        for item in arrayLogos:
            image = item["image"]
                
            if image:
                score = scores[image["type"]]
                url = image["url"]
           
                if url in result_scores:
                    
                    if not image["type"] in result_rules[url]:
                        
                        # print("regle pas encore prise en compte ")
                        result_rules[url]= result_rules[url] + " | " + image["type"] + " (+" + str(score) + ")"
                        result_scores[url] = result_scores[url] + score * 10
                    #else:
                    #    print("regle en double")

                    # print()
                    
                   
                    
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
                if "count" in item:
                    item["count"] = item["count"] + 1
                else:
                    item["count"] = 1

            result_dict[url] = item
        result=[]
        for key in result_dict:
            result.append(result_dict[key])

        # pondere score en fonction des dimensions
        result_pondere = []
        for item in result:
            
            if "width" in item and "height" in item: # and not "is_svg" in item:
                if item["width"]<32 or item["height"]<32:
                    item["score"] = item["score"] / 2
                    item["score_rules"]= item["score_rules"] + " | " + "/2 because < 32px "
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

            if "is_svg" in item and not item["image"]["url"].startswith("http") : #and len(item["image"]["url"]) > 6000:
                item["score"] = item["score"] * 4
                item["score_rules"]= item["score_rules"] + " | " + "*4 because is_svg and large inline"
                # print(item)
            if "is_svg" in item and item["image"]["url"].startswith("http"):
                item["score"] = item["score"] * 4
                item["score_rules"]= item["score_rules"] + " | " + "*4 because is_svg  and external"
                
            if "error" in item:
                item["score"] = 0
                item["score_rules"]= item["score_rules"] + " | " + "*0 because error on scrap "
            result_pondere.append(item)

        # tri desc
        result_scores_sorted = sorted(result_pondere, key=operator.itemgetter("score"), reverse=True)

        return result_scores_sorted
