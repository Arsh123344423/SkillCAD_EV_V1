# consumer_to_mongo.py
import os, json
from dotenv import load_dotenv
from confluent_kafka import Consumer
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "sensor-data")

consumer = Consumer({
    'bootstrap.servers': KAFKA_SERVERS,
    'group.id': 'mongo-writer',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe([TOPIC])

client = MongoClient(MONGO_URI)
db = client['users']
collection = db['sensor_data']

print(f"Connected to Mongo. Listening on topic '{TOPIC}'...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Error: {msg.error()}")
            continue

        data = json.loads(msg.value().decode('utf-8'))
        collection.insert_one(data)
        print(f"Inserted: {data}")

except KeyboardInterrupt:
    pass
finally:
    consumer.close()