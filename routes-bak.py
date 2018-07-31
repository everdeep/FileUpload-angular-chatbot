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
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')

#####################################################
##  404 handling
#####################################################

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.pug'), 404

#####################################################
##  INDEX
#####################################################

@app.route('/')
def index():
	# Check if the user is logged in
	if('logged_in' not in session or not session['logged_in']):
		return redirect(url_for('login'))
	page['title'] = 'Olympics'
	return render_template('index.pug',
		session=session,
		page=page,
		user=user_details)

#####################################################
##  LOGIN
#####################################################

@app.route('/login', methods=['POST', 'GET'])
def login():
	# Check if they are submitting details, or they are just logging in
	if(request.method == 'POST'):
		# submitting details
		login_return_data = database.check_login(request.form['id'], request.form['password'])

		# If it's null, saying they have incorrect details
		if(login_return_data is None):
			page['bar'] = False
			flash("Incorrect id/password, please try again")
			return redirect(url_for('login'))

		# If there was no error, log them in
		page['bar'] = True
		flash('You have been logged in successfully')
		session['logged_in'] = True

		# Store the user details for us to use throughout
		global user_details
		user_details = login_return_data
		session['member_type'] = user_details['member_type']
		return redirect(url_for('index'))

	elif(request.method == 'GET'):
		#database.data_update()
		#database.secure_passwords()
		return(render_template('login.pug', page=page))

#####################################################
##  LOGOUT
#####################################################

@app.route('/logout')
def logout():
	session['logged_in'] = False
	page['bar'] = True
	flash('You have been logged out')
	return redirect(url_for('index'))

#####################################################
##  Member Details
#####################################################

@app.route('/details')
def member_details():
	if('logged_in' not in session or not session['logged_in']):
		return redirect(url_for('login'))

	# Go to the database to get the user information
	return_information = database.member_details(user_details['member_id'], user_details['member_type'])

	if(return_information is None):
		flash('Error, User\'{}\' does not exist'.format(user_details['member_id']))
		page['bar'] = False
		return redirect(url_for('index'))

	return render_template(
		'member_details.pug',
		user = user_details,
		extra = return_information,
		session = session,
		page = page
	)

#####################################################
##  LIST EVENTS
#####################################################
search_filter = ''
search_results = []
@app.route('/events', methods=['POST', 'GET'])
def list_events_filter():
	global search_filter, search_results
	if('logged_in' not in session or not session['logged_in']):
		return redirect(url_for('login'))
	# The user is just viewing the page
	if(request.method == 'GET'):
		search_filter = ''
		search_results = []
		# First check if specific event
		search = False
		q = request.args.get('q')
		if q:
			search = True

		pagination_page = request.args.get('page', type=int, default=1)
		event_list = database.all_events()
		if(event_list is None):
			event_list = []
			flash("Error, no events in our system.")
			page['bar'] = False
			return redirect(url_for('list_events'))

		pagination = Pagination(page=pagination_page, total=len(event_list), search=search, record_name='events')
		print(pagination_page, pagination.total)
		total_pages = math.ceil(int(pagination.total) / int(pagination.per_page))
		if int(pagination_page) < 0 or int(pagination_page) > int(total_pages):
			return render_template('404.pug'), 404

		return render_template(
			'event_list.pug',
			events = event_list,
			pagination = pagination,
			session = session,
			page = page
		)

	# Try to get from the database
	elif(request.method == 'POST'):
		search_filter = request.form['search']
		search_results = database.all_events_sport(search_filter)
		if(search_results is None):
			search_results = []
			flash('Error, sport \'{}\' does not exist'.format(search_filter))
			page['bar'] = False
			return redirect(url_for('list_events_filter'))

		return redirect(url_for('list_events'))

@app.route('/events-search', methods=['POST', 'GET'])
def list_events():
	if('logged_in' not in session or not session['logged_in']):
		return redirect(url_for('login'))

	search = False
	q = request.args.get('q')
	if q:
		search = True

	pagination_page = request.args.get('page', type=int, default=1)
	pagination = Pagination(page=pagination_page, total=len(search_results), search=search, record_name='events')
	return render_template(
		'event_list.pug',
		events = search_results,
		pagination = pagination,
		session = session,
		page = page
	)

#####################################################
## EVENT DETAILS
#####################################################
@app.route('/eventdetails/')
def event_details():
	if('logged_in' not in session or not session['logged_in']):
		return redirect(url_for('login'))
	# Check the details of the event
	event_id = request.args.get('event_id', '')

	if not event_id:
		page['bar'] = False
		flash("Error, no event was given. URL requires \'?event_id=<id>\'")
		return(redirect(url_for('index')))

	if int(event_id) < 1:
		return render_template('404.pug'), 404

	# Get the relevant data for all the event details
	event_results = database.get_results_for_event(event_id)
	event_officials = database.get_all_officials(event_id)
	event_information = database.event_details(event_id)

	if event_officials is None:
		event_officials = []
	if event_results is None:
		event_results = []
	if event_information is None:
		page['bar'] = False
		flash("Error invalid event name given")
		return (redirect(url_for('list_events_filter')))

	return render_template(
		'event_detail.pug',
		session = session,
		results = event_results,
		officials = event_officials,
		event = event_information,
		page = page
	)

