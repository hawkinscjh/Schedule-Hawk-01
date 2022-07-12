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

#session.init_app(app)

#client_id = constants.client_id
#client_secret = constants.client_secret

client_id = "1000217580465-vv538d3or9de5qahi8a6qsbcmrufn4ch.apps.googleusercontent.com"
client_secret = "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"

#redirect_uri = "https://schedule-hawk-01.uc.r.appspot.com/oauth"
redirect_uri = 'http://127.0.0.1:8080/oauth'

scope = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'openid']
oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)

@app.route('/')
def index():
	authorization_url, state = oauth.authorization_url('https://accounts.google.com/o/oauth2/auth', access_type="offline", prompt="select_account")
	return render_template('oauth.html')
	#return render_template('index.html', authorization_url=authorization_url)
	#return '<h1>Welcome</h1>\n <p>Sign-in to Google <a href=%s>here</a></p>' % authorization_url

@app.route('/oauth')
def oauthroute():
	token = oauth.fetch_token('https://accounts.google.com/o/oauth2/token', authorization_response=request.url, client_secret=client_secret)
	id_info = id_token.verify_oauth2_token(token['id_token'], requests.Request(), client_id)
	# clock_skew_in_seconds=30
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

@app.route('/schedules', methods=['POST','GET', "PUT", "PATCH"])
def schedules_get_post():
	if request.method == 'POST':
		
		content = request.form

		
		if "Date" in content and "Shift" in content:
			
			new_schedule = datastore.entity.Entity(key=client.key("schedule"))
			new_schedule.update({"Date": content["Date"],"Shift": content["Shift"]})
			query = client.query(kind='schedule')
			date_shifts = [entity["Date"] + entity["Shift"] for entity in query.fetch()]
			if (content["Date"] + content["Shift"]) in date_shifts:
				flash("Schedule is already present", category='error')
				query = client.query(kind="schedule")
				results = list(query.fetch())
				return render_template('full_schedule.html', data=results)
			client.put(new_schedule)
			new_schedule['id'] = new_schedule.key.id
			new_schedule['self'] = request.url + '/' + str(new_schedule.key.id)

			query = client.query(kind="schedule")
			results = list(query.fetch())
			
			return render_template('full_schedule.html', data=results)
		else:
			return (jsonify({"Error": "The request object is missing at least one of the required attributes"}), 400)
	elif request.method == 'GET':

		query = client.query(kind="schedule")
		results = list(query.fetch())

		return render_template('full_schedule.html', data=results)

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

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)