import os
import csv
import json
import random
import string

import undetected_chromedriver as uc
import re
from sys import platform
import json
from pathlib import Path
from threading import Lock

class QueryGenerator:
    def __init__(self):
        self.countries = []
        self.words = []
        self.jobs = []
        self.email_domains = []
        self.companies = []
        self.all_together = []



        file_names = Path(os.path.join(os.getcwd(),"words")).glob("*.json")

        # for file in file_names:
        #     with open(file,encoding='utf-8') as fo:
        #         cjson = json.loads(fo.read())
        #         for word in cjson["words"]:
        #             self.all_together.append(word["targetWord"])
        
        # print(f"found words: {len(self.all_together)}")

        with open("country.txt") as co:
            for country in co:
                self.countries.append(country.strip())
                self.all_together.append(country.strip())
            
        with open("company_names.txt") as co:
            for company in co:
                self.companies.append(company.strip())
                self.all_together.append(company.strip())
        
        with open("words.txt") as wo:
            for word in wo:
                self.words.append(word.strip())
                self.all_together.append(word.strip())


    def genWord(self):
        return random.choice(self.all_together)

    def generate(self, base:str,custom_email="") -> str:
        word = random.choice(self.words)
        country = random.choice(self.countries)
        bn = random.choice(self.companies)
        mail = random.choice([
            "@gmail.com",
            "@yahoo.com",
            "@hotmail.com",
            "@icloud.com",
            "@outlook.com",
            ])
        
        if(custom_email != ""):
            mail = custom_email
        # job = random.choice(self.jobs)
        #email_dom = random.choice(self.email_domains)
        result = base +' "'+ mail +'" '
        result += random.choice([country, bn, word])
        return result



def save_data(filename:str, row:list[str]) -> bool:
    try:
        with open(filename,"a",newline='', encoding="utf-8") as fa:
            csv.writer(fa).writerow(row)
        return True

    except Exception as e:
        print(e)
        return False


def create_options_proxy(proxy_obj):
    PROXY_HOST = proxy_obj['host'] 
    PROXY_PORT = proxy_obj['port']
    PROXY_USER = proxy_obj['user']
    PROXY_PASS = proxy_obj['pass']

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
            },
            bypassList: ["localhost"]
            }
        };
    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }
    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)



    PROXY_FOLDER = os.path.join(os.getcwd(),'extension', f"{randomword()}")
    os.makedirs(PROXY_FOLDER, exist_ok=True)
    PROXY_FOLDER = os.path.join(os.getcwd(), PROXY_FOLDER)

    with open(os.path.join(PROXY_FOLDER,"manifest.json"),"w") as f:
        f.write(manifest_json)
    with open(os.path.join(PROXY_FOLDER,"background.js"),"w") as f:
        f.write(background_js)   
    
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument(f"--load-extension={PROXY_FOLDER}")

    return chrome_options




def extract_version_registry(output):
    try:
        google_version = ''
        for letter in output[output.rindex('DisplayVersion    REG_SZ') + 24:]:
            if letter != '\n':
                google_version += letter
            else:
                break
        return(google_version.strip())
    except TypeError:
        return

def extract_version_folder():
    # Check if the Chrome folder exists in the x32 or x64 Program Files folders.
    for i in range(2):
        path = 'C:\\Program Files' + (' (x86)' if i else '') +'\\Google\\Chrome\\Application'
        if os.path.isdir(path):
            paths = [f.path for f in os.scandir(path) if f.is_dir()]
            for path in paths:
                filename = os.path.basename(path)
                pattern = r'\d+\.\d+\.\d+\.\d+'
                match = re.search(pattern, filename)
                if match and match.group():
                    # Found a Chrome version.
                    return match.group(0)

    return None

def get_chrome_version():
    version = None
    install_path = None

    try:
        if platform == "linux" or platform == "linux2":
            # linux
            install_path = "/usr/bin/google-chrome"
        elif platform == "darwin":
            # OS X
            install_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"
        elif platform == "win32":
            # Windows...
            try:
                # Try registry key.
                stream = os.popen('reg query "HKLM\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome"')
                output = stream.read()
                version = extract_version_registry(output)
            except Exception as ex:
                # Try folder path.
                version = extract_version_folder()
    except Exception as ex:
        print(ex)

    version = os.popen(f"{install_path} --version").read().strip('Google Chrome ').strip() if install_path else version

    return version

def randomword(length=12):
    letters = string.ascii_lowercase
    letters = letters + string.digits
    letters = letters + string.ascii_uppercase

    return ''.join([random.choice(letters) for i in range(length)])

if __name__ == '__main__':

    qgen = QueryGenerator()

    print(qgen.genWord())
    print(qgen.genWord())
    print(qgen.genWord())
    print(qgen.genWord())


