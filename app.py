from flask import Flask, request, render_template, redirect, jsonify
from pymongo import MongoClient
from kafka import KafkaProducer
import json
import datetime
from bson import ObjectId
import os

app = Flask(__name__)

# Setup MongoDB client
client = MongoClient('localhost', 27017)
db = client['messaging_app']
names_collection = db['names']
messages_collection = db['messages']

# Set the upload folder for screenshots
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Setup Kafka producer
producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

@app.route('/', methods=['GET', 'POST'])
def home():

    ip_address = request.remote_addr

    result = names_collection.find_one({'ip':ip_address})

    if result:
        return redirect("/messages")

    if request.method == 'GET':
        error = request.args.get("error", "")
        return render_template("root.html", error=error)
    elif request.method == 'POST':
        data = request.form
        if 'name' in data:
            # Save the IP and name into the database
            name = data['name']
            ip_address = request.remote_addr

            result = names_collection.find_one({'ip':ip_address})

            if result:
                return render_template()

            names_collection.update_one({'ip': ip_address}, {'$set': {'name': name}}, upsert=True)
            
            return redirect("/messages")
        else:
            return jsonify({"error": "Name not provided"}), 400

@app.route('/messages')
def index():

    ip_address = request.remote_addr

    result = names_collection.find_one({'ip':ip_address})

    no_name=""
    welcome=""

    message_id = request.args.get("id", "")

    if message_id:
        message_id = ObjectId(message_id)

    if not result:
        no_name = "Enter your name!"

    else:
        welcome = result["name"]

    
    if message_id:
        messages = list(messages_collection.find({"_id":{"$gt":message_id}}).sort('_id', -1).limit(1))
        

        for message in messages:
            message['_id'] = str(message['_id'])
            message["created_at"] = message["created_at"].strftime('%a, %d %b %Y %H:%M:%S')

        if not messages:
            return jsonify({"data":""})
        
        return jsonify({"data":messages})
    # Retrieve the last 6 messages in descending order
    messages = list(messages_collection.find().sort('_id', -1).limit(6))

    for message in messages:
            message['_id'] = str(message['_id'])
            message["created_at"] = message["created_at"].strftime('%a, %d %b %Y %H:%M:%S')

    # Map IP addresses to names
    result = []
    for message in messages:
        ip_address = message.get('ip_address')
        result.append(message)
    
    # print(render_template('index.html', context=result))
    
    return render_template('index.html', messages=result, no_name=no_name, welcome=welcome)

@app.route('/send', methods=['POST'])
def send_message():
    message = request.form['message']
    ip_address = request.remote_addr
    # producer.send('chat', {'message': message, 'ip_address': ip_address})
    result = names_collection.find_one({'ip':ip_address})

    if not result:
        error_message = "Please enter your name first!!"
        return redirect("/?error=Please enter your name first!!")

    name = result["name"]
    messages_collection.insert_one({"created_at":datetime.datetime.now(), "name":name, "message":message})
    return jsonify({'status': 'Message sent!'})


@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'GET':
        return render_template("report.html")
    elif request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        issue = request.form['issue']
        screenshot = request.files['screenshot']

        # Save screenshot file
        if screenshot:
            screenshot_path = os.path.join(app.config['UPLOAD_FOLDER'], screenshot.filename)
            screenshot.save(screenshot_path)
        else:
            screenshot_path = None

        # Save report to MongoDB
        report_data = {
            'name': name,
            'email': email,
            'issue': issue,
            'screenshot': screenshot_path
        }
        db.reports_collection.insert_one(report_data)

        return redirect("/messages")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
