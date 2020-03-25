import sys, os
import re
from argparse import ArgumentParser
import datetime
import scrapy
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from time import sleep
import logging
import pickle
from tqdm import tqdm
import numpy as np

def scraping_sumo(start: int, end: int=2019):
    date = datetime.datetime.today().strftime('%Y_%m%d_%H%M')
    log_name = 'log/oosumo-{}.log'.format(date)
    if os.path.exists(log_name):
        os.remove(log_name)
    logging.basicConfig(filename=log_name, level=logging.INFO)
    ##### setup loging #####
    logging.info('Createing browser...')
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--blink-settings=imageEnabled=false')
    ########################
    
    # generate a Chrome's WebDriver object
    browser = webdriver.Chrome(options=options)
    browser.set_page_load_timeout(10*60)
    logging.info('browser is ready: timeout = 10*60 [sec/pageload]')

    # YYYY: year, MM: month, DAY: day
    root_url = 'http://sumodb.sumogames.de/Results.aspx?b=YYYYMM&d=DAY&l=j'
    years = np.arange(start, end+1)
    month = np.array(['01', '03', '05', '07', '09', '11'])
    basyo_list = []
    
    # Make save directories
    for y in years:
        if y == 2020:
            basyo_list.append((y, '01'))
            break
        for m in month:
            basyo_list.append((y, m))
    
    N = len(basyo_list)
    basyos = []
    logging.info('Scrape {} items'.format(N))
    logging.info('Start scraping!')
    
    for i, (y, m) in enumerate(basyo_list):
        sys.stdout.write('\rScraping the list of category: {} / {}'.format(i, N))
        basyo_url = root_url.replace('YYYY', str(y)).replace('MM', str(m))
        
        # Make directories and save files as pickle
        save_dir = 'data/{}/{}'.format(y, m)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        for day in np.arange(1, 16):
            sleep(0.1) # Sleep time
            sys.stdout.write('\rScraping the list of category: {} / {} \n day:{}\n'.format(i, N, day))
            url = basyo_url.replace('DAY', str(day))
            try:
                browser.get(url)
                # obtain list of category
                category_contents = browser.find_element_by_class_name('tk_table')
                images = category_contents.find_elements_by_tag_name('img')
                images = [img.get_attribute('src') for img in images]
                # If True, east rikishi wins tha game.
                which_shiro = np.array([os.path.basename(image_path) == 'hoshi_kuro.gif' for image_path in images])
                which_shiro = which_shiro[::2]
                east = category_contents.find_elements_by_class_name('tk_east')
                east_rikishi = [re.split('\n', cont.text)[1] for cont in east]
                
                west = category_contents.find_elements_by_class_name('tk_west')
                west_rikishi = [re.split('\n', cont.text)[1] for cont in west]
                
                kim  = category_contents.find_elements_by_class_name('tk_kim')
                kimarites = [re.split('\n', cont.text)[0] for cont in kim]
                results = list(zip(east_rikishi, west_rikishi, which_shiro, kimarites))
                logging.info('Success!')
                
            except Exception as err:
                logging.exception('[TimeoutException]: {}'.format(err))
            # Save file as pickle
            save_file = '{}/sumo_{}{}_day{}.pickle'.format(save_dir, y, m, day)
            logging.info('Trying to save {} with pickle...'.format(save_file))
            with open(save_file, mode='wb') as f:
                pickle.dump(results, f)
            logging.info('Succeded to save {}'.format(save_file))
            
    browser.close()
    logging.info('Close browser')
    
if __name__ == '__main__':
    # Setting Parser
    parser = ArgumentParser(description='Scrape Oo-Sumo　data.')
    parser.add_argument('--start', type=int, help='Do scraping starts from this year')
    parser.add_argument('--end',   type=int, help='Do scraping ends to this year')
    args = parser.parse_args()
    
    scraping_sumo(args.start, args.end)
