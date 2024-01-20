import shutil

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from customtkinter import filedialog
from pathlib import Path
import csv
import concurrent.futures
from threading import Event,Lock
import requests
import crawler
import utils
import time
import random
import threading
import os
import re
from selenium.webdriver.common.keys import Keys


WAIT_TIME = 4 * 60
INSTANCE_COUNT = 4
HEADLESS = True
API_LINK = "https://proxy.webshare.io/api/v2/proxy/list/download/bathcjvcmhettprrcsvvnwzzqvhbymownjvbkpge/-/any/username/direct/-/"
EMAIL_REGEX = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'
dangerous_users = r'^hr$|about|abuse|admin|apps|calendar|catch|community|confirm|contracts|customer|daemon|director|excel|fax|feedback|found|hello|help|home|invite|job|mail|manager|marketing|newsletter|office|orders|postmaster|regist|reply|report|sales|scanner|security|service|staff|submission|survey|tech|test|twitter|verification|webmaster'
dangerous_zones = r'\.(gov|mil|edu)(\.[a-z.]+|$)'
dangerous_isps = r'acronis|acros|adlice|alinto|appriver|aspav|atomdata|avanan|avast|barracuda|baseq|bitdefender|broadcom|btitalia|censornet|checkpoint|cisco|cistymail|clean-mailbox|clearswift|closedport|cloudflare|comforte|corvid|crsp|cyren|darktrace|data-mail-group|dmarcly|drweb|duocircle|e-purifier|earthlink-vadesecure|ecsc|eicar|elivescanned|emailsorting|eset|essentials|exchangedefender|fireeye|forcepoint|fortinet|gartner|gatefy|gonkar|group-ib|guard|helpsystems|heluna|hosted-247|iberlayer|indevis|infowatch|intermedia|intra2net|invalid|ioactive|ironscales|isync|itserver|jellyfish|kcsfa.co|keycaptcha|krvtz|libraesva|link11|localhost|logix|mailborder.co|mailchannels|mailcleaner|mailcontrol|mailinator|mailroute|mailsift|mailstrainer|mcafee|mdaemon|mimecast|mx-relay|mx1.ik2|mx37\.m..p\.com|mxcomet|mxgate|mxstorm|n-able|n2net|nano-av|netintelligence|network-box|networkboxusa|newnettechnologies|newtonit.co|odysseycs|openwall|opswat|perfectmail|perimeterwatch|plesk|prodaft|proofpoint|proxmox|redcondor|reflexion|retarus|safedns|safeweb|sec-provider|secureage|securence|security|sendio|shield|sicontact|smxemail|sonicwall|sophos|spamtitan|spfbl|spiceworks|stopsign|supercleanmail|techtarget|titanhq|trellix|trendmicro|trustifi|trustwave|tryton|uni-muenster|usergate|vadesecure|wessexnetworks|zillya|zyxel'
dangerous_isps2 = r'abus|bad|black|bot|brukalai|excello|filter|honey|junk|lab|list|metunet|rbl|research|security|spam|trap|ubl|virtual|virus|vm\d'


