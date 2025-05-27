from kibana_api import Kibana

URL = "http://kibana-logging-devops-pcto.stella.cloud.az.cgm.ag"
USERNAME = "kibana"
PASSWORD = "kibanaPassword"

kibana = Kibana(base_url=URL, username=USERNAME, password=PASSWORD)

try:
    response = kibana.space().all()

    if response.status_code == 200:
        print("Connected to Kibana successfully!")
        spaces = response.json()
        print("Available spaces:")
        for space in spaces:
            print(f"- ID: {space['id']}, Name: {space['name']}")
    else:
        print(
            f"Connected, but received unexpected status code: {response.status_code}")

except Exception as e:
    print("Failed to connect to Kibana:", str(e))
