from flask import Flask
app = Flask(__name__)
#app.config["CACHE_TYPE"] = "null"  # to make sure changes go through
app.config["TEMPLATES_AUTO_RELOAD"]=True  # otherwise pywidget rendering doesn't update
from flaskexample import views
