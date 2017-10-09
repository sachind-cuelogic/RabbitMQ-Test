import datetime
import time
import json
import pika
import csv


def createConnection():
	# import pdb; pdb.set_trace()
	credentials = pika.PlainCredentials('guest','guest')
	connection = pika.BlockingConnection(pika.ConnectionParameters(credentials=credentials, host='localhost', port=5672))
	channel = connection.channel()


	reader = csv.DictReader(open('response.csv', 'rb'))
	dict_list = []
	for line in reader:
		print line['companyName']
		line['requestUpdatedTime'] = str(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
		channel.basic_publish(exchange='domainExchange', routing_key='domainExchange', body=json.dumps(line), properties=pika.BasicProperties(delivery_mode=2))

		time.sleep(2)
	connection.close()


if __name__ == "__main__":
    print "inside main"
    createConnection()