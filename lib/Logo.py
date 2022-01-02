#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

class Logo:

    def __init__(self, type, tag, base_url):
        self.type = type
        self.tag = tag
        self.base_url = base_url
        self.url = None
        self.last_status_code = None
        self.size = None

    def toJSON(self):
            return json.dumps(self, default=lambda o: o.__dict__, 
                sort_keys=True, indent=4)

    def to_JSON(self):
        return {
                    'image':
                        {
                            'type': self.type,
                            'url': self.url,
                            'tag': self.tag,
                            'base_url': self.base_url
                        }
                }
                    
                    
