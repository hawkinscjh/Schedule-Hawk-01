from secrets import token_bytes
from google.cloud import datastore
from flask import Flask, request, jsonify, make_response, render_template, redirect, session
import requests
from requests_oauthlib import OAuth2Session
from json2html import *
import json
from google.auth import crypt, jwt
from google.oauth2 import id_token
from google.auth.transport import requests
import constants

import os 
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
client = datastore.Client()

client_id = constants.client_id
client_secret = constants.client_secret

#redirect_uri = "https://schedule-hawk-01.uc.r.appspot.com/oauth"
redirect_uri = 'http://127.0.0.1:8080/oauth'

scope = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'openid']
oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)

@app.route('/')
def index():
	authorization_url, state = oauth.authorization_url('https://accounts.google.com/o/oauth2/auth', access_type="offline", prompt="select_account")
	
	return render_template('index.html', authorization_url=authorization_url)
	#return '<h1>Welcome</h1>\n <p>Sign-in to Google <a href=%s>here</a></p>' % authorization_url

@app.route('/oauth')
def oauthroute():
	token = oauth.fetch_token('https://accounts.google.com/o/oauth2/token', authorization_response=request.url, client_secret=client_secret)
	id_info = id_token.verify_oauth2_token(token['id_token'], requests.Request(), client_id, clock_skew_in_seconds=30)
	query = client.query(kind="users")
	query.add_filter("sub", "=", id_info['sub'])
	result = list(query.fetch())

	if len(result) == 0:
		new_user = datastore.entity.Entity(key=client.key('users'))
		new_user.update({'email': id_info['email'], 'sub': id_info['sub']})
		client.put(new_user)
		return (("<h1>Account has been created</h1>\n	<p>JWT: %s</p>\n	<p>Unique ID (sub): %s</p>\n" % (token['id_token'], id_info['sub'])), 201)
	elif len(result) == 1:
		return render_template('oauth.html', token=token['id_token'], sub=id_info['sub'], email=id_info['email'])

@app.route('/users', methods=['GET'])
def get_users():
	if request.method == 'GET':
		query = client.query(kind="users")
		results = list(query.fetch())

		for entity in results:
			entity["id"] = entity.key.id
			entity["self"] = request.url + "/" + str(entity.key.id)

		return (jsonify(results), 200)
	else:
		return "Method not allowed", 405

@app.route('/users/<uid>', methods=['GET'])
def get_user_id(uid):
	if request.method == 'GET':

		token = request.headers.get('Authorization')
		
		if token:
			token = token.split(" ")[1]

			try:
				id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
				sub = id_info['sub']
			except:
				return (jsonify({"Error": "Invalid JWT"}), 401)
		else:
			return (jsonify({"Error": "JWT not found"}), 401)
		
		if sub != uid:
			return(jsonify({'Error': 'You do not have access to this user'}), 401)
			
		query = client.query(kind="users")
		query.add_filter("sub", "=", uid)
		results = list(query.fetch())

		if len(results) == 0:
			return(jsonify({'Error': 'User does not exist'}), 401)

		for entity in results:
			entity["id"] = entity.key.id
			entity["self"] = request.url

		return (jsonify(results), 200)
	else:
		return "Method not allowed", 405

