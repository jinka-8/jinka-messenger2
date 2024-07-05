from flask import Flask, render_template, request, jsonify, redirect
from kafka import KafkaProducer
import json
from pymongo import MongoClient

app = Flask(__name__)
producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client.message_db
messages_collection = db.messages


@app.route('/')
def home(request):

    if request.method=="GET":
        return render_template("root.html")

    data=request.json()

    print(data)

    if 'name' in data:
        #save ip and name into the database
        return redirect("/messages")



@app.route('/messages')
def index():
    # Retrieve only the last 6 messages in descending order
    messages = list(messages_collection.find().sort('_id', -1).limit(6))
    return render_template('index.html', messages=messages)

@app.route('/send', methods=['POST'])
def send_message():
    message = request.form['message']
    ip_address = request.remote_addr
    producer.send('chat', {'message': message, 'ip_address': ip_address})
    return jsonify({'status': 'Message sent!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


