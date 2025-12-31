import json
import urllib.request
import urllib.error
import concurrent.futures
import sys
import ssl

# Ignore SSL certificate errors for this audit (some learning sites have bad certs)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def check_url(url_info):
    url = url_info['url']
    # Add a user agent so sites don't block us immediately
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        req = urllib.request.Request(url, headers=headers, method='HEAD')
        with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
            return {
                'title': url_info.get('title', 'Unknown'),
                'url': url,
                'status': response.getcode(),
                'ok': True
            }
    except (urllib.error.HTTPError, urllib.error.URLError, Exception) as e:
        # Try GET if HEAD fails
        try:
            req = urllib.request.Request(url, headers=headers, method='GET')
            with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
                 return {
                    'title': url_info.get('title', 'Unknown'),
                    'url': url,
                    'status': response.getcode(),
                    'ok': True
                }
        except Exception as e2:
             return {
                'title': url_info.get('title', 'Unknown'),
                'url': url,
                'status': str(e2),
                'ok': False
            }

def main():
    print("Loading roadmap data...")
    try:
        with open('embedded_tracker/data/roadmap_seed.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: embedded_tracker/data/roadmap_seed.json not found.")
        return

    urls_to_check = []
    
    # Extract URLs
    for phase in data.get('phases', []):
        for week in phase.get('weeks', []):
            for resource in week.get('resources', []):
                if resource.get('url'):
                    urls_to_check.append({'title': resource['title'], 'url': resource['url']})

    for project in data.get('projects', []):
        if project.get('repo_url'): urls_to_check.append({'title': project['name'] + ' Repo', 'url': project['repo_url']})
        if project.get('demo_url'): urls_to_check.append({'title': project['name'] + ' Demo', 'url': project['demo_url']})
    
    for cert in data.get('certifications', []):
        if cert.get('credential_url'): urls_to_check.append({'title': cert['name'], 'url': cert['credential_url']})

    print(f"Found {len(urls_to_check)} URLs to verify. Checking concurrently...")

    broken_urls = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_url, u): u for u in urls_to_check}
        for future in concurrent.futures.as_completed(future_to_url):
            result = future.result()
            if not result['ok']:
                # Filter out False Positives (LinkedIn often blocks bots with 999 or 403)
                if "HTTP Error 999" in str(result['status']) or "HTTP Error 403" in str(result['status']):
                     print(f"[WARN] Access denied (bot block) - {result['url']}")
                else:
                    print(f"[FAIL] {result['status']} - {result['url']}")
                    broken_urls.append(result)

    print("\n" + "="*50)
    print("URL AUDIT RESULTS")
    print("="*50)
    print(f"Total checked: {len(urls_to_check)}")
    print(f"Broken/Unreachable: {len(broken_urls)}")
    
    if broken_urls:
        print("\nCRITICAL ISSUES (Broken Links):")
        for link in broken_urls:
            print(f"{link['title'][:30]:<30} | {str(link['status']):<20} | {link['url']}")
    else:
        print("\n✅ All URLs are accessible.")

if __name__ == "__main__":
    main()
