import os
import re
import json
import argparse
import requests
from urllib.parse import urlparse

def extract_image_urls(text):
    md_pattern = r'!\[[^\]]*\]\(([^)]+)\)'
    html_pattern = r'<img [^>]*src=["\']([^"\'>]+)["\']'
    urls = re.findall(md_pattern, text or '')
    urls += re.findall(html_pattern, text or '')
    return urls

def get_image_id_and_ext(url):
    """Extract imageId (filename without extension) and extension from a URL."""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if '.' in filename:
        image_id, ext = filename.rsplit('.', 1)
        return image_id, '.' + ext
    return filename, ''

def download_image_api(base_url, image_id, ext, dest_folder, session=None, token=None):
    os.makedirs(dest_folder, exist_ok=True)
    api_url = f"{base_url.rstrip('/')}/images/{image_id}"
    headers = {}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    headers['Accept'] = 'image/png'
    sess = session or requests
    try:
        r = sess.get(api_url, headers=headers, timeout=15)
        r.raise_for_status()
        local_path = os.path.join(dest_folder, image_id + ext)
        with open(local_path, 'wb') as f:
            f.write(r.content)
        print(f"Downloaded: {api_url} -> {local_path}")
        return local_path
    except Exception as e:
        print(f"Failed to download {api_url}: {e}")
        return None

def extract_image_urls_from_fields(obj, fields):
    """Extract all image URLs from the given fields in an object (question, comment, or answer)."""
    urls = set()
    for field in fields:
        if field in obj:
            urls.update(extract_image_urls(obj[field]))
    return urls

def main():
    parser = argparse.ArgumentParser(description='Download all images referenced in markdown bodies from questions_answers_comments.json using the Stack Overflow for Teams API')
    parser.add_argument('--input', default='questions_answers_comments.json', help='Input JSON file')
    parser.add_argument('--output', default='so_exported_images', help='Output folder for images')
    parser.add_argument('--api-base-url', required=True, help='Stack Overflow for Teams API base URL (e.g. https://stackoverflow.developer.gov.bc.ca/api/v3)')
    parser.add_argument('--token', help='API token for authentication (if required)')
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        data = json.load(f)

    all_image_urls = set()
    fields = ['body', 'body_markdown', 'body_html']
    for q in data:
        all_image_urls.update(extract_image_urls_from_fields(q, fields))
        for c in q.get('comments', []):
            all_image_urls.update(extract_image_urls_from_fields(c, fields))
        for a in q.get('answers', []):
            all_image_urls.update(extract_image_urls_from_fields(a, fields))
            for c in a.get('comments', []):
                all_image_urls.update(extract_image_urls_from_fields(c, fields))

    print(f"Found {len(all_image_urls)} unique image URLs.")
    session = requests.Session()
    for url in all_image_urls:
        image_id, ext = get_image_id_and_ext(url)
        if image_id:
            download_image_api(args.api_base_url, image_id, ext, args.output, session=session, token=args.token)

if __name__ == '__main__':
    main()
