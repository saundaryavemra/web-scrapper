import requests
import time
from datetime import datetime, timedelta
import yaml

import gspread
from google.oauth2.service_account import Credentials
API_KEY = ''  # Your API key
MAX_PAGES = 5  # Maximum number of pages to fetch

def get_start_date(num_months):
    # Calculate the start date based on the specified number of months
    today = datetime.now().date()
    start_date = today - timedelta(days=(30 * max(num_months, 1)))
    return start_date.strftime("%Y-%m-%d")


def fetch_articles(topic, search_phrase, start_date):
    articles = []

    for page in range(1, MAX_PAGES + 1):
        url = f'https://api.nytimes.com/svc/search/v2/articlesearch.json?q={topic}&fq={search_phrase}&api-key={API_KEY}&page={page}&begin_date={start_date}'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            # Check if there are any articles available
            if 'response' in data and 'docs' in data['response']:
                docs = data['response']['docs']

                # Extract necessary fields from each article
                for doc in docs:
                    filtered_doc = {
                        'title': doc['headline']['main'],
                        'date': doc.get('pub_date', ''),
                        'description': doc.get('abstract', ''),
                        'image_link': extract_image_link(doc),
                        'article_link': doc.get('web_url', '')
                    }
                    articles.append(filtered_doc)
            else:
                print(f"No articles found on page {page}")

            # Pause before making the next request to avoid overwhelming the API
            time.sleep(6)
        else:
            print(f"Failed to fetch data from page {page}: {response.status_code}")

    return articles


def extract_image_link(article):
    multimedia = article.get('multimedia', [])
    for item in multimedia:
        if item.get('type', '') == 'image': #and 'https://' in item.get('url', ''):
            return 'https://www.nytimes.com/' + item['url']
    return ''


def open_spreadsheet(credentials_path, spreadsheet_link):
    # Authenticate with Google Sheets API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
    client = gspread.authorize(creds)
    
    spreadsheet_id = spreadsheet_link.split('/')[-1]
    
    spreadsheet = client.open_by_key(spreadsheet_id)
    return spreadsheet

def write_to_spreadsheet(articles, spreadsheet):
    # Open the first sheet of the spreadsheet
    sheet = spreadsheet.sheet1

    # Write headers to the first row
    headers = ['Title', 'Publication Date', 'Description', 'Image Link', 'Article Link']
    sheet.append_row(headers)

    # Write data to the spreadsheet
    for article in articles:
        row = [article['title'], article['date'], article['description'], article['image_link'], article['article_link']]
        sheet.append_row(row)



if __name__ == "__main__":
    # Fetch articles with default parameters
    
    with open("config.yml") as stream:
        try:
            args = yaml.safe_load(stream)
            num_months = args['NUM_MONTHS']
            topic = args['TOPIC']
            search_phrase = args['SEARCH_PHRASE']
        except yaml.YAMLError as exc:
            print(exc)

    start_date = get_start_date(num_months)

    articles = fetch_articles(topic, search_phrase, start_date)

    # Print the first 10 articles
    for idx, article in enumerate(articles[:10], 1):
        print(f"Article {idx}:")
        print(f"Title: {article['title']}")
        print(f"Date: {article['date']}")
        print(f"Description: {article['description']}")
        print(f"Image link: {article['image_link']}")
        print(f"Article link: {article['article_link']}")
        print("-" * 50)

    spreadsheet = open_spreadsheet('rare-shadow-422516-c5-1260be18f729.json', 'https://docs.google.com/spreadsheets/d/1YO5-RbvUeGvUPKSoYkFF-PwGs_G0kpSnwfQbhCGbD4c')

    # Write articles to the spreadsheet
    write_to_spreadsheet(articles, spreadsheet)