@app.route('/availability', methods=['POST','GET'])
def availability_get_post():
	if request.method == 'POST':
		
		token = request.headers.get('Authorization')
		
		if token:
			token = token.split(" ")[1]

			try:
				id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
				sub = id_info['sub']
				email = id_info['email']
			except:
				return (jsonify({"Error": "Invalid JWT"}), 401)
		else:
			return (jsonify({"Error": "JWT not found"}), 401)

		content = request.get_json()
		
		if "Type" in content and "Sunday_AM" in content and "Sunday_PM" in content and "Monday_AM" in content and "Monday_PM" in content and "Tuesday_AM" in content and "Tuesday_PM" in content and "Wednesday_AM" in content and "Wednesday_PM" in content and "Thursday_AM" in content and "Thursday_PM" in content and "Friday_AM" in content and "Friday_PM" in content and "Saturday_AM" in content and "Saturday_PM" in content:
			
			new_availability = datastore.entity.Entity(key=client.key("availability"))
			new_availability.update({"Type": content["Type"], "Sunday_AM": content["Sunday_AM"],"Sunday_PM": content["Sunday_PM"],"Monday_AM": content["Monday_AM"], "Monday_PM": content["Monday_PM"],"Tuesday_AM": content["Tuesday_AM"], "Tuesday_PM": content["Tuesday_PM"], "Wednesday_AM": content["Wednesday_AM"], "Wednesday_PM": content["Wednesday_PM"],"Thursday_AM": content["Thursday_AM"], "Thursday_PM": content["Thursday_PM"],"Friday_AM": content["Friday_AM"], "Friday_PM": content["Friday_PM"],"Saturday_AM": content["Saturday_AM"], "Saturday_PM": content["Saturday_PM"], "Available": [], "Unavailable": [], "owner": sub, "email": email})
			
			client.put(new_availability)
			new_availability['id'] = new_availability.key.id
			new_availability['self'] = request.url + '/' + str(new_availability.key.id)
			
			return(jsonify(new_availability), 201)
		else:
			return (jsonify({"Error": "The request object is missing at least one of the required attributes"}), 400)
	
	elif request.method == 'GET':
		token = request.headers.get('Authorization')
		if token:
			token = token.split(" ")[1]
			try:
				id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
				sub = id_info['sub']

				query = client.query(kind="availability")
				query.add_filter("owner", "=", sub)

				q_limit = int(request.args.get('limit', '5'))
				q_offset = int(request.args.get('offset', '0'))
				l_iterator = query.fetch(limit= q_limit, offset=q_offset)
				pages = l_iterator.pages
				results = list(next(pages))
				if l_iterator.next_page_token:
					next_offset = q_offset + q_limit
					next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
				else:
					next_url = None
				for e in results:
					e["id"] = e.key.id
					e["self"] = request.url + '/' + str(e.key.id)
				output = {"availabilities": results}
				output['total'] = len(list(query.fetch()))
				if next_url:
					output["next"] = next_url

				return (jsonify(output), 200)
			except:

				q_limit = int(request.args.get('limit', '5'))
				q_offset = int(request.args.get('offset', '0'))
				l_iterator = query.fetch(limit= q_limit, offset=q_offset)
				pages = l_iterator.pages
				results = list(next(pages))
				if l_iterator.next_page_token:
					next_offset = q_offset + q_limit
					next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
				else:
					next_url = None
				for e in results:
					e["id"] = e.key.id
					e["self"] = request.url + '/' + str(e.key.id)
				output = {"availabilities": results}
				output['total'] = len(list(query.fetch()))
				if next_url:
					output["next"] = next_url

				return (jsonify(output), 200)
		else:
			query = client.query(kind="availability")
			q_limit = int(request.args.get('limit', '5'))
			q_offset = int(request.args.get('offset', '0'))
			l_iterator = query.fetch(limit= q_limit, offset=q_offset)
			pages = l_iterator.pages
			results = list(next(pages))
			if l_iterator.next_page_token:
				next_offset = q_offset + q_limit
				next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
			else:
				next_url = None
			for e in results:
				e["id"] = e.key.id
				e["self"] = request.url + '/' + str(e.key.id)
			output = {"availabilities": results}
			output['total'] = len(list(query.fetch()))
			if next_url:
				output["next"] = next_url

			return (jsonify(output), 200)

	else:
		return "Method not allowed", 405

