class Config(object):
    #DEBUG = True
    #TESTING = False
    pass


class ProductionConfig(Config):
    DB_CONN_CONFIG = {
        'host': '121.36.48.65',
        'user': 'clover_md',
        'password': 'neweastwillgnu@cloveropen',
        'dbname': 'clover_md',
        'port': 5432
    }
    JWT_SECRET_KEY = 'JWT-SECRET'
    SECRET_KEY = 'SECRET-KEY'
    SECURITY_PASSWORD_SALT = 'SECRET-KEY-PASSWORD'
    UPLOAD_FOLDER = '<upload_folder>'
    CAS_URL = 'https://clover.app-hos.com:8443'
    SERVICE_URL = 'https://clover.app-hos.com'

class DevelopmentConfig(Config):
    DEBUG = True
    DB_CONN_CONFIG = {
        'host': '121.36.48.65',
        'user': 'clover_md',
        'password': 'neweastwillgnu@cloveropen',
        'dbname': 'clover_md',
        'port': 5432
    }
    JWT_SECRET_KEY = 'JWT-SECRET'
    SECRET_KEY = 'SECRET-KEY'
    SECURITY_PASSWORD_SALT = 'SECRET-KEY-PASSWORD'
    UPLOAD_FOLDER = '<upload_folder>'
    CAS_URL = 'https://clover.app-hos.com:8443'
    SERVICE_URL = 'https://clover.app-hos.com'

class TestingConfig(Config):
    TESTING = True
    DB_CONN_CONFIG = {
        'host': 'localhost',
        'user': 'postgres',
        'password': '',
        'dbname': 'test',
        'port': 5432
    }
    JWT_SECRET_KEY = 'JWT-SECRET'
    SECRET_KEY = 'SECRET-KEY'
    SECURITY_PASSWORD_SALT = 'SECRET-KEY-PASSWORD'
    UPLOAD_FOLDER = '<upload_folder>'
    CAS_URL = 'https://clover.app-hos.com:8443'
    SERVICE_URL = 'https://clover.app-hos.com'