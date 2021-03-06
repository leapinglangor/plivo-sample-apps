from flask import Flask, request, make_response
import plivoxml, plivo
import os


#Heroku or wherever App base URL
SERVER_NAME = 'asd-sdf-1234.herokuapp.com'
CONF_CODE = '1234'
#Moderator Phone No.
MODERATOR_ID = '1234567890'
#For SMS, Auth from Plivo
auth_id = ""
auth_token = ""

app = Flask(__name__)

@app.route('/conf-get-input/', methods=['GET', 'POST'])
def conf_get_input():
    print request.method
    if request.method == 'GET':
        caller = request.args.get('From', '')
        called = request.args.get('To', '')
    elif request.method == 'POST':
        caller = request.form.get('From', '')
        called = request.args.get('To', '')
    response = plivoxml.Response()
    response.addSpeak('Hello. If you know your conference pin, please enter')
    getdigits = response.addGetDigits(
        action='http://' + SERVER_NAME + '/conf-verify-input/%s/%s' % (caller, called),
        timeout='15',
        finishOnKey='#'
    )
    response.addSpeak(body="Input not received. Thank you.")
    xml_response = make_response(response.to_xml())
    xml_response.headers["Content-type"] = "text/xml"
    return xml_response

@app.route('/conf-verify-input/<caller>/<called>', methods=['GET', 'POST'])
def conf_verify_input(caller, called):
    if request.method == 'GET':
        user_input = request.args.get('Digits', '')
    elif request.method == 'POST':
        user_input = request.form.get('Digits', '')
        
    response = plivoxml.Response()
    if CONF_CODE != user_input:
        response.addSpeak('There is no conference running with the code ' + user_input)
        response.addHangup()
    else:
	callbackurl=""
	if caller == MODERATOR_ID:
		startonenter="true"
	else:
		startonenter="false"
#		Don't bother the mod if hes already in
		callbackurl='http://' + SERVER_NAME + '/conf-action/%s/%s' %(caller,called)

        response.addConference(
            body=CONF_CODE,
            callbackUrl=callbackurl,
	    startConferenceOnEnter = startonenter,
	    endConferenceOnExit = startonenter
        )

    xml_response = make_response(response.to_xml())
    xml_response.headers["Content-type"] = "text/xml"
    return xml_response

@app.route('/conf-action/<caller>/<called>', methods=['GET', 'POST'])
def conf_action(caller, called):
    conf_name = request.form.get('ConferenceName', '')
    conf_uuid = request.form.get('ConferenceUUID', '')
    member_uuid = request.form.get('ConferenceMemberID', '')
##    This Block is made for use with plivo RestAPI
    p = plivo.RestAPI(auth_id, auth_token)
    print p
    # Send a SMS
    params = {
        'src': called, # App's No.
        'dst' : MODERATOR_ID, # Mod's Number
        'text' : "Hi, Moderator. The user with ID %s has just entered the conference. To send a message to this user, reply to this message as \"%s I'm running late\""%(caller,member_uuid),
        'type' : "sms"
    }

    response = p.send_message(params)
    return "Message sent to moderator"

##     And this one for use with restXML, doesn't send for some reason...
#    response = plivoxml.Response()
#
#    response.addMessage(
#            body="Hi, Moderator. The user with ID %s has just entered the conference. To send a message to this user, reply to this message as \"%s I'm running late\"" % (caller,member_uuid),
#	    src = called, # Caller Id
#            dst = MODERATOR_ID, # User Number to Call
#            type = "sms"
#    )
#    xml_response = make_response(response.to_xml())
#    xml_response.headers["Content-type"] = "text/xml"
#    return xml_response

@app.route('/mesg-action/', methods=['POST'])
def mesg_action():
    From = request.form.get('From','')
    to = request.form.get('To','')
    text = request.form.get('Text','')
#   Not a good idea when making do with demo sms app
    if( From == MODERATOR_ID):
	    text = text.strip("\"")
	    temp = text.split(" ")
	    rxr = temp[0]
	    mesg = " ".join(temp[1:])
	    p = plivo.RestAPI(auth_id, auth_token)
	
	    # SPeak to member
	    params = {
		'conference_name' : CONF_CODE,
		'member_id' : rxr,
	        'text' : mesg
	    }

	    response = p.speak_member(params)
	    return "Speaking to member "
    return "Anauthorized Message"

@app.route('/call-term-action/', methods=['POST'])
def call_term_action():
	return "Call terminated."


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
