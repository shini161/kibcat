import json
import prison
import urllib.parse


def encode_kibana_url(g_path, a_path, base_url):
    with open(g_path, "r") as f:
        g_obj = json.load(f)
    with open(a_path, "r") as f:
        a_obj = json.load(f)

    g_encoded = urllib.parse.quote(prison.dumps(g_obj))
    a_encoded = urllib.parse.quote(prison.dumps(a_obj))

    final_url = f"{base_url}#/?_g={g_encoded}&_a={a_encoded}"
    return final_url


if __name__ == "__main__":
    BASE_URL = "https://***REMOVED***/app/discover"
    url = encode_kibana_url("./url_g.json", "./url_a.json", BASE_URL)

    print("Kibana URL:")
    print(url)
