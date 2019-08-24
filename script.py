import json

from kafka import KafkaConsumer
from cassandra.cluster import Cluster

from settings import BTC_BLOCK_TOPIC, BOOSTRAP_SERVER, CASSANDRA_HOST, CASSANDRA_KEYSPACE

consumer = KafkaConsumer(
    BTC_BLOCK_TOPIC, bootstrap_servers="%s"  % (BOOSTRAP_SERVER))

cluster = Cluster([CASSANDRA_HOST])
session = cluster.connect()

session.execute("CREATE KEYSPACE IF NOT EXISTS bitcoin WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 } AND durable_writes = true;")

session.execute("USE bitcoin;")

session.execute("CREATE TABLE IF NOT EXISTS bitcoin.blocks (hash text, confirmations text, strippedsize text, size text, weight text, height text, version text, version_hex text, merkleroot text, time text, mediantime text, nonce text, bits text, difficulty text, chainwork text, n_tx text, previousblockhash text, nextblockhash text, PRIMARY KEY (hash, height)) WITH CLUSTERING ORDER BY (height DESC);")
session.execute("CREATE TABLE IF NOT EXISTS bitcoin.transactions (hash text, version text, size text, vsize text, weight text, locktime text, vin text, vout text, block_height text, PRIMARY KEY (hash, block_height)) WITH CLUSTERING ORDER BY (block_height DESC);")

session.execute("CREATE CUSTOM INDEX vout_details ON bitcoin.transactions (vout) USING 'org.apache.cassandra.index.sasi.SASIIndex' WITH OPTIONS = { 'mode': 'CONTAINS', 'analyzer_class': 'org.apache.cassandra.index.sasi.analyzer.NonTokenizingAnalyzer', 'case_sensitive': 'false'};")

for message in consumer:
    entry = json.loads(message.value)
    session.execute(
        """
INSERT INTO bitcoin.blocks (hash, confirmations, strippedsize, size, weight, height, version, version_hex, merkleroot, time, mediantime, nonce, bits, difficulty, chainwork, n_tx, previousblockhash, nextblockhash)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
""",
        (str(entry['hash']), str(entry['confirmations']), str(entry['strippedsize']), str(entry['size']), str(entry['weight']), str(entry['height']), str(entry['version']), str(entry['versionHex']), str(entry['merkleroot']), str(entry['time']), str(entry['mediantime']), str(entry['nonce']), str(entry['bits']), str(entry['difficulty']), str(entry['chainwork']), str(entry['nTx']), str(entry['previousblockhash']), str(entry['nextblockhash'])))

    for tx in entry['tx']:
        session.execute(
            """
    INSERT INTO bitcoin.transactions (hash, version, size, vsize, weight, locktime, vin, vout, block_height)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """,
            (str(tx['hash']), str(tx['version']), str(tx['size']), str(tx['vsize']), str(tx['weight']), str(tx['locktime']), str(json.dumps(tx['vin']).encode('utf-8')), str(json.dumps(tx['vout']).encode('utf-8')), str(entry['height'])))
