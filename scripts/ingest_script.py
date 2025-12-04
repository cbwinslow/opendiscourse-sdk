cd /home/cbwinslow/Videos/opendiscourse && source test_env/bin/activate && python3 -c "
import requests
import psycopg2
import json
import time

# Database connection
conn = psycopg2.connect(dbname='opendiscourse', user='cbwinslow', host='/var/run/postgresql')
conn.autocommit = True  # Avoid transaction issues
cursor = conn.cursor()

# API setup
api_key = 'U71JFZEqNsiSranCdbrj4pZaobtoMtAnl18cIJc2'
headers = {'X-API-Key': api_key, 'Accept': 'application/json'}

# Get bills from Congress 118 (different from existing 119 data)
print('Starting Congress 118 bills ingestion...')
base_url = 'https://api.congress.gov/v3/bill'
params = {'congress': 118, 'limit': 100}
offset = 0
total_ingested = 0

for batch in range(3):  # Just 3 batches for testing
    params['offset'] = offset
    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        bills = data.get('bills', [])

        batch_ingested = 0
        for bill in bills:
            try:
                cursor.execute('''
                    INSERT INTO congress.bills (congress, number, type, title, origin_chamber, latest_action, update_date, url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (congress, number, type) DO NOTHING
                ''', (
                    bill.get('congress'),
                    bill.get('number'),
                    bill.get('type'),
                    bill.get('title', '')[:500],  # Truncate long titles
                    bill.get('originChamber'),
                    json.dumps(bill.get('latestAction', {})),
                    bill.get('updateDate'),
                    bill.get('url')
                ))
                batch_ingested += 1
            except Exception as e:
                print(f'Error inserting bill {bill.get(\"number\", \"unknown\")}: {e}')

        print(f'Batch {batch+1}: Processed {len(bills)} bills, ingested {batch_ingested}')
        total_ingested += batch_ingested
        offset += len(bills)

        if len(bills) < 100:
            break

    else:
        print(f'API Error: {response.status_code}')
        break

    time.sleep(1)

print(f'Ingestion complete. Total bills ingested: {total_ingested}')
cursor.close()
conn.close()
"
