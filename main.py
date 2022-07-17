from secrets import token_bytes
from google.cloud import datastore
from flask import Flask, request, jsonify, make_response, render_template, redirect, session, flash
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

app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

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

@app.route('/oauth')
def oauthroute():
	token = oauth.fetch_token('https://accounts.google.com/o/oauth2/token', authorization_response=request.url, client_secret=client_secret)
	id_info = id_token.verify_oauth2_token(token['id_token'], requests.Request(), client_id)
	# clock_skew_in_seconds=30
	query = client.query(kind="user")
	query.add_filter("sub", "=", id_info['sub'])
	result = list(query.fetch())

	if len(result) == 0:
		new_user = datastore.entity.Entity(key=client.key('user'))
		new_user.update({'email': id_info['email'], 'sub': id_info['sub']})
		client.put(new_user)
		return render_template('oauth.html', token=token['id_token'], sub=id_info['sub'], email=id_info['email'])
	elif len(result) == 1:
		return render_template('oauth.html', token=token['id_token'], sub=id_info['sub'], email=id_info['email'])


@app.route('/schedules', methods=['POST','GET', "PUT", "PATCH"])
def schedules_get_post():

	query = client.query(kind="profile")
	profiles = list(query.fetch())

	if request.method == 'POST':
	
		content = request.form
		
		if content["Date"] != '' and content["Shift"] != '':
			
			new_schedule = datastore.entity.Entity(key=client.key("schedule"))
			new_schedule.update({"Date": content["Date"],"Shift": content["Shift"], "Working": []})
			query = client.query(kind='schedule')
			date_shifts = [entity["Date"] + entity["Shift"] for entity in query.fetch()]
			if (content["Date"] + content["Shift"]) in date_shifts:
				flash("Schedule is already present", category='error')
				query = client.query(kind="schedule")
				query.order = ["Date"]
				results = list(query.fetch())
				return render_template('full_schedule.html', data=results)
			client.put(new_schedule)
			new_schedule['id'] = new_schedule.key.id
			new_schedule['self'] = request.url + '/' + str(new_schedule.key.id)

			query = client.query(kind="schedule")
			query.order = ["Date"]
			results = list(query.fetch())
			
			return render_template('full_schedule.html', data=results, profiles=profiles)
		else:
			flash("Schedule is missing a required attribute", category='error')
			query = client.query(kind="schedule")
			results = list(query.fetch())
			return render_template('full_schedule.html', data=results)
	elif request.method == 'GET':

		query = client.query(kind="schedule")
		query.order = ["Date"]
		results = list(query.fetch())

		return render_template('full_schedule.html', data=results)

	#elif request.method == 'PATCH':


	else:
		return "Method not allowed", 405

@app.route('/schedules/<sid>', methods=['POST','GET', "PUT", "PATCH"])
def schedule_get_post(sid):

	query = client.query(kind="profile")
	profiles = list(query.fetch())
	
	if request.method == 'GET':
		
		schedule_key = client.key("schedule", int(sid))
		schedule = client.get(key=schedule_key)

		query = client.query(kind="profile")
		profiles = list(query.fetch())

		return render_template('schedule.html', schedule=schedule, profiles=profiles)


	else:
		return "Method not allowed", 405

@app.route('/schedules/<sid>/profiles/<pid>', methods=['PUT','DELETE'])
def add_delete_schedule_profile(sid, pid):
	if request.method == 'PUT':
		schedule_key = client.key("schedule", int(sid))
		schedule = client.get(key=schedule_key)
		profile_key = client.key("profile", int(pid))
		profile = client.get(key=profile_key)
		if schedule != None and profile != None:
			schedule['Working'].append({"id": profile.key.id, "fName": profile['fName'], "lName": profile['lName'] ,"email": profile["email"]})
			profile['Schedule'].append({"id": schedule.key.id, "Date": schedule["Date"], "Shift": schedule["Shift"]})
			client.put(schedule)
			client.put(profile)
			return(jsonify(''), 204)
		else:
			return (jsonify({"Error": "The specified schedule and/or profile does not exist"}), 404)
	if request.method == 'DELETE':
		schedule_key = client.key("schedule", int(sid))
		schedule = client.get(key=schedule_key)
		profile_key = client.key("profile", int(pid))
		profile = client.get(key=profile_key)
		if schedule != None and profile != None:
			schedule['Working'].remove({"id": profile.key.id, "fName": profile['fName'], "lName": profile['lName'] ,"email": profile["email"]})
			profile['Schedule'].remove({"id": schedule.key.id, "Date": schedule["Date"], "Shift": schedule["Shift"]})
			client.put(schedule)
			client.put(profile)
			return(jsonify(''),204)
		else:
			return (jsonify({"Error": "No schedule with this schedule_id is associated with the profile with this profile_id"}), 404)
	else:
		return "Method not allowed", 405

