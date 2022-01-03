from lib.Logos import Logos 
from lib.Logo import Logo

testLogos = Logos()
logox = Logo("test","<img>","http://www.domaine.com")

testLogos.append(Logo("test","<img>","http://www.domaine.com"))
testLogos.append(Logo("test","<img>","http://www.domaine.com"))
testLogos.append(Logo("test","<img>","http://www.domaine.com"))
testLogos.append(Logo("test","<img>","http://www.domaine.com"))
testLogos.append(Logo("test","<img>","http://www.domaine.com"))

testLogos.computeScore()
