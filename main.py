import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import re
from PyPDF2 import PdfReader, PdfWriter

# A4 300 DPI
A4_WIDTH = 2480
A4_HEIGHT = 3508

script_dir = os.path.dirname(os.path.abspath(__file__))

def fetch_urls_from_file(file_name):
    with open(file_name, 'r') as file:
        urls = file.readlines()
    return [url.strip() for url in urls]

def fetch_webpage_content(url):
    response = requests.get(url)
    return response.text

def parse_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup

def get_comic_title(soup):
    h3_tags = soup.find_all('h3')
    if len(h3_tags) > 1:
        comic_title = h3_tags[1].get_text().strip()  # Second <h3>
        comic_title = re.sub(r'[\/:*?"<>|]', '-', comic_title)
    else:
        comic_title = "output"
    return comic_title

def create_pdf_from_images(soup, comic_title, output_dir):
    img_tags = soup.find_all('img')
    
    images = []

    for idx, img in enumerate(img_tags):
        img_url = img['src']
        img_data = requests.get(img_url).content
        
        img = Image.open(BytesIO(img_data))
        
        img_ratio = img.width / img.height
        a4_ratio = A4_WIDTH / A4_HEIGHT
        
        if img_ratio > a4_ratio:
            new_width = A4_WIDTH
            new_height = round(new_width / img_ratio)
        else:
            new_height = A4_HEIGHT
            new_width = round(new_height * img_ratio)
        
        img = img.resize((new_width, new_height), Image.LANCZOS)
        
        a4_img = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), (255, 255, 255))
        
        offset = ((A4_WIDTH - new_width) // 2, (A4_HEIGHT - new_height) // 2)
        
        a4_img.paste(img, offset)
        
        images.append(a4_img)

    if images:
        pdf_file_name = f"{comic_title}.pdf"
        pdf_file_path = os.path.join(output_dir, pdf_file_name)
        images[0].save(pdf_file_path, save_all=True, append_images=images[1:])

    return pdf_file_path

def remove_first_and_last_page(pdf_file_path):
    reader = PdfReader(pdf_file_path)
    writer = PdfWriter()

    for page_num in range(1, len(reader.pages) - 1):
        writer.add_page(reader.pages[page_num])

    with open(pdf_file_path, "wb") as output_pdf:
        writer.write(output_pdf)

def main():
    links_file = os.path.join(script_dir, "links.txt")
    urls = fetch_urls_from_file(links_file)
    
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    for url in urls:
        html_content = fetch_webpage_content(url)
        soup = parse_html(html_content)
        comic_title = get_comic_title(soup)
        pdf_file_path = create_pdf_from_images(soup, comic_title, output_dir)
        remove_first_and_last_page(pdf_file_path)
        print(f"\n'{url}', '{pdf_file_path}' saved.")

if __name__ == "__main__":
    main()