class MyGui:
    def __init__(self) -> None:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self.root = ctk.CTk()
        self.root.title("Linkedin Crawler-collect emails")
        self.root.geometry("600x600")
        self.root.maxsize(width=600, height=600)
        self.root.minsize(width=600, height=600)
        self.event = Event()

        self.isRefreshing = Event()
        self.isRefreshing.set()
        self.spiders: list[crawler.Crawler] = []
        self.proxies = []
        self.qgen = utils.QueryGenerator()

        ###### checkboxes
        self.checkboxframe = ctk.CTkFrame(master=self.root, width=550, height=200)
        self.checkboxframe.pack(padx=10, pady=10)

        self.checkboxframetitle = ctk.CTkLabel(master=self.checkboxframe, text="Please Select mails to scrape")
        self.checkboxframetitle.grid(row=0, column=1, columnspan=2)

        self.collect_gmail = tk.BooleanVar(value=False)
        self.checkgmail = ctk.CTkCheckBox(master=self.checkboxframe,
                                          variable=self.collect_gmail,
                                          width=130,
                                          text="Gmail",
                                          )
        self.checkgmail.grid(row=1, column=0, padx=10, pady=10)

        self.collect_yahoo = tk.BooleanVar(value=False)
        self.checkyahoo = ctk.CTkCheckBox(master=self.checkboxframe, width=130, variable=self.collect_yahoo,
                                          text="Yahoo")
        self.checkyahoo.grid(row=1, column=1, padx=5, pady=5)

        self.collect_hotmail = tk.BooleanVar(value=False)
        self.checkhotmail = ctk.CTkCheckBox(master=self.checkboxframe, width=130, variable=self.collect_hotmail,
                                            text="Hotmail")
        self.checkhotmail.grid(row=1, column=2, padx=5, pady=5)

        self.collect_outlook = tk.BooleanVar(value=False)
        self.checkoutlook = ctk.CTkCheckBox(master=self.checkboxframe, width=130, variable=self.collect_outlook,
                                            text="Outlook")
        self.checkoutlook.grid(row=1, column=3, padx=5, pady=5)

        #### start button
        self.btntext = tk.StringVar(value="Start")
        self.btn_start = ctk.CTkButton(master=self.checkboxframe, textvariable=self.btntext, command=self.start)
        self.btn_start.grid(row=2, column=1, columnspan=2, pady=10)

        ### summary
        self.summaryframe = ctk.CTkFrame(master=self.root, width=580, height=200)
        self.summaryframe.pack(padx=10, pady=10)

        self.summarytitle = ctk.CTkLabel(master=self.summaryframe, width=560, height=20,
                                         text="<<<<<<<<<<SUMMARY>>>>>>>>>>")
        self.summarytitle.pack(padx=10, pady=10)

        self.total = tk.StringVar(value="Total Email Count is : 0")
        self.summarytotal = ctk.CTkLabel(master=self.summaryframe, width=560, height=20, textvariable=self.total)
        self.summarytotal.pack(padx=10, pady=5)

        self.totalgmail = tk.StringVar(value="Total Gmail Count is : 0")
        self.summarygmail = ctk.CTkLabel(master=self.summaryframe, width=560, height=20, textvariable=self.totalgmail)
        self.summarygmail.pack(padx=10, pady=5)

        self.totalyahoo = tk.StringVar(value="Total Yahoo Count is : 0")
        self.summaryyahoo = ctk.CTkLabel(master=self.summaryframe, width=560, height=20, textvariable=self.totalyahoo)
        self.summaryyahoo.pack(padx=10, pady=5)

        self.totaloutlook = tk.StringVar(value="Total Outlook Count is : 0")
        self.summaryoutlook = ctk.CTkLabel(master=self.summaryframe, width=560, height=20,
                                           textvariable=self.totaloutlook)
        self.summaryoutlook.pack(padx=10, pady=5)

        self.totalhotmail = tk.StringVar(value="Total hotmail Count is : 0")
        self.summaryhotmail = ctk.CTkLabel(master=self.summaryframe, width=560, height=20,
                                           textvariable=self.totalhotmail)
        self.summaryhotmail.pack(padx=20, pady=5)

        self.btnrefresh = ctk.CTkButton(master=self.summaryframe, text="Refresh", )
        self.btnrefresh.pack(padx=10, pady=20)

        ### save logics
        self.checkboxsaveframe = ctk.CTkFrame(master=self.root, width=550, height=100)
        self.checkboxsaveframe.pack(padx=20, pady=10)

        self.checkboxsaveframetitle = ctk.CTkLabel(master=self.checkboxsaveframe, text="Please Select mails to Save")
        self.checkboxsaveframetitle.grid(row=0, column=1, columnspan=2)

        self.save_gmail = tk.BooleanVar(value=False)
        self.savegmail = ctk.CTkCheckBox(master=self.checkboxsaveframe, width=130, variable=self.save_gmail,
                                         text="Gmail")
        self.savegmail.grid(row=1, column=0, padx=10, pady=10)

        self.save_yahoo = tk.BooleanVar(value=False)
        self.saveyahoo = ctk.CTkCheckBox(master=self.checkboxsaveframe, width=130, variable=self.save_yahoo,
                                         text="Yahoo")
        self.saveyahoo.grid(row=1, column=1, padx=5, pady=5)

        self.save_hotmail = tk.BooleanVar(value=False)
        self.savehotmail = ctk.CTkCheckBox(master=self.checkboxsaveframe, width=130, variable=self.save_hotmail,
                                           text="Hotmail")
        self.savehotmail.grid(row=1, column=2, padx=5, pady=5)

        self.save_outlook = tk.BooleanVar(value=False)
        self.saveoutlook = ctk.CTkCheckBox(master=self.checkboxsaveframe, width=130, variable=self.save_outlook,
                                           text="Outlook")
        self.saveoutlook.grid(row=1, column=3, padx=5, pady=5)

        #### save button
        self.btn_save = ctk.CTkButton(master=self.checkboxsaveframe, width=120, text="Save selected", command=self.save)
        self.btn_save.grid(row=2, column=0, pady=10, padx=10, columnspan=2, )

        ### save all
        self.btn_save_all = ctk.CTkButton(master=self.checkboxsaveframe, width=120, text="Save all",
                                          command=self.save_all)
        self.btn_save_all.grid(row=2, column=1, pady=10, padx=5, columnspan=2)

        ## verify logics
        self.btn_verify_save = ctk.CTkButton(master=self.checkboxsaveframe, width=120, text="Filter",
                                             command=self.verify_save)
        self.btn_verify_save.grid(row=2, column=2, pady=10, padx=5, columnspan=2)

        self.verf_text = tk.StringVar(value="Click filter to start filtering...")
        self.currently_verf = ctk.CTkLabel(master=self.checkboxsaveframe, textvariable=self.verf_text)
        self.currently_verf.grid(row=3, column=1, columnspan=2, pady=10)

        self.refresh()

        # show app
        self.root.mainloop()

    def verify_save(self):
        self.verf_text.set(f"Verifying... Please wait")
        domains: list[str] = []
        if (self.save_gmail.get() == True): domains.append("@gmail.com")
        if (self.save_hotmail.get() == True): domains.append("@hotmail.com")
        if (self.save_yahoo.get() == True): domains.append("@yahoo.com")
        if (self.save_outlook.get() == True): domains.append("@outlook.com")

        if len(domains) == 0:
            messagebox.showwarning(title="Error!", message="Please select at least one domain")
            return

        save_filtered_dir = os.path.join(os.getcwd(), "filtered")
        if os.path.exists(save_filtered_dir) == False:
            os.mkdir(save_filtered_dir)

        safe_emails = os.path.join(save_filtered_dir, "safe_email.csv")
        unsafe_emails = os.path.join(save_filtered_dir, "unsafe_email.csv")
        invalid_emails = os.path.join(save_filtered_dir, "invalid_email.csv")
        no_emails = os.path.join(save_filtered_dir, "no_email.csv")
        print(save_filtered_dir)

        files = Path(os.path.join(os.getcwd(), "data")).glob("*.csv")

        safe = open(safe_emails, 'a', newline='')
        unsafe = open(unsafe_emails, 'a', newline='')
        invalid = open(invalid_emails, 'a', newline='')
        nom = open(no_emails, 'a', newline='')
        count = 0

        for file in files:
            r = open(file,errors='ignore')

            csvr = csv.reader(r)
            csv_safe = csv.writer(safe)
            csv_unsafe = csv.writer(unsafe)
            csv_invalid = csv.writer(invalid)
            csv_none = csv.writer(nom)

            for row in csvr:
                count += 1
                if (row[2] == ""):
                    csv_none.writerow(row)
                    continue
                if (re.match(EMAIL_REGEX, row[2]) == None):
                    csv_invalid.writerow(row)
                    continue
                if (
                        re.match(dangerous_zones, row[2]) or
                        re.match(dangerous_isps, row[2]) or
                        re.match(dangerous_isps2, row[2]) or
                        re.match(dangerous_users, row[2])
                ):
                    csv_unsafe.writerow(row)
                    continue
                csv_safe.writerow(row)

        print(count)
        messagebox.showinfo(title="Verify Done",message="Filtered all the emails. Check 'filtered' folder")
        self.verf_text.set(f"Verifying... Done!!!!!!!")

    def refresh(self):
        print(f"Refreshing {random.randint(1, 100)}")
        files = Path("data").glob("*.csv")
        counts = {
            "gmail": 0,
            "yahoo": 0,
            "hotmail": 0,
            "outlook": 0,
        }

        total = 0
        for file in files:
            try:
                r = open(file, errors='ignore')
                csvr = csv.reader(r)
                for row in csvr:
                    total += 1
                    if "@gmail.com" in row[2]:
                        counts["gmail"] += 1
                    if "@yahoo.com" in row[2]:
                        counts["yahoo"] += 1
                    if "@hotmail.com" in row[2]:
                        counts["hotmail"] += 1
                    if "@outlook.com" in row[2]:
                        counts["outlook"] += 1
                r.close()
            except Exception as e:
                print(f"Found error in {file}")
                print(e)

        self.total.set(f'Total Entry: {total}')
        self.totalgmail.set(f'Total gmail: {counts["gmail"]}')
        self.totalhotmail.set(f'Total hotmail: {counts["hotmail"]}')
        self.totaloutlook.set(f'Total outlook: {counts["outlook"]}')
        self.totalyahoo.set(f'Total yahoo: {counts["yahoo"]}')

        self.root.after(5000, self.refresh)

    def start(self):
        domains = []
        if (self.collect_gmail.get() == True): domains.append("@gmail.com")
        if (self.collect_hotmail.get() == True): domains.append("@hotmail.com")
        if (self.collect_yahoo.get() == True): domains.append("@yahoo.com")
        if (self.collect_outlook.get() == True): domains.append("@outlook.com")

        if (len(domains) == 0):
            messagebox.showwarning(title="Error", message="Please select one of the domains")
            print("select at least one")
            return

        if (self.btntext.get() == "Stop"):  # clicked stop
            self.btntext.set("Start")
            self.event.clear()


        elif (self.btntext.get() == "Start"):  # clicked start
            self.btntext.set("Stop")
            self.event.set()
            threading.Thread(target=self.control_body, args=[domains], daemon=True).start()

    def control_body(self, domains):
        try:
            cycle_count = 1
            while True:
                print(f"Starting cycle {cycle_count}")
                self.del_extensions()
                self.preparations()

                futures = []
                total_coll: list[list[str]] = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=INSTANCE_COUNT) as executor:
                    for proxy in self.proxies:
                        futures.append(executor.submit(self.mainframe, proxy, domains))

                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        print(f"Completed with proxy: {len(result)}")

                        for item in result:
                            total_coll.append(item)

                    except Exception as e:
                        print("Found Error!!!")
                        print(e)

                print(f"Ending cycle {cycle_count}")
                print(f"Cycle summary: found total entry in this cycle: {len(total_coll)}")
                save_file_path = os.path.join(os.getcwd(),"data","output.csv")

                with open(save_file_path,"a",encoding="utf-8",errors='ignore',newline="") as fo:
                    csv_writer = csv.writer(fo)
                    for line in total_coll:
                        csv_writer.writerow(line)


                cycle_count += 1
                tm = WAIT_TIME

                while tm != 0:
                    time.sleep(1)
                    if self.event.is_set() == False:
                        return
                    tm -= 1
        except Exception as e:
            messagebox.showwarning(title="error", message=f"{e}")
            raise e




    def createSpider(self, proxy) -> crawler.Crawler:
        print(f"using proxy :{proxy}")
        spider = crawler.Crawler(
            options=utils.create_options_proxy(proxy),
            name=f'output_{utils.randomword()}',
            headless=HEADLESS,
            browser_path=os.path.join(os.getcwd(),
                                      "GoogleChromePortableBeta",
                                      "App",
                                      "Chrome-bin",
                                      "chrome.exe", ),
            driver_path=os.path.join(os.getcwd(), "chromedriver.exe"),

        )
        self.spiders.append(spider)
        return spider

    def preparations(self):
        # res = requests.get(API_LINK)
        proxy_text = '''154.12.77.107:6482:dmucqoej:pboe4k5t25ei
64.137.43.228:5565:dmucqoej:pboe4k5t25ei
107.181.149.96:5392:dmucqoej:pboe4k5t25ei
104.238.48.61:5451:dmucqoej:pboe4k5t25ei
81.21.235.211:5566:dmucqoej:pboe4k5t25ei
154.17.250.222:5908:dmucqoej:pboe4k5t25ei
154.17.250.253:5939:dmucqoej:pboe4k5t25ei
154.38.35.83:5351:dmucqoej:pboe4k5t25ei
185.201.140.227:6741:dmucqoej:pboe4k5t25ei
154.9.23.25:5936:dmucqoej:pboe4k5t25ei
154.21.155.65:6508:dmucqoej:pboe4k5t25ei
154.30.58.148:5743:dmucqoej:pboe4k5t25ei
207.60.117.186:6469:dmucqoej:pboe4k5t25ei
154.9.23.235:6146:dmucqoej:pboe4k5t25ei
45.250.65.145:5496:dmucqoej:pboe4k5t25ei
154.12.97.218:6571:dmucqoej:pboe4k5t25ei
185.199.228.56:7136:dmucqoej:pboe4k5t25ei
154.21.39.163:6001:dmucqoej:pboe4k5t25ei
185.48.54.100:5420:dmucqoej:pboe4k5t25ei
23.129.255.96:5504:dmucqoej:pboe4k5t25ei
154.12.140.63:5710:dmucqoej:pboe4k5t25ei
154.21.111.154:6539:dmucqoej:pboe4k5t25ei
134.73.174.129:5565:dmucqoej:pboe4k5t25ei
154.9.176.24:5048:dmucqoej:pboe4k5t25ei
104.148.28.225:6502:dmucqoej:pboe4k5t25ei
'''
        # proxy_list = res.text.splitlines()
        proxy_list = proxy_text.splitlines()
        self.proxies = []
        print("done")
        for s in proxy_list:
            s = s.split(':')
            self.proxies.append({
                'host': s[0],
                'port': s[1],
                'user': s[2],
                'pass': s[3],
            })
        print(self.proxies)
        random.shuffle(self.proxies)



    def mainframe(self, proxy: dict, domains: list[str]):
        domain = random.choice(domains)
        collection: list[list[str]] = []

        if (self.event.is_set() == False):
            return collection
        try:
            spider = self.createSpider(proxy)
            search_box = spider.driver.find_element("xpath", "//textarea[@name='q']")
            search_box.click()
            search_box.clear()
            time.sleep(random.randint(1,3))

            search_str = f'''site:linkedin.com/in "{domain}" {self.qgen.genWord()} before:2022-01-01'''
            search_box.send_keys(search_str)
            time.sleep(random.randint(1,3))
            search_box.send_keys(Keys.ENTER)
            time.sleep(random.randint(1,3))
            spider.driver.get(spider.driver.current_url + "&num=100")
            time.sleep(random.randint(5, 10))
            collection = spider.retrieve_data()

            spider.driver.close()
            spider.driver.quit()
        except Exception as e:
            print("A spider just failed!")
            print(e)
        finally:
            return collection






    def save_all(self):
        savefilename = filedialog.asksaveasfilename(filetypes=[("csv", "*.csv")])
        print(savefilename)
        if ".csv" not in savefilename:
            savefilename += ".csv"

        files = Path("data").glob("*.csv")

        for file in files:
            r = open(file,errors='ignore')
            w = open(savefilename, 'a', newline='')

            csvr = csv.reader(r)
            csvw = csv.writer(w)

            for row in csvr:
                csvw.writerow(row)
            r.close()
            w.close()

    def save(self):
        domains = []
        if (self.save_gmail.get() == True): domains.append("@gmail.com")
        if (self.save_hotmail.get() == True): domains.append("@hotmail.com")
        if (self.save_yahoo.get() == True): domains.append("@yahoo.com")
        if (self.save_outlook.get() == True): domains.append("@outlook.com")

        if (len(domains) == 0): return

        savefilename = filedialog.asksaveasfilename(filetypes=[("csv", "*.csv")])

        if ".csv" not in savefilename:
            savefilename += ".csv"
        print(savefilename)

        files = Path("data").glob("*.csv")

        for file in files:
            r = open(file,errors='ignore')
            w = open(savefilename, 'a', newline='')

            csvr = csv.reader(r)
            csvw = csv.writer(w)

            for row in csvr:
                for domain in domains:
                    if domain in row[2]:
                        csvw.writerow(row)
                        break
            r.close()
            w.close()

    def del_extensions(self):
        try:
            shutil.rmtree(os.path.join(os.getcwd(), "extension"))
        except FileNotFoundError:
            print("extension folder not found")


if __name__ == "__main__":
    m = MyGui()

