import json
import requests
from bs4 import BeautifulSoup

url = "https://radiovietnamonline.com/"

headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
if not script_tag:
    raise ValueError("Không tìm thấy thẻ script __NEXT_DATA__")

data = json.loads(script_tag.string)

radios = data["props"]["pageProps"]["radios"]

with open("vietnam.m3u8", "w", encoding="utf-8") as f:
    f.write('#EXTM3U url-tvg="https://raw.githubusercontent.com/brianhuster/radio/refs/heads/main/schedule/vietnam.xml"\n')
    for r in radios:
        name = r.get("name", "")
        logo = r.get("imageUrl", "")
        stream = r.get("streamUrl", "")
        id = r.get("Url", "")

        if stream.startswith("/"):
            stream = url + stream

        f.write(f'#EXTINF:-1 tvg-id="{id}" tvg-logo="{logo}" group-title="Radio",{name.replace("-", "")}\n')
        f.write(f"{stream}\n")
