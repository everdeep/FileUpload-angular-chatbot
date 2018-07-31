# Importing the frameworks

from modules import *
from flask import *
from flask_paginate import Pagination
import database
import configparser
import math

user_details = {}	# User details kept for us
session = {}
page = {}

# Initialise the application
app = Flask(__name__)

# Change this to more secure key
app.secret_key = 'aab12124d346928d14710610f'

@app.route('/api/', methods=['POST'])
def index():
	# Check if the user is logged in
	if('logged_in' not in session or not session['logged_in']):
		return redirect(url_for('login'))

	return 'message received'