#####################################################
##  MAKE BOOKING
#####################################################

@app.route('/new-booking' , methods=['GET', 'POST'])
def new_booking():
	if('logged_in' not in session or not session['logged_in']):
		return redirect(url_for('login'))

	# The make_booking() plpgsql function will also check that it is a staff member making the booking
	if(session['member_type'] != 'Staff'):
		return redirect(url_for('index'))

	# If we're just looking at the 'new booking' page
	if(request.method == 'GET'):
		return render_template('new_booking.pug', user=user_details, session=session, page=page)
	# If we're making the booking
	success = database.make_booking(user_details['member_id'],
									request.form['member_id'],
									request.form['vehicle_regno'],
									request.form['book_date'],
									request.form['book_hour'],
									request.form['from_place'],
									request.form['to_place'])
	if(success == True):
		page['bar'] = True
		flash('Booking Successful!')
		return(redirect(url_for('index')))
	else:
		page['bar'] = False
		flash('There was an error making your booking.')
		return(redirect(url_for('new_booking')))



#####################################################
##  SHOW MY BOOKINGS
#####################################################

@app.route('/bookings', methods=['GET', 'POST'])
def user_bookings():
	if('logged_in' not in session or not session['logged_in']):
		return redirect(url_for('login'))

	# Check the day filter - if it is not there, then get all bookings
	if(request.method == 'POST'):
		bookings_list = database.day_bookings(user_details['member_id'], request.form['dayfilter'])
	else:
		bookings_list = database.all_bookings(user_details['member_id'])

	if(bookings_list is None):
		page['bar'] = False
		flash('No bookings available')
		bookings_list = []

	# First check if specific event
	search = False
	q = request.args.get('q')
	if q:
		search = True

	pagination_page = request.args.get('page', type=int, default=1)
	pagination = Pagination(page=pagination_page, total=len(bookings_list), search=search, record_name='events')
	return render_template(
		'bookings_list.pug',
		bookings = bookings_list,
		pagination = pagination,
		session = session,
		page = page
	)



@app.route('/booking-detail')
def booking_detail():
	if('logged_in' not in session or not session['logged_in']):
		return redirect(url_for('login'))

	# Bookings information
	booking_to = request.args.get('to', '')
	booking_from = request.args.get('from', '')
	booking_vehicle = request.args.get('vehicle', '')
	booking_startday = request.args.get('startdate', '')
	booking_starttime= request.args.get('starttime', '')

	if(booking_to == '' or booking_from == '' or booking_vehicle == '' or booking_startday == '' or booking_starttime == ''):
		# Booking details
		page['bar'] = False
		flash('Error, incorrect details provided')
		return redirect(url_for('user_bookings'))

	# Get the booking based off the information
	booking_details = database.get_booking(
		booking_startday,
		booking_starttime,
		booking_vehicle,
		booking_from,
		booking_to,
		user_details['member_id']
	)

	return render_template(
		'booking_detail.pug',
		user = user_details,
		page = page,
		session = session,
		booking = booking_details
	)

#####################################################
## Show Journeys
#####################################################
from_place = ''
to_place = ''
filter_date = ''
journeys_data = None

@app.route('/journeysfilter', methods=['GET', 'POST'])
def journeys_filterpage():
	global from_place, to_place, filter_date, journeys_data
	if('logged_in' not in session or not session['logged_in']):
		return redirect(url_for('login'))

	if(request.method == 'GET'):
		from_place = ''
		to_place = ''
		filter_date = ''
		journeys_data = None
		return render_template('journey_filterpage.pug', session=session, user=user_details, page=page)

	# Get the filter information
	from_place = request.form['from_place']
	to_place = request.form['to_place']
	filter_date = request.form['filter_date']

	if(from_place == '' or to_place == ''):
		page['bar'] = False
		flash('Error, no from_place/to_place provided!')
		return redirect(url_for('journeys_filterpage'))

	# Check if the date is filtered
	if(filter_date == ''):
		journeys_data = database.all_journeys(from_place, to_place)
	else:
		journeys_data = database.get_day_journeys(from_place, to_place, filter_date)

	if(journeys is None):
		journeys_data = []
		page['bar'] = False
		flash('No journeys for given places')

	return redirect(url_for('journeys'))

@app.route('/journeys', methods=['GET', 'POST'])
def journeys():
	if('logged_in' not in session or not session['logged_in']):
		return redirect(url_for('login'))

	# First check if specific event
	search = False
	q = request.args.get('q')
	if q:
		search = True

	pagination_page = request.args.get('page', type=int, default=1)
	pagination = Pagination(page=pagination_page, total=len(journeys_data), search=search, record_name='events')
	return render_template(
		'journey_list.pug',
		formdata = {'to': to_place, 'from': from_place},
		user_details = user_details,
		journeys = journeys_data,
		pagination = pagination,
		session = session,
		page = page
	)
