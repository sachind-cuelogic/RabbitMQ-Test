from flask import Flask, jsonify
from config import configure_app
from domainIdentifier.models import db, Domains
from domain_crawler import getDomains

app = Flask(__name__)
configure_app(app)
db.init_app(app)

@app.route('/domain/<companyName>', methods=['GET'])
def get(companyName):
    output = []
    domains = getDomains(companyName)
    return jsonify({'result': list(domains)})
