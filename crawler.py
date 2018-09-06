import os
import time
import json
import requests
import numpy as np
from bs4 import BeautifulSoup
from collections import defaultdict
from selenium import webdriver
import argparse
from datetime import datetime as dt

"""Set Script Options"""
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--headless")  
driver = webdriver.Chrome(chrome_options=chrome_options)
driver.get('https://google.com')

def get_sa_urls(n):
	"""
	Return list of transcript urls.

	Parameters:
	-----------
	n (int) = number of pages to scrape
	"""

	base_url = 'https://seekingalpha.com/earnings/earnings-call-transcripts/'
	sector = 'financial'
	pre = 'https://seekingalpha.com'
	post = '?part=single'

	temp_url_list = list()
	for i in range(1, n + 1):
		n_url = base_url + '/{}?sector={}'.format(i, sector)
		soup = BeautifulSoup(requests.get(n_url).content, 'html.parser')
		for a in soup.find_all('a', href=True):
			temp = a['href']
			if 'article' in temp.split('/'):
				temp_url_list.append(pre + temp + post)
		time.sleep(3)
	return temp_url_list

def get_content(url):
	"""
	Return dictionary of transcripts call.

	Parameters:
	-----------
	url (str): url of website to be scraped.
	"""

	company_id = "_".join(url.split('-')[1:-1])
	print('************')
	print(company_id)
	print(url)
	soup = BeautifulSoup(requests.get(url).content, 'html.parser')
	p_list = list()
	for p in soup.find_all('p'):
		p_list.append(p.text.lower())
	print(p_list[:5])
	print('------------')
	i_analysts = p_list.index('analysts')
	i_executives = p_list.index('executives')
	i_opp = p_list.index('operator')
	temp_dict = defaultdict(dict)
	filtr = lambda x: x.split(' - ')
	for i_text in p_list[i_executives + 1: i_analysts]:
		i_exec = filtr(i_text)
		temp_dict['executives'][i_exec[0]] = i_exec[1:]
	for i_text in p_list[i_analysts + 1: i_opp]:
		i_anlst = filtr(i_text)
		temp_dict['analysts'][i_anlst[0]] = i_anlst[1:]
	temp_dict['call_body'] = p_list[i_opp:]
	return {company_id: temp_dict}


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Seeking Alpha Web Crawler.',
									 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--directory',
						type=str,
						action='store',
						default=None,
						help='Directory to store txt files ')
	parser.add_argument('--n_pages',
						type=int,
						action='store',
						default=1,
						help='Number of pages to scrape.')
	args = parser.parse_args()

	if args.directory is None:
		directory = os.getcwd()
	else:
		directory = args.directory
	content_dict = dict()
	url_list = get_sa_urls(args.n_pages)
	for i, url in enumerate(url_list):
		content_dict.update(get_content(url))
		time.sleep(np.random.randint(1,10))
		if i % 1 == 0:
			path_time = str(dt.today()).split('.')[0]
			with open(os.path.join(directory, path_time, 'transcripts.txt'), 'w') as file:
				file.write(json.dumps(content_dict))
			content_dict = dict()
