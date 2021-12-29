from logging import log
from flask          import Flask, render_template, request, redirect, send_file
from flask_cors     import CORS
from flask_caching  import Cache
from io             import BytesIO
import json


from lib.LogoScrapper import LogoScrapper 


app = Flask(__name__)

config = {
    "DEBUG": True,                # some Flask specific configs
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

    page = 'https://%s/' % (domain)  

    logoScrapper =  LogoScrapper();
    logos = logoScrapper.get_logos(page)

    result= {
            "logos": logos,
            "url": logoScrapper.last_url
    }
    
    with open('./var/%s.json' % (domain), 'w') as outfile:
        json.dump(result, outfile, indent=4)

    
    if len(logos) > 0:
        if not request.args.get('debug'): 
            img_io = BytesIO()
            pil_img = logoScrapper.get_image(logos[0]["image"]["url"])
            print(logos[0]["image"]["url"])
            pil_img.convert('RGB').save(img_io, 'JPEG', quality=70)
            img_io.seek(0)
            return send_file(img_io, mimetype='image/jpeg')
   

    response = app.response_class(
        response=json.dumps(result, indent=4),
        mimetype='application/json'
    )
    #print(logoScrapper.last_error)
    return response



