from requests import ReadTimeout
import pywikibot
import requests
import re
import time
from pywikibot import pagegenerators

site = pywikibot.Site()

matchBuilder = pywikibot.textlib.MultiTemplateMatchBuilder(site)
REPLACED_TEMPLATE = "IOC profile"
IOC_PROFILE = matchBuilder.pattern(REPLACED_TEMPLATE)
OLYMPICS_COM_PROFILE = [matchBuilder.pattern("Olympics.com profile"), matchBuilder.pattern("Olympic Channel"), matchBuilder.pattern("Olympics.com")]
SPORTS_LINKS = [matchBuilder.pattern("Sports links"), matchBuilder.pattern("Sport links"), matchBuilder.pattern("Sport link")]
EDIT_SUMMARY = "{{[[Template:IOC profile|IOC profile]]}} is being merged into {{[[Template:Olympics.com profile|Olympics.com profile]]}} "
EDIT_SUMMARY += "([[Wikipedia:Templates for discussion/Log/2021 May 6#Template:Olympic Channel|TfD]]) "
EDIT_SUMMARY += "([[Wikipedia:Bots/Requests for approval/Yet another TfD implementor bot|BRfA]])"
HEADERS = headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"}

factory = pagegenerators.GeneratorFactory()
factory.handle_arg("-transcludes:" + REPLACED_TEMPLATE)
pageset = factory.getCombinedGenerator()
for page in pageset:
    if pywikibot.Page(site, "User:Yet another TfD implementor bot/Switch").text != "OK":
        print("Bot disabled by switch")
        exit()

    for regex in OLYMPICS_COM_PROFILE:
        if (re.search(regex, page.text) != None): # This template has the same merge target and would be a duplicate
            page.text = re.sub("\n.*\{\{" + REPLACED_TEMPLATE + ".*?\}\}", "", page.text)
            try:
                page.save(EDIT_SUMMARY, minor=False, botflag=True)
                time.sleep(30)
            except pywikibot.exceptions.LockedPageError:
                print(page.title() + " is protected")
            finally:
                continue

    for regex in SPORTS_LINKS:
        if (re.search(regex, page.text) != None):
            wikidataItem = pywikibot.ItemPage.fromPage(page)
            wikidataItem.get()
            if wikidataItem.claims:
                if "P3171" in wikidataItem.claims:
                    page.text = re.sub("\n.*\{\{" + REPLACED_TEMPLATE + ".*?\}\}", "", page.text)
                    try:
                        page.save(EDIT_SUMMARY, minor=False, botflag=True)
                        time.sleep(30)
                    except pywikibot.exceptions.LockedPageError:
                        print(page.title() + " is protected")
                    finally:
                        continue
        
    match = re.search(IOC_PROFILE, page.text)
    if match is None:
        continue # This script only processes redirects one at a time because it's easier
    
    # Search the page text for {{IOC profile}}, use extract_templates_and_params() to parse the params, 
    # grab the index 0 template from the list as it is going to be the only one, and then the first
    # index because we only need the OrderedDict
    params = pywikibot.textlib.extract_templates_and_params(match.group(0), strip=True, remove_disabled_parts=True)[0][1]
    id = None
    name = None
    if "id" in params:
        id = params["id"]
    if "1" in params:
        id = params["1"]
    if id == None:
        wikidataItem = pywikibot.ItemPage.fromPage(page)
        wikidataItem.get()
        if not wikidataItem.claims:
            continue # All possible locations of the ID have been exhausted
        if not "P3171" in wikidataItem.claims:
            continue
        id = wikidataItem.claims["P3171"][0].getTarget()
    if "name" in params:
        name = params["name"]
    if "2" in params:
        name = params["2"]
    
    # olympics.com seems to block automated traffic, so we get the target from the headers instead without connecting to them.
    try:
        newid = requests.head("http://www.olympic.org/" + id, timeout=5, headers=HEADERS).headers['Location'][24:]
        print(newid[24:])
    except ReadTimeout:
        print("Editing " + page.title() + " failed because of timeout. " + id)
        continue
    if name == None:
        page.text = re.sub(IOC_PROFILE, "{{Olympics.com profile|" + newid + "}}", page.text)
    else:
        page.text = re.sub(IOC_PROFILE, "{{Olympics.com profile|" + newid + "|" + name + "}}", page.text)
    
    try:
        page.save(EDIT_SUMMARY, minor=False, botflag=True)
        time.sleep(30)
    except pywikibot.exceptions.LockedPageError:
        print(page.title + " is protected")
    finally:
        continue
