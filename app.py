from flask import Flask, render_template, request, redirect
from flask_cors import CORS
from flask_caching import Cache

import json


from lib.LogoScrapper import LogoScrapper 

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
    
    logoScrapper =  LogoScrapper();

    response = logoScrapper.get_url_content(home)

    logos = logoScrapper.get_logos(response)
 
  

    logos_downloaded = logoScrapper.getDownloads(logos)
   
    print(logos_downloaded)

    logos_scored = logoScrapper.getScores(logos_downloaded)


    if len(logos_scored) > 0:
        print(logos_scored[0])
        if not request.args.get('debug'): 
            return redirect(logos_scored[0]["image"]["url"], code=302)

    if len(logos_scored) > 0:

        choosen_logo = logos_scored[0]["image"]["url"]
    else:
        choosen_logo = ""

    result= {
        "logo": choosen_logo,
        # "logos_details": logos,
        "logos_scores": logos_scored
        
    }
    response = app.response_class(
        response=json.dumps(result),
        mimetype='application/json'
    )
    return response




# def get_param_url(path, query_string):
#     if not query_string:
#         return path
#     return '%s?%s' % (path, query_string) 

