import json
import os
import requests
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables
QUEUE_TYPE = os.environ.get('QUEUE_TYPE', 'sqs')  # Default to SQS if not set
STOCK_API = os.environ.get('STOCK_API', 'alphavantage')  # Default to Alpha Vantage

# Initialize clients based on queue type
if QUEUE_TYPE == 'sqs':
    import boto3
    sqs = boto3.client('sqs')
elif QUEUE_TYPE == 'rabbitmq':
    import pika  # RabbitMQ client library
    rabbitmq_url = os.environ.get('RABBITMQ_URL')
    rabbitmq_queue = os.environ.get('RABBITMQ_QUEUE')
elif QUEUE_TYPE == 'ibm_mq':
    import ibm_boto3  # IBM MQ client library
    ibm_mq_url = os.environ.get('IBM_MQ_URL')
    ibm_mq_queue = os.environ.get('IBM_MQ_QUEUE')
    ibm_mq_client = ibm_boto3.client('mq')  # Adjust depending on the specific client you are using
else:
    logging.error(f"Invalid QUEUE_TYPE: {QUEUE_TYPE}. Must be 'sqs', 'rabbitmq', or 'ibm_mq'.")
    raise ValueError(f"Invalid QUEUE_TYPE: {QUEUE_TYPE}")

def fetch_stock_data():
    try:
        if STOCK_API == 'alphavantage':
            api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
            symbol = 'AAPL'  # Example symbol, replace with dynamic input if needed
            api_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&apikey={api_key}'
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            return [{'symbol': symbol, 'price': float(data['Time Series (1min)'][next(iter(data['Time Series (1min)']))]['1. open'])}]
        
        elif STOCK_API == 'iexcloud':
            api_key = os.environ.get('IEXCLOUD_API_KEY')
            symbol = 'AAPL'  # Example symbol, replace with dynamic input if needed
            api_url = f'https://cloud.iexapis.com/stable/stock/{symbol}/quote?token={api_key}'
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            return [{'symbol': symbol, 'price': data['latestPrice']}]

        elif STOCK_API == 'finnhub':
            api_key = os.environ.get('FINNHUB_API_KEY')
            symbol = 'AAPL'  # Example symbol, replace with dynamic input if needed
            api_url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}'
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            return [{'symbol': symbol, 'price': data['c']}]  # Current price

        else:
            logging.error(f"Invalid STOCK_API: {STOCK_API}. Must be 'alphavantage', 'iexcloud', or 'finnhub'.")
            raise ValueError(f"Invalid STOCK_API: {STOCK_API}")

    except requests.RequestException as e:
        logging.error(f"Error fetching stock data: {e}")
        return []

def main():
    while True:
        stock_data = fetch_stock_data()

        for stock in stock_data:
            stock_symbol = stock.get('symbol')
            price = stock.get('price')

            if stock_symbol is None or price is None:
                logging.warning("Stock data missing required fields.")
                continue
            
            # Prepare message
            message = json.dumps(stock)
            logging.info(f"Processing stock: {stock_symbol}, Price: {price}")

            # Send message to the appropriate queue
            try:
                if QUEUE_TYPE == 'sqs':
                    queue_url = determine_sqs_queue(price)
                    sqs.send_message(
                        QueueUrl=queue_url,
                        MessageBody=message
                    )
                    logging.info(f"Sent message to SQS queue: {queue_url}")
                elif QUEUE_TYPE == 'rabbitmq':
                    send_to_rabbitmq(message)
                elif QUEUE_TYPE == 'ibm_mq':
                    send_to_ibm_mq(message)
            except Exception as e:
                logging.error(f"Error sending message: {e}")

        time.sleep(60)  # Poll every 60 seconds

def determine_sqs_queue(price):
    # Example logic to route messages in SQS
    if price > 100:
        return 'high_price_queue_url'
    else:
        return 'low_price_queue_url'

def send_to_rabbitmq(message):
    try:
        connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_queue, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=rabbitmq_queue,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )
        connection.close()
        logging.info(f"Sent message to RabbitMQ queue: {rabbitmq_queue}")
    except Exception as e:
        logging.error(f"Error sending to RabbitMQ: {e}")

def send_to_ibm_mq(message):
    try:
        # Adjust this method based on the actual IBM MQ SDK or client you are using
        ibm_mq_client.send(
            QueueName=ibm_mq_queue,
            MessageBody=message
        )
        logging.info(f"Sent message to IBM MQ queue: {ibm_mq_queue}")
    except Exception as e:
        logging.error(f"Error sending to IBM MQ: {e}")

if __name__ == "__main__":
    main()
