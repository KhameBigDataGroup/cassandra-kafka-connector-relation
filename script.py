import json

from kafka import KafkaConsumer
from cassandra.cluster import Cluster

from settings import KAFKA_TOPIC, BOOSTRAP_SERVER, CASSANDRA_HOST, CASSANDRA_KEYSPACE

consumer = KafkaConsumer(
    KAFKA_TOPIC, bootstrap_servers="%s"  % (BOOSTRAP_SERVER))

cluster = Cluster([CASSANDRA_HOST])
session = cluster.connect()

session.execute("CREATE KEYSPACE IF NOT EXISTS bitcoin WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 } AND durable_writes = true;")

session.execute("USE bitcoin;")

session.execute("CREATE TABLE IF NOT EXISTS bitcoin.relation (block_hash text  PRIMARY KEY, transaction_hashes text );")

for message in consumer:
    entry = json.loads(message.value)
    block_hash = entry['hash']
    transaction_hashes = []

    for tx in entry['tx']:
        transaction_hashes.append(tx['hash'])
    session.execute(
        """
INSERT INTO bitcoin.relation (block_hash, transaction_hashes)
VALUES (%s,%s)
""",
        (str(block_hash), str(json.dumps(transaction_hashes))))
