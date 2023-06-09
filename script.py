import pywikibot
import requests
import re
import time
from pywikibot import pagegenerators

site = pywikibot.Site()

matchBuilder = pywikibot.textlib.MultiTemplateMatchBuilder(site)
IOC_PROFILE = matchBuilder.pattern("IOC profile")
OLYMPICS_COM_PROFILE = [matchBuilder.pattern("Olympics.com profile"), matchBuilder.pattern("Olympic Channel"), matchBuilder.pattern("Olympics.com")]
EDIT_SUMMARY = "{{[[Template:IOC profile|IOC profile]]}} is being merged into {{[[Template:Olympics.com profile|Olympics.com profile]]}} "
EDIT_SUMMARY += "([[Wikipedia:Templates for discussion/Log/2021 May 6#Template:Olympic Channel|TfD]]) "
EDIT_SUMMARY += "([[Wikipedia:Bots/Requests for approval/Yet another TfD implementor bot|Bot trial]])"

def processPage(page : pywikibot.Page):
    if pywikibot.Page(site, "User:Yet another TfD implementor bot/Switch").text != "OK":
        return

    for regex in OLYMPICS_COM_PROFILE:
        if (re.search(regex, page.text) != None): # This template has the same merge target and would be a duplicate
            page.text = re.sub("\n.*\{\{IOC profile.*?\}\}", "", page.text)

            try:
                page.save(EDIT_SUMMARY, minor=False)
            except pywikibot.exceptions.LockedPageError:
                print(page.title + " is protected")
            finally:
                return
        
    match = re.search(IOC_PROFILE, page.text)
    if match is None:
        return # This script only processes redirects one at a time because it's easier
    
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
            return # All possible locations of the ID have been exhausted
        if not "P3171" in wikidataItem.claims:
            return
        id = wikidataItem.claims["P3171"][0].getTarget()
    if "name" in params:
        name = params["name"]
    if "2" in params:
        name = params["2"]
    
    # olympics.com seems to block automated traffic, so we get the target from the headers instead without connecting to them.
    newid = requests.head("https://www.olympic.org/" + id, timeout=5).headers['Location'][33:]
    if name == None:
        page.text = re.sub(IOC_PROFILE, "{{Olympics.com profile|" + newid + "}}", page.text)
    else:
        page.text = re.sub(IOC_PROFILE, "{{Olympics.com profile|" + newid + "|" + name + "}}", page.text)
    
    try:
        page.save(EDIT_SUMMARY, minor=False)
    except pywikibot.exceptions.LockedPageError:
        print(page.title + " is protected")
    finally:
        return

factory = pagegenerators.GeneratorFactory()
factory.handle_arg("-transcludes:IOC profile")
pageset = factory.getCombinedGenerator()
for i in pageset:
    processPage(pageset)
    time.sleep(30)
