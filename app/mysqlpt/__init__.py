from flask import Blueprint
mysql = Blueprint('mysql', __name__)
from . import views