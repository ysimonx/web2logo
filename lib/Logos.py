#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import array
import operator
from .Logo import Logo

class CustomLogoError(Exception):
    def __init__(self, if_obj, element):
        self.IF_obj = if_obj
        self.element = element

    def __str__(self):
        return self.element + ' is not a Logo'


class Logos(list):
    def __init__(self, *args):
        super().__init__(self, *args)
        self.sorted_logo = []

    def download(self):
        print("downloading Logos...")
        for i in range(len(self)):  
            logo = self.__getitem__(i)
            logo = logo.download()
            self.__setitem__(i,logo)

    def append(self, element):
        if not isinstance(element, Logo):
            raise CustomLogoError(self, element)
        return super(Logos, self).append(element)

    def toJSONArray(self):
        result = []
        for i in range(len(self)): 
            logo = self.__getitem__(i)
            result.append(logo.toJSON())
        return result

    def computeScore(self):
        print("computing scores...")

       

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

        for i in range(len(self)):
            logo = self.__getitem__(i)
            
            if logo.img:
                
                score = scores[logo.type]
                url = logo.url
           
                if url in result_scores:
                    if not logo.type in result_rules[url]: # on evite les regles en double
                        result_rules[url]= result_rules[url] + " | " + logo.type + " (+" + str(score) + ")"
                        result_scores[url] = result_scores[url] + score * 10
  
                else:
                    result_scores[url] = score * 10
                    result_rules[url] = logo.type + " (+" + str(score) + ")"
        
        
        # dedoublonne 
        result_dict= dict()
        for i in range(len(self)):
            logo = self.__getitem__(i)
            if logo:
                url = logo.url
                try:
                   
                    logo.score =  result_scores[url]
                    logo.score_rules = result_rules[url]
                except:
                    logo.score =  0
                    logo.score_rules = "error"
                #if "count" in logo:
                #    logo.count = logo.count + 1
                #else:
                #    logo.count = 1

            result_dict[url] = logo

        results=[]
        for key in result_dict:
            results.append(result_dict[key])
        
         # pondere score en fonction des dimensions
        result_pondere = []
        for item in results:
            if item.size:
                width, height= item.size
              
                if width<32 or height<32:
                    item.score = item.score / 2
                    item.score_rules = item.score_rules + " | " + "/2 because < 32px "
                if width<80 or height<80:
                    item.score = item.score / 2
                    item.score_rules = item.score_rules + " | " + "/2 because < 80px "
                if width >130 or height >130:
                    item.score = item.score * 2
                    item.score_rules = item.score_rules + " | " + "*2 because > 130px "
                if width >300 or height >300:
                    item.score = item.score * 2
                    item.score_rules = item.score_rules + " | " + "*2 because > 300px "
            else:
                item.score = 0

         
            if item.isSVG and not item.url.startswith("http") and len(item.tag) > 2000:
                item.score = item.score * 2
                item.score_rules = item.score_rules + " | " + "*2 because is_svg and large inline"
            if item.isSVG and item.url.startswith("http"):
                item.score = item.score * 4
                item.score_rules = item.score_rules + " | " + "*4 because is_svg and external"
            #    
           
            result_pondere.append(item)

        # tri desc
        # result_scores_sorted = sorted(result_pondere, key=operator.itemgetter("score"), reverse=True)
        result_scores_sorted = sorted(result_pondere, key=lambda x: x.score, reverse=True)

        # print("-------------------------------")
        # for result in result_scores_sorted:
        #     print(result.toJSON())

        self.sorted_logo = result_scores_sorted
        return self