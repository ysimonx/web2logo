#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import array
import requests
from PIL import Image
import io
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import BytesIO
from cairosvg import svg2png
import re
import base64

class Logo:

    def __init__(self, type, tag, base_url):
        self.type = type
        self.tag = tag
        self.base_url = base_url

        self.useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
       
        self.findURLFromTypeAndTag()

        self.last_status_code = None
        self.size = None
        self.last_image_error = None
        self.img = None
        self.score = 0
        self.score_rules = ""
        self.isSVG = False
        
    def findURLFromTypeAndTag(self):
        url = None
        # print ("type = ", self.type)
        if self.type in [
                            "url_favicon_html",
                            "apple-touch-icon"
                        ]:
            soup =  BeautifulSoup(self.tag, features="html.parser")
            node = next(iter(soup))
            if node and node.has_attr("href"):
                url = node.get("href")
                

        if self.type in [
                            "url_og_logo",
                            "url_og_image",
                            "url_twitter_image"
                        ]:
            soup =  BeautifulSoup(self.tag, features="html.parser")
            node = next(iter(soup))
            if node and node.has_attr("content"):
                url = node.get("content")

        if self.type in [
                            "url_src_contains_logo",
                            "class_contains_logo",
                            "alt_contains_logo",
                            "url_schema_org",
                            "url_class_logo_in_parents",
                            "url_has_header_in_parents",
                            "url_has_link_in_parents",
                            "url_has_link_in_parents_with_logo_in_title",
                            "url_has_a_parents_with_logo_in_id",
                            "url_has_link_in_parent_to_home"
                        ]:
            soup =  BeautifulSoup(self.tag, features="html.parser")
            node = next(iter(soup))
            if node and node.has_attr("src"):
                url = node.get("src")
           
    
        if url == None:
            url = self.tag
        else:
            url = urljoin(self.base_url,url)

        # print("url = ", url)
        self.url = url                      

    def toJSON(self):
        return {
                    'image':
                        {
                            'type': self.type,
                            'url': self.url,
                            'tag': self.tag,
                            'base_url': self.base_url,
                            'last_status_coded': self.last_status_code,
                            'score': self.score,
                            'score_rules': self.score_rules,
                            'size': self.size,
                            'is_svg': self.isSVG
                        }
                }

    def setIMG(self, pil_img):
        self.img = pil_img
        self.size = pil_img.size
        return self



    def download(self):

        self.img = None

        # ---- INLINE -----
        if self.url.startswith("data:"):
            contentbase64= re.sub("data:image\/[^,]+,","",self.url)
            image_downloaded = Image.open(BytesIO(base64.b64decode(contentbase64)))
            self.setIMG(image_downloaded)
            return self

        if self.url.startswith('<svg'):
            self.isSVG=True
            self.setIMG(self.convertSVGtoImage(self.url))
            return self
        
        # ---- EXTERNAL -----
        headers = {
            "User-Agent": self.useragent
        }
        
        try:
            response = requests.get(self.url, headers=headers)
            # print("response status code = ", response.status_code)
            self.last_status_code = response.status_code
            
            if response.status_code == 200:
                if ('<svg' in str(response.content)):
                    # print("contains svg xml")
                    # print(response.content)
                    self.isSVG=True
                    self.setIMG(self.convertSVGtoImage(response.content))
                    return self
                image_bytes = io.BytesIO(response.content)
                img = Image.open(image_bytes)
                self.setIMG(img)

                
        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            self.last_image_error = "requests.exceptions.Timeout"
        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            self.last_image_error = "requests.exceptions.TooManyRedirects"
        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            self.last_image_error = "requests.exceptions.RequestException : %s" % (e) 
            
        return self
                                      
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

                # because of  <svg xmlns="http://www.w3.org/2000/svg" width="100" viewBox="0 0 768 300" class="hide-on-desktop"> on decitre.fr
                if "width" in svg.attrs:
                    del svg.attrs['width']
                if "height" in svg.attrs:
                    del svg.attrs['height']

                text = str(svg)

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
