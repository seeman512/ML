# usage:
#   python3 fetch.py pages|articles

from bs4 import BeautifulSoup
import aiohttp
import sys
import os
import json
import logging
import asyncio


logging.basicConfig(level=logging.DEBUG)

pages_url = 'https://vn.mk.ua/ru/arhiv/page/'
pages_file_path = './pages.json'
articles_dir = './articles'
max_pages = 1528
batch_size = 5


async def parse_page(session, page_url):
    logging.debug('Handling page:' + page_url)
    articles_data = []

    async with session.get(page_url) as page:
        if page.status != 200:
            logging.debug('Could not handle page' +  str(page.status))
            return articles_data
        
        soup = BeautifulSoup(await page.text(), 'html.parser')
        for article in soup.find(id='main-content').findAll('article'):
            header = article.find('h3')
            articles_data.append({'page_url': page_url,
                                  'href': header.find('a')['href'],
                                  'title': header.find('a')['title'],
                                  'date': article.find('span', class_="entry-meta-date").find("a").text.strip(),
                                  'category': article.find('div', class_='mh-image-caption').text.strip()})
    return articles_data

async def fetch_pages():
    pages = []

    i = 0
    async with aiohttp.ClientSession() as session:
        for _ in range(1, max_pages + 1):
            tasks = []

            for page in range(1, batch_size + 1):
                i = i + 1
                if i > max_pages:
                    break

                page_url = pages_url + str(i)
                tasks.append(parse_page(session, page_url))

            results = await asyncio.gather(*tasks)
            for articles_data in results:
                pages.extend(articles_data)

    return pages

async def parse_article(session, article_url):
    logging.debug('Handling article:' + article_url)
    file_name = article_url.strip('/').split('/')[-1]

    # skip pdf version
    if file_name.startswith('nomer-ot'):
        return

    file_path = os.path.join(articles_dir, file_name)

    async with session.get(article_url) as page:
        if page.status != 200:
            logging.debug('Could not handle page' +  str(page.status))
            return
        
        soup = BeautifulSoup(await page.text(), 'html.parser')
        content = soup.find(id='main-content').text
        with open(file_path, 'w') as f:
            f.write(content)


async def fetch_articles(articles):
    offset = 0
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = []

            for article in articles[offset:offset+batch_size]:
                article_url = article['href']
                tasks.append(parse_article(session, article_url))

            if not tasks:
                break

            await asyncio.gather(*tasks)
            offset = offset + batch_size
            await asyncio.sleep(1)
            logging.debug('Handled ' + str(offset) + ' articles')


async def main():
    action = sys.argv[1] 

    if action == 'pages':
        pages = await fetch_pages()
        json_formatted_str = json.dumps(pages, indent=2)
        with open(pages_file_path, 'w', encoding='utf-8') as f:
            f.write(json_formatted_str)

    if action == 'articles':
        if not os.path.exists(articles_dir):
            os.makedirs(articles_dir)
            logging.debug('Creating articles dir: ' + articles_dir)
            
        with open(pages_file_path, 'r') as f:
            articles = json.load(f)
            await fetch_articles(articles)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(e)
