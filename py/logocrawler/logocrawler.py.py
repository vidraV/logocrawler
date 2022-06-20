import aiohttp
from bs4 import BeautifulSoup
import asyncio
import csv
import sys
from datetime import datetime
import json
import random
import os

#async GET method 
async def fetch(session, url):
    try:
        async with session.get(url) as response:
            if response.status < 400:
                response_body = await response.text()
                data = await grab_image_urls(url, response_body)
                return data
    except Exception as e:
        print(str(e))

def images_from_src(response_body):
    soup = BeautifulSoup(response_body, "html.parser")
    img_tags = soup.find_all('img', {"src":True})
    urls = [img['src'] for img in img_tags]
    return urls


def check_if_logo(string_image):
    if "logo" in string_image.lower():
        return True
    else:
        return False

def check_if_favicon(string_image):
    if "favicon" in string_image.lower():
        return True
    else:
        return False

def random_user_agent():
    headers = { '0' : {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'},
            '1' : {'User-Agent': 'WeatherReport/1.2.2 CFNetwork/485.13.9 Darwin/11.0.0'},
            '2' : {'User-Agent': 'Mozilla/5.0 (X11; Datanyze; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'},
            '3' : {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 OPR/78.0.4093.184'},
            '4' : {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.1 Mobile/15E148 Safari/604.1'}}
    random_number = random.randint(0, 4)
    return headers[str(random_number)]

async def grab_image_urls(url, response_body):
    try:
        found_logo = False
        found_favicon = False
        temporary_logo = ""
        temporary_favicon = ""
        data = {}
        data[url] = {}
        soup = BeautifulSoup(response_body, "html.parser")

        #try to find logo or favicon from og:image. If "logo" in image url, save as logo. If "favicon" in url, save as favicon.
        meta_image = soup.find("meta", property="og:image")
        if meta_image:
            try:
                string_meta_image = meta_image["content"]
                if check_if_logo(string_meta_image):
                    found_logo = True
                    temporary_logo = string_meta_image
                elif check_if_favicon(string_meta_image):
                    found_favicon = True
                    temporary_favicon = string_meta_image
                    
                else:
                    temporary_logo = string_meta_image
            except Exception as e:
                print(str(e))

        #try to find logo or favicon from shorcut url
        favicon_url = soup.find("link", rel="shortcut icon")
        if favicon_url:
            try:
                string_favicon_image = favicon_url["href"]
                if not found_logo:
                    if check_if_logo(string_favicon_image):
                        found_logo = True
                        temporary_logo = string_favicon_image
                if not found_favicon:
                    if check_if_favicon(string_favicon_image):
                        found_favicon = True
                        temporary_favicon = string_favicon_image
                        
            except Exception as e:
                print(str(e))

        #Try to find logo or favicon in other images
        if not found_logo:
            string_images = images_from_src(response_body)
            urls_counter = 0      
            if string_images:
                try:
                    while not found_logo and urls_counter != len(string_images):
                        if check_if_logo(string_images[urls_counter]):
                            found_logo = True
                            temporary_logo = string_images[urls_counter]
                        urls_counter += 1               
                except Exception as e:
                    print(e)

        if not found_favicon:
            string_images = images_from_src(response_body)
            urls_counter = 0      
            if string_images:
                try:
                    while not found_favicon and urls_counter != len(string_images):
                        if check_if_favicon(string_images[urls_counter]):
                            found_favicon = True
                            temporary_favicon = string_images[urls_counter]
                        urls_counter += 1
                except Exception as e:
                    print(e)

        data[url]["logo"] = temporary_logo
        data[url]["favicon"] = temporary_favicon

        print(data)

        return data
    except Exception as e:
        print(str(e))

async def main(urls):
    tasks = []
    output_json = {}
    session_timeout = 20
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=session_timeout, sock_read=session_timeout)
  
    async with aiohttp.ClientSession(timeout=timeout, headers=random_user_agent()) as session:
        for url in urls:
            tasks.append(fetch(session, url))

        final_data = await asyncio.gather(*tasks)

        for each_website_result in final_data:
            if each_website_result:
                output_json.update(each_website_result)

        return output_json

if __name__ == '__main__':
    now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    urls_list = []
    current_dir = os.path.dirname(os.path.realpath(__file__))
    target_dir = os.path.sep.join(current_dir.split(os.path.sep)[:-2])
    with open(f'{target_dir}/websites.csv', newline='') as csvfile:
        csv_websites = csv.reader(csvfile, delimiter=' ')
        for row in csv_websites:
            domain_name = ''.join(row)
            website = "https://www." + domain_name
            urls_list.append(website)

    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    final_json_output = asyncio.run(main(urls = urls_list))

    print("**********************************************")


    with open(f"{target_dir}/parsed_json/json_data-{str(now)}.json", "w") as fp:
        json.dump(final_json_output, fp)