@app.route('/availability/<availability_id>', methods=['PUT', 'PATCH', 'DELETE'])
def put_patch_delete_availability(availability_id):
	if request.method == 'DELETE':
		token = request.headers.get('Authorization')
		if token:
			token = token.split(" ")[1]
			try:
				id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
				sub = id_info['sub']
			except:
				return (jsonify({"Error": "Invalid JWT"}), 401)
		else:
			return (jsonify({"Error": "JWT not found"}), 401)
		
		availability_key = client.key("availability", int(availability_id))
		availability = client.get(key=availability_key)
		
		if availability == None:
			return (jsonify({'Error': 'No availability with this availability_id exists'}), 404)
		elif availability['owner'] != sub:
			return (jsonify({'Error': 'This availability is owned by someone else'}), 403)

		if len(availability['Available']) > 0:
			for schedule in availability['Available']:
				schedule_key = client.key("schedule", int(schedule['id']))
				schedule_obj = client.get(key=schedule_key)
				schedule_obj['Availabilities'].remove({"id": availability.key.id, "email": availability["email"]})
				client.put(schedule_obj)
		if len(availability['Unavailable']) > 0:
			for schedule in availability['Unavailable']:
				schedule_key = client.key("schedule", int(schedule['id']))
				schedule_obj = client.get(key=schedule_key)
				schedule_obj['Unavailabilities'].remove({"id": availability.key.id, "email": availability["email"]})
				client.put(schedule_obj)


		client.delete(availability_key)
		return (jsonify(''), 204)

	elif request.method == 'PATCH':
		token = request.headers.get('Authorization')
		if token:
			token = token.split(" ")[1]
			try:
				id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
				sub = id_info['sub']
			except:
				return (jsonify({"Error": "Invalid JWT"}), 401)
		else:
			return (jsonify({"Error": "JWT not found"}), 401)

		content = request.get_json()
		availability_key = client.key("availability", int(availability_id))
		availability = client.get(key=availability_key)
		if availability != None:
			if availability['owner'] != sub:
				return (jsonify({'Error': 'This availability is owned by someone else'}), 403)

			if len(content) > 1:
					return (jsonify({"Error": "PATCH may only be used to update one attribute at a time"}), 400)
			if "id" in content:
				return (jsonify({"Error": "Not allowed to change id"}), 400)
			if "email" in content:
				return (jsonify({"Error": "Not allowed to change email"}), 400)
			if "owner" in content:
				return (jsonify({"Error": "Not allowed to change owner"}), 400)
			if len(availability["Available"]) > 0 or len(availability["Unavailable"]) > 0:
				return (jsonify({"Error": "Not allowed to patch availabilties after they have been assigned to a schedule"}), 400)
			if "Type" in content:
				availability.update({"Type": content["Type"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Sunday_AM" in content:
				availability.update({"Sunday_AM": content["Sunday_AM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Sunday_PM" in content:
				availability.update({"Sunday_PM": content["Sunday_PM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Monday_AM" in content:
				availability.update({"Monday_AM": content["Monday_AM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Monday_PM" in content:
				availability.update({"Monday_PM": content["Monday_PM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Tuesday_AM" in content:
				availability.update({"Tuesday_AM": content["Tuesday_AM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Tuesday_PM" in content:
				availability.update({"Tuesday_PM": content["Tuesday_PM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Wednesday_AM" in content:
				availability.update({"Wednesday_AM": content["Wednesday_AM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Wednesday_PM" in content:
				availability.update({"Wednesday_PM": content["Wednesday_PM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Thursday_AM" in content:
				availability.update({"Thursday_AM": content["Thursday_AM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Thursday_PM" in content:
				availability.update({"Thursday_PM": content["Thursday_PM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Friday_AM" in content:
				availability.update({"Friday_AM": content["Friday_AM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Friday_PM" in content:
				availability.update({"Friday_PM": content["Friday_PM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Saturday_AM" in content:
				availability.update({"Saturday_AM": content["Saturday_AM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
			if "Saturday_PM" in content:
				availability.update({"Saturday_PM": content["Saturday_PM"]})
				client.put(availability)
				availability["id"] = int(availability_id)
				availability["self"] = request.url
				return (jsonify(availability), 200)
				
			else:
				return (jsonify({"Error": "PATCH requires updating either type or one day_AM/PM shift availability"}), 400)	
		else:
			return (jsonify({"Error": "No availability with this availability_id exists"}), 404)


	elif request.method == 'PUT':
		token = request.headers.get('Authorization')
		if token:
			token = token.split(" ")[1]
			try:
				id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
				sub = id_info['sub']
			except:
				return (jsonify({"Error": "Invalid JWT"}), 401)
		else:
			return (jsonify({"Error": "JWT not found"}), 401)

		content = request.get_json()
		availability_key = client.key("availability", int(availability_id))
		availability = client.get(key=availability_key)
		if availability != None:
			if availability['owner'] != sub:
				return (jsonify({'Error': 'This availability is owned by someone else'}), 403)
			if "Type" in content and "Sunday_AM" in content and "Sunday_PM" in content and "Monday_AM" in content and "Monday_PM" in content and "Tuesday_AM" in content and "Tuesday_PM" in content and "Wednesday_AM" in content and "Wednesday_PM" in content and "Thursday_AM" in content and "Thursday_PM" in content and "Friday_AM" in content and "Friday_PM" in content and "Saturday_AM" in content and "Saturday_PM" in content:
				availability.update({"Type": content["Type"], "Sunday_AM": content["Sunday_AM"],"Sunday_PM": content["Sunday_PM"],"Monday_AM": content["Monday_AM"], "Monday_PM": content["Monday_PM"],"Tuesday_AM": content["Tuesday_AM"], "Tuesday_PM": content["Tuesday_PM"], "Wednesday_AM": content["Wednesday_AM"], "Wednesday_PM": content["Wednesday_PM"],"Thursday_AM": content["Thursday_AM"], "Thursday_PM": content["Thursday_PM"],"Friday_AM": content["Friday_AM"], "Friday_PM": content["Friday_PM"],"Saturday_AM": content["Saturday_AM"], "Saturday_PM": content["Saturday_PM"]})
				client.put(availability)
				availability["id"] = id
				availability["self"] = request.url + '/' + str(availability.key.id)
				res = make_response(json2html.convert(json = jsonify('')))
				res.headers.set('Location', availability["self"])
				res.status_code = 303
				return res
			else:
				return (jsonify({"Error": "PUT requires updating all of the required attributes"}), 400)	
		else:
			return (jsonify({"Error": "No availability with this availability_id exists"}), 404)


	else:
		return "Method not allowed", 405

@app.route('/schedules', methods=['POST','GET', "PUT", "PATCH"])
def schedules_get_post():
	if request.method == 'POST':
		
		token = request.headers.get('Authorization')
		
		if token:
			token = token.split(" ")[1]

			try:
				id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
				sub = id_info['sub']
				email = id_info['email']
			except:
				return (jsonify({"Error": "Invalid JWT"}), 401)
		else:
			return (jsonify({"Error": "JWT not found"}), 401)

		content = request.get_json()
		
		if "Day" in content and "Date" in content and "Shift" in content:
			
			new_schedule = datastore.entity.Entity(key=client.key("schedule"))
			new_schedule.update({"Day": content["Day"],"Date": content["Date"],"Shift": content["Shift"], "Availabilities": [], "Unavailabilities": [], "owner": sub, "email": email})
			query = client.query(kind='schedule')
			day_date_shifts = [entity["Day"] + entity["Date"] + entity["Shift"] for entity in query.fetch()]
			if (content["Day"] + content["Date"] + content["Shift"]) in day_date_shifts:
				return (jsonify({"Error": "A schedule for that day, date and shift already exists"}), 403)
			client.put(new_schedule)
			new_schedule['id'] = new_schedule.key.id
			new_schedule['self'] = request.url + '/' + str(new_schedule.key.id)
			return (jsonify(new_schedule), 201)
		else:
			return (jsonify({"Error": "The request object is missing at least one of the required attributes"}), 400)
	elif request.method == 'GET':

		query = client.query(kind="schedule")
		q_limit = int(request.args.get('limit', '5'))
		q_offset = int(request.args.get('offset', '0'))
		l_iterator = query.fetch(limit= q_limit, offset=q_offset)
		pages = l_iterator.pages
		results = list(next(pages))
		if l_iterator.next_page_token:
			next_offset = q_offset + q_limit
			next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
		else:
			next_url = None
		for e in results:
			e["id"] = e.key.id
			e["self"] = request.url + '/' + str(e.key.id)
		output = {"schedules": results}
		output['total'] = len(list(query.fetch()))
		if next_url:
			output["next"] = next_url

		return (jsonify(output), 200)

	else:
		return "Method not allowed", 405

@app.route('/schedules/<schedule_id>', methods=['PUT', 'PATCH', 'DELETE'])
def put_patch_delete_delete_schedule(schedule_id):
	if request.method == 'DELETE':
		token = request.headers.get('Authorization')
		if token:
			token = token.split(" ")[1]
			try:
				id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
				sub = id_info['sub']
			except:
				return (jsonify({"Error": "Invalid JWT"}), 401)
		else:
			return (jsonify({"Error": "JWT not found"}), 401)
		
		schedule_key = client.key("schedule", int(schedule_id))
		schedule = client.get(key=schedule_key)
		if schedule == None:
			return (jsonify({'Error': 'No schedule with this schedule_id exists'}), 404)
		elif schedule['owner'] != sub:
			return (jsonify({'Error': 'This schedule is owned by someone else'}), 403)

		if len(schedule['Availabilities']) > 0:
			for availability in schedule['Availabilities']:
				availability_key = client.key("availability", int(availability['id']))
				availability_obj = client.get(key=availability_key)
				availability_obj['Available'].remove({"id": schedule.key.id, "Day": schedule["Day"], "Date": schedule["Date"], "Shift": schedule["Shift"]})
				client.put(availability_obj)
		if len(schedule['Unavailabilities']) > 0:
			for availability in schedule['Unavailabilities']:
				availability_key = client.key("availability", int(availability['id']))
				availability_obj = client.get(key=availability_key)
				availability_obj['Unavailable'].remove({"id": schedule.key.id, "Day": schedule["Day"], "Date": schedule["Date"], "Shift": schedule["Shift"]})
				client.put(availability_obj)
		client.delete(schedule_key)
		return (jsonify(''), 204)

	elif request.method == 'PATCH':
		token = request.headers.get('Authorization')
		if token:
			token = token.split(" ")[1]
			try:
				id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
				sub = id_info['sub']
			except:
				return (jsonify({"Error": "Invalid JWT"}), 401)
		else:
			return (jsonify({"Error": "JWT not found"}), 401)

		content = request.get_json()
		schedule_key = client.key("schedule", int(schedule_id))
		schedule = client.get(key=schedule_key)
		if schedule == None:
			return (jsonify({'Error': 'No schedule with this schedule_id exists'}), 404)
		elif schedule['owner'] != sub:
			return (jsonify({'Error': 'This schedule is owned by someone else'}), 403)
		if schedule['owner'] != sub:
			return (jsonify({'Error': 'This schedule is owned by someone else'}), 403)
		
		if len(content) > 1:
				return (jsonify({"Error": "PATCH may only be used to update one attribute at a time"}), 400)
		if "id" in content:
			return (jsonify({"Error": "Not allowed to change id"}), 400)
		if "email" in content:
			return (jsonify({"Error": "Not allowed to change email"}), 400)
		if "owner" in content:
			return (jsonify({"Error": "Not allowed to change owner"}), 400)
		if len(schedule["Availabilities"]) > 0 or len(schedule["Unavailabilities"]) > 0:
			return (jsonify({"Error": "Not allowed to patch schedules after an availability has been assigned"}), 400)
		
		if "Date" in content:
			query = client.query(kind='schedule')
			day_date_shifts = [entity["Day"] + entity["Date"] + entity["Shift"] for entity in query.fetch()]
			if (schedule["Day"] + content["Date"] + schedule["Shift"]) in day_date_shifts:
				return (jsonify({"Error": "A schedule for that day, date and shift already exists"}), 403)
			schedule.update({"Date": content["Date"]})
			client.put(schedule)
			schedule["id"] = int(schedule_id)
			schedule["self"] = request.url
			return (jsonify(schedule), 200)
		if "Day" in content:
			query = client.query(kind='schedule')
			day_date_shifts = [entity["Day"] + entity["Date"] + entity["Shift"] for entity in query.fetch()]
			if (content["Day"] + schedule["Date"] + schedule["Shift"]) in day_date_shifts:
				return (jsonify({"Error": "A schedule for that day, date and shift already exists"}), 403)
			schedule.update({"Day": content["Day"]})
			client.put(schedule)
			schedule["id"] = int(schedule_id)
			schedule["self"] = request.url
			return (jsonify(schedule), 200)
		if "Shift" in content:
			query = client.query(kind='schedule')
			day_date_shifts = [entity["Day"] + entity["Date"] + entity["Shift"] for entity in query.fetch()]
			if (schedule["Day"] + schedule["Date"] + content["Shift"]) in day_date_shifts:
				return (jsonify({"Error": "A schedule for that day, date and shift already exists"}), 403)
			schedule.update({"Shift": content["Shift"]})
			client.put(schedule)
			schedule["id"] = int(schedule_id)
			schedule["self"] = request.url
			return (jsonify(schedule), 200)
		else:
			return (jsonify({"Error": "PATCH only allows updating Date, Day or Shift"}), 400)	

	elif request.method == 'PUT':
		token = request.headers.get('Authorization')
		if token:
			token = token.split(" ")[1]
			try:
				id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
				sub = id_info['sub']
			except:
				return (jsonify({"Error": "Invalid JWT"}), 401)
		else:
			return (jsonify({"Error": "JWT not found"}), 401)

		content = request.get_json()
		schedule_key = client.key("schedule", int(schedule_id))
		schedule = client.get(key=schedule_key)
		if schedule != None:
			if schedule['owner'] != sub:
				return (jsonify({'Error': 'This schedule is owned by someone else'}), 403)
			if "id" in content:
				return (jsonify({"Error": "Not allowed to change id"}), 400)
			if "email" in content:
				return (jsonify({"Error": "Not allowed to change email"}), 400)
			if "owner" in content:
				return (jsonify({"Error": "Not allowed to change owner"}), 400)
			if len(schedule["Availabilities"]) > 0 or len(schedule["Unavailabilities"]) > 0:
				return (jsonify({"Error": "Not allowed to patch schedules after an availability has been assigned"}), 400)
			if "Day" in content and "Date" in content and "Shift" in content:
				# Test unique name
				query = client.query(kind='schedule')
				day_date_shifts = [entity["Day"] + entity["Date"] + entity["Shift"] for entity in query.fetch()]
				if (content["Day"] + content["Date"] + content["Shift"]) in day_date_shifts:
					return (jsonify({"Error": "A schedule for that day, date and shift already exists"}), 403)
				schedule.update({"Day": content["Day"],"Date": content["Date"],"Shift": content["Shift"]})				
				client.put(schedule)
				schedule["id"] = id
				schedule["self"] = request.url + '/' + str(schedule.key.id)
				res = make_response(json2html.convert(json = jsonify('')))
				res.headers.set('Location', schedule["self"])
				res.status_code = 303
				return res
			else:
				return (jsonify({"Error": "PUT requires updating all of the required attributes"}), 400)
		else:
			return (jsonify({'Error': 'No schedule with this schedule_id exists'}), 404)
	else:
		return "Method not allowed", 405


@app.route('/schedules/<sid>/availability/<aid>', methods=['PUT','DELETE'])
def add_delete_schedule_availability(sid, aid):
	if request.method == 'PUT':
		schedule_key = client.key("schedule", int(sid))
		schedule = client.get(key=schedule_key)
		availability_key = client.key("availability", int(aid))
		availability = client.get(key=availability_key)
		if schedule != None and availability != None:
			if availability[schedule["Day"]+"_"+schedule["Shift"]] == "Available":
				schedule['Availabilities'].append({"id": availability.key.id, "email": availability["email"]})
				availability['Available'].append({"id": schedule.key.id, "Day": schedule["Day"], "Date": schedule["Date"], "Shift": schedule["Shift"]})
				client.put(schedule)
				client.put(availability)
			else:
				schedule['Unavailabilities'].append({"id": availability.key.id, "email": availability["email"]})
				availability['Unavailable'].append({"id": schedule.key.id, "Day": schedule["Day"], "Date": schedule["Date"], "Shift": schedule["Shift"]})
				client.put(schedule)
				client.put(availability)
			return(jsonify(''), 204)
		else:
			return (jsonify({"Error": "The specified schedule and/or availability does not exist"}), 404)
	if request.method == 'DELETE':
		schedule_key = client.key("schedule", int(sid))
		schedule = client.get(key=schedule_key)
		availability_key = client.key("availability", int(aid))
		availability = client.get(key=availability_key)
		if schedule != None and availability != None:
			if 'Availabilities' in schedule.keys() and len(schedule["Availabilities"]) != 0:
				schedule['Availabilities'].remove({"id": availability.key.id, "email": availability["email"]})
				availability['Available'].remove({"id": schedule.key.id, "Day": schedule["Day"], "Date": schedule["Date"], "Shift": schedule["Shift"]})
				client.put(schedule)
				client.put(availability)
			if 'Unavailabilities' in schedule.keys() and len(schedule["Unavailabilities"]) != 0:
				schedule['Unavailabilities'].remove({"id": availability.key.id, "email": availability["email"]})
				availability['Unavailable'].remove({"id": schedule.key.id, "Day": schedule["Day"], "Date": schedule["Date"], "Shift": schedule["Shift"]})
				client.put(schedule)
				client.put(availability)
			return(jsonify(''),204)
		else:
			return (jsonify({"Error": "No schedule with this schedule_id is availabilityed with the availability with this availability_id"}), 404)
	else:
		return "Method not allowed", 405

if __name__ == '__main__':
	app.run(host='127.0.0.1', port=8080, debug=True)
