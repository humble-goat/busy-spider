from bs4 import BeautifulSoup
import requests
import requests.exceptions
from urllib.parse import urlsplit
from collections import deque
import re
import pandas as pd

trusted_ = ['gr, com, gov, net, org, info, nfo, be']
linker = '' # google search url
new_urls = deque([linker])
mail_db = pd.DataFrame(columns=['emails', 'from'])
counter = 0
# a set of urls that we have already crawled
processed_urls = set()

# a set of crawled emails
emails = set()

# process urls one by one until we exhaust the queue
while len(new_urls):

    # move next url from the queue to the set of processed urls
    url = new_urls.popleft()
    processed_urls.add(url)

    # extract base url to resolve relative links
    parts = urlsplit(url)
    base_url = "{0.scheme}://{0.netloc}".format(parts)
    path = url[:url.rfind('/') + 1] if '/' in parts.path else url

    # get url's content
    # print("Processing %s" % url)
    print(counter)
    try:
        response = requests.get(url)
    except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
        # ignore pages with errors
        continue

    # extract all email addresses and add them into the resulting set
    new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", response.text, re.I))
    if new_emails.split('.')[-1].lower() in trusted_:       # email proofing
        emails.update(new_emails)
        if new_emails not in mail_db.values:
            try:
                mail_db.loc[counter, 'emails'] = emails.pop()
            except Exception as err:
                pass
            mail_db.loc[counter, 'from'] = str(url).replace('"', '')
            counter += 1
            mail_db.dropna(subset=['emails'], inplace=True)
            mail_db.drop_duplicates(subset=['emails'], inplace=True)
            mail_db.to_csv('test.csv', sep=';', encoding='utf-8', index=False)
        # create a beutiful soup for the html document
        soup = BeautifulSoup(response.text, features="html.parser")

        # find and process all the anchors in the document
        for anchor in soup.find_all("a"):
            # extract link url from the anchor
            link = anchor.attrs["href"] if "href" in anchor.attrs else ''
            # resolve relative links
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith('http'):
                link = path + link
            # add the new url to the queue if it was not enqueued nor processed yet
            if not link in new_urls and not link in processed_urls:
                new_urls.append(link)
