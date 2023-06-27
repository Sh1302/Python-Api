from flask import Flask, Blueprint, jsonify
from flask_cors import CORS
from api import all_api



def start():
    web = Flask(__name__)  # Initialize Flask App
    CORS(web)

    api_blueprint = Blueprint('api_blueprint', __name__)
    api_blueprint = all_api(api_blueprint)

    web.register_blueprint(api_blueprint , url_prefix='/api')    

    return web

app = start()


if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)