import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
import json

OUTPUT_FILE = "schedule/vietnam.xml"

HANOI_CHANNELS = {
    "FM90": "dai-phat-thanh-Ha-Noi-90MHz",
    "FM96": "dai-phat-thanh-Ha-Noi-96MHz",
}

# VOH channel map (id → channelNewId)
VOH_CHANNELS = {
    "dai-phat-thanh-VOH-99.9Mhz": 999,
    "dai-phat-thanh-VOH-95.6Mhz": 956,
    "dai-phat-thanh-VOH-87.7Mhz": 877,
    "dai-phat-thanh-VOH-610KHz": 610,
}

VOH_BUILD_PAGE = "https://voh.com.vn/radio/lich-phat-song-fm-999-02221123001000999.html"


def get_today_vn():
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    return datetime.now(tz).strftime("%d_%m_%Y")


def fmt_time(dt: datetime):
    return dt.strftime("%Y%m%d%H%M%S +0700")


def fetch_hanoionline():
    today = get_today_vn()
    progs = []
    for key, ch_id in HANOI_CHANNELS.items():
        url = f"https://hanoionline.vn/api/Schedule/listschedule/?key={
            key}_{today}"
        r = requests.get(url)
        data = r.json()
        items = data.get("Data", [])
        for item in items:
            start = datetime.fromisoformat(item["StartTime"])
            stop = datetime.fromisoformat(item["EndTime"])
            progs.append({
                "channel": ch_id,
                "title": item.get("Name", ""),
                "desc": item.get("Description", ""),
                "start": start,
                "stop": stop,
            })
    return progs


def get_voh_build_id():
    r = requests.get(VOH_BUILD_PAGE)
    soup = BeautifulSoup(r.text, "html.parser")
    script_tag = soup.find("script", id="__NEXT_DATA__")
    data = json.loads(script_tag.string)
    return data.get("buildId")


VOH_BASE_URL = f"https://voh.com.vn/_next/data/{
    get_voh_build_id()}/radios/schedule/schedule-detail.json"


def fetch_voh():
    progs = []
    for ch_id, freq in VOH_CHANNELS.items():
        url = f"{VOH_BASE_URL}?channelNewId={freq}"
        r = requests.get(url)
        data = r.json()
        schedule_list = (
            data.get("pageProps", {})
                .get("pageData", {})
                .get("chanelActive", {})
                .get("radioScheduleList", [])
        )
        for item in schedule_list:
            start = datetime.fromisoformat(item["broadcastFrom"])
            stop = datetime.fromisoformat(item["broadcastTo"])
            progs.append({
                "channel": ch_id,
                "title": item.get("radioTitle", ""),
                "desc": item.get("categoryTitle", ""),
                "start": start,
                "stop": stop,
            })
    return progs


def main():
    root = ET.Element("tv")

    all_programs = []
    all_programs.extend(fetch_hanoionline())
    all_programs.extend(fetch_voh())

    # Lấy danh sách channel duy nhất
    channels = {}
    for prog in all_programs:
        if prog["channel"] not in channels:
            channels[prog["channel"]] = prog["channel"]

    # Xuất channel
    for ch_id in channels.values():
        ch_elem = ET.SubElement(root, "channel", id=ch_id)
        ET.SubElement(ch_elem, "display-name").text = ch_id

    # Xuất chương trình
    for prog in all_programs:
        elem = ET.SubElement(
            root, "programme",
            start=fmt_time(prog["start"]),
            stop=fmt_time(prog["stop"]),
            channel=prog["channel"],
        )
        ET.SubElement(elem, "title", lang="vi").text = prog["title"]
        if prog["desc"]:
            ET.SubElement(elem, "desc", lang="vi").text = prog["desc"]

    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
