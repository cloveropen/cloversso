#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import logging

from flask import Flask
from flask import send_from_directory
from flask import jsonify
from api.config.config import DevelopmentConfig, ProductionConfig, TestingConfig
from api.utils.responses import response_with
import api.utils.database as db
from api.routes.users import user_routes
from api.routes.login import login_routes
import api.utils.responses as resp
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
from apispec import APISpec
from flask_jwt_extended import JWTManager

SWAGGER_URL = '/api/docs'
app = Flask(__name__)


@app.route('/')
def hos_restapi():
    return response_with(resp.SUCCESS_200, value={'message': 'cloveropen.com hos api'})


if os.environ.get('WORK_ENV') == 'PROD':
    app_config = ProductionConfig
elif os.environ.get('WORK_ENV') == 'TEST':
    app_config = TestingConfig
else:
    app_config = DevelopmentConfig

app.config.from_object(app_config)

# db.init_app(app)
with app.app_context():
    db.test_link()
# app.register_blueprint(author_routes, url_prefix='/api/authors')
# app.register_blueprint(book_routes, url_prefix='/api/books')
app.register_blueprint(user_routes, url_prefix='/api/v1/users')
app.register_blueprint(login_routes, url_prefix='/api/v1/login')


@app.route('/avatar/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.after_request
def add_header(response):
    return response


@app.errorhandler(400)
def bad_request(e):
    logging.error(e)
    return response_with(resp.BAD_REQUEST_400)


@app.errorhandler(500)
def server_error(e):
    logging.error(e)
    return response_with(resp.SERVER_ERROR_500)


@app.errorhandler(404)
def not_found(e):
    logging.error(e)
    return response_with(resp.SERVER_ERROR_404)


# END GLOBAL HTTP CONFIGURATIONS

@app.route("/api/spec")
def spec():
    swag = swagger(app, prefix='/api')
    swag['info']['base'] = "http://localhost:5000"
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "Flask Author DB"
    return jsonify(swag)


swaggerui_blueprint = get_swaggerui_blueprint('/api/docs', '/api/spec', config={'app_name': "CAS LOGIN"})
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
jwt = JWTManager(app)
# db.init_app(app)
# mail.init_app(app)
# with app.app_context():
#    # from api.models import *
#    db.create_all()

if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0", use_reloader=False, debug=True)
