#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import array
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

    def download(self):
        print("downloading Logos...")
        for i in range(len(self)):  
            logo = self.__getitem__(i)
            logo = logo.download()
            self.__setitem__(i,logo)


    def computeScore(self):
        print("computing scores...")

        for i in range(len(self)):
            logo = self.__getitem__(i)
            print(logo.to_JSON())
            

    def append(self, element):
        if not isinstance(element, Logo):
            raise CustomLogoError(self, element)
        return super(Logos, self).append(element)


