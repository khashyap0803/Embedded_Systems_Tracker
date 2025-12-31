#!/usr/bin/env python3
"""URL Verification Script - Check all resource URLs"""

from embedded_tracker.db import session_scope, init_db
from embedded_tracker.models import Resource
from sqlmodel import select
import urllib.request
import urllib.error
import ssl
import sys

def main():
    init_db()
    
    # SSL context for testing
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    def quick_test(url):
        """Quick URL test with 3 second timeout"""
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'},
                method='HEAD'
            )
            urllib.request.urlopen(req, timeout=3, context=ctx)
            return True, None
        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}"
        except urllib.error.URLError as e:
            return False, f"URL Error: {str(e.reason)[:30]}"
        except Exception as e:
            return False, str(e)[:40]
    
    broken = []
    
    with session_scope() as session:
        resources = session.exec(select(Resource).order_by(Resource.id)).all()
        total = len(resources)
        
        print(f"Testing {total} URLs...")
        sys.stdout.flush()
        
        for i, r in enumerate(resources):
            ok, error = quick_test(r.url)
            if not ok:
                broken.append({
                    'id': r.id,
                    'title': r.title,
                    'url': r.url,
                    'error': error
                })
            
            # Progress indicator
            if (i + 1) % 25 == 0:
                print(f"Progress: {i+1}/{total}")
                sys.stdout.flush()
    
    print("\n" + "=" * 70)
    print(f"BROKEN URLs: {len(broken)} out of {total}")
    print("=" * 70 + "\n")
    
    for b in broken:
        print(f"ID {b['id']}: {b['title'][:45]}")
        print(f"  URL: {b['url']}")
        print(f"  Error: {b['error']}")
        print()

if __name__ == "__main__":
    main()