@app.route('/schedules/delete-schedule', methods=['POST'])
def delete_schedule():
	if request.method == 'POST':
		jsonData = json.loads(request.data)
		schedule_id = jsonData['schedule_id']
		schedule_key = client.key("schedule", int(schedule_id))
		schedule = client.get(key=schedule_key)
		if schedule == None:
			return (jsonify({'Error': 'No schedule with this schedule_id exists'}), 404)
		client.delete(schedule_key)

		query = client.query(kind="schedule")
		results = list(query.fetch())

		return render_template('full_schedule.html', data=results)

	else:
		return "Method not allowed", 405

@app.route('/profiles', methods=['POST','GET', "PUT", "PATCH"])
def profiles():
	if request.method == 'POST':
	
		content = request.form
		
		if content["fName"] != '' and content["lName"] != '' and content["email"] != '' and content["phone"] != '':
			
			new_profile = datastore.entity.Entity(key=client.key("profile"))
			new_profile.update({"fName": content["fName"],"lName": content["lName"], "email": content["email"], "phone": content["phone"]})
			query = client.query(kind='profile')
			fName_lName_email_phone = [entity["fName"] + entity["lName"] + entity["email"] + entity["phone"] for entity in query.fetch()]
			if (content["fName"] + content["lName"] + content["email"] + content["phone"]) in fName_lName_email_phone:
				flash("User already has a profile", category='error')
				query = client.query(kind="profile")
				results = list(query.fetch())
				return render_template('profiles.html', data=results)
			client.put(new_profile)
			new_profile['id'] = new_profile.key.id
			new_profile['self'] = request.url + '/' + str(new_profile.key.id)
			new_profile.update({"id": new_profile.key.id})

			query = client.query(kind="profile")
			results = list(query.fetch())
			
			return render_template('profiles.html', data=results)
		else:
			flash("Must input all categories", category='error')
			query = client.query(kind="profile")
			results = list(query.fetch())
			return render_template('profiles.html', data=results)
	elif request.method == 'GET':

		query = client.query(kind="profile")
		results = list(query.fetch())

		return render_template('profiles.html', data=results)

	else:
		return "Method not allowed", 405

@app.route('/profiles/<pid>', methods=['GET', 'POST'])
def get_profile_id(pid):
	if request.method == 'GET':
			
		#query1 = client.query(kind="availabilities")
		#query1.add_filter("pid", "=", pid)
		#avails = list(query1.fetch())
		
		profile_key = client.key("profile", int(pid))
		profile = client.get(key=profile_key)
		print(profile['fName'])
		print(profile['lName'])
		#print(profile['id'])
		print(profile['email'])
		return render_template('user_profile.html', data=profile)
	else:
		return "Method not allowed", 405

@app.route('/profiles/delete-profile', methods=['POST'])
def delete_profile():
	if request.method == 'POST':
		jsonData = json.loads(request.data)
		print(jsonData)
		profile_id = jsonData['profile_id']
		profile_key = client.key("profile", int(profile_id))
		profile = client.get(key=profile_key)
		if profile == None:
			return (jsonify({'Error': 'No profile with this profile_id exists'}), 404)
		client.delete(profile_key)

		query = client.query(kind="profile")
		results = list(query.fetch())

		return render_template('profiles.html', data=results)

	else:
		return "Method not allowed", 405		

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)