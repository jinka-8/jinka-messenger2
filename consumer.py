from kafka import KafkaConsumer
import json
from pymongo import MongoClient

consumer = KafkaConsumer('chat', bootstrap_servers='localhost:9092', value_deserializer=lambda x: json.loads(x.decode('utf-8')))

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client.message_db
messages_collection = db.messages

for message in consumer:
    message_value = message.value['message']
    ip_address = message.value['ip_address']
    messages_collection.insert_one({'message': message_value, 'ip_address': ip_address})
    print(f"Stored message: {message_value} from {ip_address}")
