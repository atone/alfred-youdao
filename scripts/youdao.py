import sys
import os
import re
import json

from urllib.parse import urlencode, quote

# Ensure the script can find the required modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import requests
from bs4 import BeautifulSoup
from workflow import Workflow


def get_query_language(query):
    if re.search(r"[\u4e00-\u9fa5]+", query):
        return "eng"
    elif re.search(r"[\uAC00-\uD7A3]+", query):
        return "ko"
    elif re.search(r"[\u3040-\u309F\u30A0-\u30FF]+", query):
        return "jap"
    else:
        return "eng"


def is_chinese(query):
    return bool(re.search(r"[\u4e00-\u9fa5]+", query))


def get_youdao_url(query):
    params = {
        "le": get_query_language(query),
        "q": query
    }
    url = "https://mobile.youdao.com/dict?" + urlencode(params)
    print(f"Requesting Youdao URL: {url}", file=sys.stderr)
    return url


def get_quicklook_url(query):
    return "https://www.youdao.com/w/" + quote(query)


def make_arg(*args):
    return "\0".join(args)


def get_youdao_response(query):
    url = get_youdao_url(query)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response
    except requests.RequestException:
        return None


def get_youdao_soup(response):
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except:
        return None


def add_translation(wf, query, soup):
    quicklookurl = get_quicklook_url(query)
    fanyi_content = soup.find('div', id='fanyi_contentWrp')
    if fanyi_content:
        translation = fanyi_content.find('p').find_next_sibling('p')
        if translation:
            title = translation.get_text(strip=True)
            wf.add_item(title=title, subtitle=query, arg=make_arg(query, title), quicklookurl=quicklookurl)


def add_phonetic(wf, query, soup):
    quicklookurl = get_quicklook_url(query)
    subtitle = query if is_chinese(query) else '按 ↩︎ 听取发音'
    pronunciations = []
    for span in soup.find_all('span', class_='phonetic'):
        text = " ".join(span.parent.stripped_strings)
        pronunciations.append(text)
    title = '；'.join(pronunciations)
    if title:
        wf.add_item(title=title, subtitle=subtitle, arg=make_arg(query, title), icon="phonetic", quicklookurl=quicklookurl)


def regroup(s: str, max_length: int) -> list[str]:
    parts = s.split('；')
    result = []
    current_segment = ""

    for part in parts:
        if not current_segment:
            current_segment = part
        elif len(current_segment) + 1 + len(part) <= max_length:
            current_segment += "；" + part
        else:
            result.append(current_segment)
            current_segment = part

    if current_segment:
        result.append(current_segment)

    return result

def add_explains(wf, query, soup):
    quicklookurl = get_quicklook_url(query)
    if ec_content := soup.find('div', id='ec_contentWrp'):
        definitions = [li.get_text(strip=True) for li in ec_content.find_all('li')]
        for definition in definitions:
            if len(definition) > 27:
                parts = regroup(definition, 27)
                wf.add_item(title=parts[0], subtitle="；".join(parts[1:]), arg=make_arg(query, definition), quicklookurl=quicklookurl)
            else:
                wf.add_item(title=definition, subtitle="基本释义", arg=make_arg(query, definition), quicklookurl=quicklookurl)
    elif ce_content := soup.find('div', id='ce_contentWrp'):
        explanations = [a.get_text(strip=True) for a in ce_content.find_all('a', 'clickable')]
        for explanation in explanations:
            wf.add_item(title=explanation, subtitle="按 ⇥ 查询", arg=make_arg(explanation, explanation), quicklookurl=quicklookurl, autocomplete=explanation)


def add_badcase(wf, query):
    title = '有道也翻译不出来了'
    subtitle = '尝试一下去网站搜索'
    quicklookurl = get_quicklook_url(query)
    wf.add_item(title=title, subtitle=subtitle, arg=make_arg(query, query), quicklookurl=quicklookurl, valid=False)

def main():
    query = sys.argv[1].strip().lower() if len(sys.argv) > 1 else None
    wf = Workflow()

    if query:
        response = get_youdao_response(query)
        soup = get_youdao_soup(response)
        if not soup:
            add_badcase(wf, query)
        else:
            add_translation(wf, query, soup)
            add_phonetic(wf, query, soup)
            add_explains(wf, query, soup)
        if not wf.items:
            add_badcase(wf, query)
    print(json.dumps(wf.to_dict(), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
