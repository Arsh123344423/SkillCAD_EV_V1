import time, json
from confluent_kafka import Producer
from APM.simulator import EV
from APM.degradation_accuracy_local import get_prediction

producer = Producer({'bootstrap.servers': 'localhost:9092'})

def delivery_report(err, msg):
    if err is not None:
        print(f'Delivery failed: {err}')
    else:
        print(f'Delivered to {msg.topic()} [{msg.partition()}]')

TOPIC = "sensor-data"
DELAY_SECONDS = 1

vehicle = EV()

while True:
    telemetry = vehicle.update()
    data = get_prediction(telemetry)

    producer.produce(TOPIC, value=json.dumps(data), callback=delivery_report)
    producer.poll(0)

    time.sleep(DELAY_SECONDS)