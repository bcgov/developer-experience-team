#!/usr/bin/env python3
"""
URL validation using Playwright to handle authenticated GitHub requests.
This script requires manual login to GitHub. The script will prompt for login within the browser.
"""

import asyncio
import argparse
import logging
import os
import time
from typing import List, Dict, Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validate_urls_playwright.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PlaywrightURLValidator:
    """URL validator using Playwright for browser-based testing."""
    
    def __init__(self):
        """
        Initialize the Playwright URL validator.
        """
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def setup(self):
        """Set up the browser and context."""
        self.playwright = await async_playwright().start()
        
        # Launch browser in headful mode (visible browser window)
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=['--no-sandbox'] if os.getenv('CI') else []
        )
        
        # Create context
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Set up response logging
        self.page.on("response", self._log_response)
        
        logger.info("Browser setup complete")
    
    async def cleanup(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    def _log_response(self, response):
        """Log response details for debugging."""
        if response.status >= 300 and response.status < 400:
            logger.debug(f"Redirect: {response.status} {response.url} -> {response.headers.get('location', 'unknown')}")
    
    async def manual_login_to_github(self, org: str = None):
        """
        Open GitHub and wait for manual login, then handle SSO authentication.
        
        Args:
            org: GitHub organization name to test SSO access (optional)
        """
        try:
            logger.info("Opening GitHub for manual login...")
            
            # Step 1: Basic GitHub login
            await self.page.goto('https://github.com/login')
            
            print("\n" + "="*60)
            print("STEP 1: GITHUB LOGIN")
            print("="*60)
            print("Please log into GitHub in the browser window:")
            print("  1. Enter your GitHub username/password")
            print("  2. Complete 2FA if required")
            print("")
            print("Once you're logged into GitHub (at github.com homepage),")
            print("press ENTER in this terminal to continue to SSO setup...")
            print("="*60)
            
            # Wait for basic GitHub login
            input("Press ENTER when GitHub login is complete: ")
            
            # Step 2: SSO authentication (if org is provided)
            if org:
                logger.info(f"Initiating SSO authentication for organization: {org}")
                
                print("\n" + "="*60)
                print("STEP 2: SSO AUTHENTICATION")
                print("="*60)
                print(f"Now navigating to {org} organization...")
                print(f"The browser will navigate to https://github.com/{org}")
                print("SSO authentication will be required for this organization.")
                print("Please complete the SSO login when prompted in the browser.")
                print("="*60)
                
                # Navigate to org to trigger SSO
                org_url = f'https://github.com/{org}'
                try:
                    await self.page.goto(org_url, timeout=15000, wait_until='domcontentloaded')
                    
                    # Give a moment for the page to fully load and potential redirects
                    await asyncio.sleep(2)
                    
                    current_url = self.page.url
                    logger.info(f"Current URL after {org} navigation: {current_url}")
                    
                    # For GitHub orgs, we assume SSO is always needed
                    print("\n" + "="*60)
                    print("SSO AUTHENTICATION REQUIRED")
                    print("="*60)
                    print(f"Please complete your SSO authentication for {org} in the browser.")
                    print("This may involve:")
                    print("  1. Clicking 'Authorize' if you see an SSO prompt")
                    print("  2. Logging into Microsoft SSO if redirected")
                    print("  3. Completing any 2FA requirements")
                    print("")
                    print(f"Once you can see the GitHub {org} organization page,")
                    print("press ENTER in this terminal to continue...")
                    print("="*60)
                    
                    input(f"Press ENTER when you can access the GitHub {org} page: ")
                    
                    # Wait for page to stabilize after user interaction
                    await asyncio.sleep(2)
                    await self.page.wait_for_load_state('domcontentloaded', timeout=15000)
                    
                    final_url = self.page.url
                                   
                    # Verify we're actually on the org page
                    parsed_url = urlparse(final_url)
                    hostname = parsed_url.hostname or ""
                    
                    if hostname == "github.com" and org in final_url and 'login.microsoftonline.com' not in final_url:
                        print(f"\n✓ SSO authentication successful for {org}!")
                        logger.info(f"✓ SSO authentication successful for {org}!")
                        return True
                    else:
                        print(f"\n❌ SSO authentication may have failed.")
                        print(f"Current URL: {final_url}")
                        print(f"Please ensure you completed SSO and are on the GitHub {org} page.")
                        
                        # Ask user if they want to continue anyway
                        choice = input("Continue anyway? (y/n): ").lower().strip()
                        if choice == 'y' or choice == 'yes':
                            return True
                        else:
                            logger.error("SSO authentication required but not completed.")
                            return False
                                
                except Exception as e:
                    logger.warning(f"SSO navigation failed: {e}")
                    print(f"\n⚠ SSO test failed: {e}")
                    print("Continuing anyway - some URLs may require manual authentication.")
                    return True
            else:
                # No organization specified, skip SSO test
                print("\n✓ GitHub login complete (no organization specified for SSO test)")
                logger.info("✓ GitHub login complete (no organization specified)")
                return True
                
        except Exception as e:
            logger.error(f"Manual login process failed: {e}")
            return False
    
    async def validate_url(self, url: str, expected_url: str, timeout: int = 15000) -> Tuple[bool, int, str, str, List[Dict], bool, str]:
        """
        Validate that a URL returns HTTP 301 status and optionally check redirect destination.
        
        Args:
            url: The URL to validate
            expected_url: The expected redirect destination URL
            timeout: Page load timeout in milliseconds
            
        Returns:
            Tuple of (is_valid_redirect, final_status_code, final_url, error_message, redirect_chain, 
                     url_matches_expected, url_comparison_message)
        """
        redirect_chain = []
        error_message = ""
        
        try:
            logger.info(f"Validating URL: {url}")
            
            # Set up response capture
            responses = []
            
            def capture_response(response):
                responses.append({
                    'url': response.url,
                    'status': response.status,
                    'headers': dict(response.headers),
                    'redirected': response.request.redirected_from is not None
                })
                logger.debug(f"Response captured: {response.status} {response.url}")
            
            self.page.on("response", capture_response)
            
            response = await self.page.goto(url, timeout=timeout, wait_until='domcontentloaded')
            
            # Give a moment for any additional redirects to complete
            await asyncio.sleep(1)
            
            logger.info(f"Navigation completed: {response.status} {self.page.url}")
            
            self.page.remove_listener("response", capture_response)
            
            if not response:
                return False, 0, url, "No response received", []
            
            # Analyze redirect chain
            for resp in responses:
                if resp['status'] >= 300 and resp['status'] < 400:
                    redirect_chain.append({
                        'from_url': resp['url'],
                        'to_url': resp['headers'].get('location', 'unknown'),
                        'status_code': resp['status']
                    })
                    logger.debug(f"Redirect found: {resp['status']} {resp['url']} -> {resp['headers'].get('location', 'unknown')}")
            
            final_status = response.status
            final_url = self.page.url
            
            # Check for 301 redirect in the chain
            has_301 = any(r['status_code'] == 301 for r in redirect_chain)
            
            # URL comparison logic
            url_matches_expected = True
            url_comparison_message = ""
        
            # Normalize URLs for comparison (remove trailing slashes, etc.)
            normalized_final = final_url.rstrip('/')
            normalized_expected = expected_url.rstrip('/')
            
            if normalized_final == normalized_expected:
                url_matches_expected = True
                url_comparison_message = "✓ Final URL matches expected destination"
            else:
                url_matches_expected = False
                url_comparison_message = f"✗ Expected: {expected_url}, Got: {final_url}"
            
            logger.info(f"URL comparison for {url}: {url_comparison_message}")
        
            if has_301:
                logger.info(f"✓ URL {url} had 301 redirect in chain, final URL: {final_url}")
                return True, final_status, final_url, "", redirect_chain, url_matches_expected, url_comparison_message
            elif redirect_chain:
                error_message = f"Found redirects but no 301: {[r['status_code'] for r in redirect_chain]}"
                logger.warning(f"✗ URL {url} - {error_message}")
                return False, final_status, final_url, error_message, redirect_chain, url_matches_expected, url_comparison_message
            else:
                error_message = f"No redirects found, final status: {final_status}"
                logger.warning(f"✗ URL {url} - {error_message}")
                return False, final_status, final_url, error_message, redirect_chain, url_matches_expected, url_comparison_message
                
        except Exception as e:
            error_message = f"Navigation failed: {str(e)}"
            logger.error(f"✗ URL {url} - {error_message}")
            return False, 0, url, error_message, [], False, f"Error during validation: {str(e)}"
    
    async def validate_urls_from_file(self, file_path: str, delay_seconds: float = 1.0) -> Dict:
        """
        Validate URLs from a file with CSV format: originalLink,newLink
        
        Args:
            file_path: Path to file containing URLs in CSV format (originalLink,newLink per line)
            delay_seconds: Delay between requests
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'total': 0,
            'valid_redirects': 0,
            'invalid_redirects': 0,
            'url_matches': 0,
            'url_mismatches': 0,
            'details': []
        }
        
        try:
            url_pairs = []
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse CSV format: originalLink,newLink
                    parts = line.split(',', 1)  # Split on first comma only
                    if len(parts) == 2:
                        original_url = parts[0].strip()
                        expected_url = parts[1].strip()
                        url_pairs.append((original_url, expected_url))
                    else:
                        logger.warning(f"Line {line_num}: Invalid CSV format, skipping: {line}")
            
            logger.info(f"Found {len(url_pairs)} URL pairs to validate in {file_path}")
            
            for i, (original_url, expected_url) in enumerate(url_pairs, 1):
                logger.info(f"Processing {i}/{len(url_pairs)}: {original_url} -> {expected_url}")
                
                is_valid_redirect, status_code, final_url, error_message, redirect_chain, url_matches_expected, url_comparison_message = await self.validate_url(original_url, expected_url)
                
                result_detail = {
                    'original_url': original_url,
                    'expected_url': expected_url,
                    'is_valid_redirect': is_valid_redirect,
                    'final_status_code': status_code,
                    'final_url': final_url,
                    'error_message': error_message,
                    'redirect_chain': redirect_chain,
                    'url_matches_expected': url_matches_expected,
                    'url_comparison_message': url_comparison_message
                }
                
                results['details'].append(result_detail)
                results['total'] += 1
                
                if is_valid_redirect:
                    results['valid_redirects'] += 1
                else:
                    results['invalid_redirects'] += 1
                
                if url_matches_expected:
                  results['url_matches'] += 1
                else:
                  results['url_mismatches'] += 1
                
                # Add delay between requests
                if i < len(url_pairs):
                    await asyncio.sleep(delay_seconds)
            
            logger.info(f"Validation complete: {results['valid_redirects']}/{results['total']} URLs had 301 redirects")
            if results['url_matches'] + results['url_mismatches'] > 0:
                logger.info(f"URL comparison: {results['url_matches']}/{results['url_matches'] + results['url_mismatches']} URLs matched expected destinations")
            return results
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise
    
    def print_summary(self, results: Dict):
        """Print a summary of validation results."""
        print(f"\n{'='*60}")
        print("PLAYWRIGHT URL VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total URLs processed: {results['total']}")
        print(f"Valid (301) redirects: {results['valid_redirects']}")
        print(f"Invalid responses: {results['invalid_redirects']}")
        print(f"Redirect success rate: {(results['valid_redirects']/results['total']*100):.1f}%" if results['total'] > 0 else "No URLs processed")
        
        # URL comparison summary (only if we have expected URLs to compare)
        if results['url_matches'] + results['url_mismatches'] > 0:
            total_comparisons = results['url_matches'] + results['url_mismatches']
            print(f"URL destination matches: {results['url_matches']}")
            print(f"URL destination mismatches: {results['url_mismatches']}")
            print(f"URL match success rate: {(results['url_matches']/total_comparisons*100):.1f}%")
        
        print(f"\n{'='*60}")
        print("DETAILED RESULTS (FAILURES ONLY):")
        print(f"{'='*60}")
        
        failed_results = []
        for detail in results['details']:
            is_failure = (not detail['is_valid_redirect']) or (not detail['url_matches_expected'])
            if is_failure:
                failed_results.append(detail)
        
        if not failed_results:
            print("🎉 No failures detected! All URLs redirected properly and matched expected destinations.")
        else:
            for detail in failed_results:
                redirect_status = "✓ VALID REDIRECT" if detail['is_valid_redirect'] else "✗ INVALID REDIRECT"
                print(f"{redirect_status}: {detail['original_url']}")
                print(f"  Final URL: {detail['final_url']}")
                print(f"  Final Status: {detail['final_status_code']}")
                
                # Show expected URL comparison
                url_match_status = "✓" if detail['url_matches_expected'] else "✗"
                print(f"  Expected URL: {detail['expected_url']}")
                print(f"  URL Match: {url_match_status} {detail['url_comparison_message']}")
                
                if detail['redirect_chain']:
                    print(f"  Redirect Chain:")
                    for redirect in detail['redirect_chain']:
                        print(f"    {redirect['status_code']}: {redirect['from_url']} -> {redirect['to_url']}")
                
                if detail['error_message']:
                    print(f"  Error: {detail['error_message']}")
                print()


async def main():
    parser = argparse.ArgumentParser(
        description='Validate URLs using Playwright with manual browser authentication',
        epilog="""
File Format:
  The input file should contain URLs in CSV format:
  originalLink,newLink
  
  Where:
  - originalLink: The URL to test for redirects
  - newLink: The expected redirect destination URL
  
  Lines starting with # are treated as comments and ignored.

Examples:
  python validate_urls_playwright.py --file urls.txt
  python validate_urls_playwright.py --file urls.txt --org bcgov
  python validate_urls_playwright.py --file urls.txt --org mycompany --delay 2.0
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--file', required=True,
                       help='Path to file containing URLs in CSV format: originalLink,newLink')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay in seconds between requests (default: 1.0)')
    parser.add_argument('--org', 
                       help='GitHub organization name for SSO testing (e.g., bcgov, mycompany)')
    
    args = parser.parse_args()
    
    try:
        async with PlaywrightURLValidator() as validator:
            
            # Always perform manual login with optional SSO
            logger.info("Starting manual login process...")
            success = await validator.manual_login_to_github(org=args.org)
            if not success:
                logger.error("Manual login failed, exiting...")
                return 1
            
            print("\n" + "="*60)
            print("AUTHENTICATION COMPLETE")
            print("="*60)
            print("Starting URL validation process...")
            print("="*60)
            
            # Validate URLs
            results = await validator.validate_urls_from_file(args.file, delay_seconds=args.delay)
            
            # Print summary
            validator.print_summary(results)
            
            # Exit with non-zero code if any validations failed
            failed_redirects = results['invalid_redirects'] > 0
            failed_url_matches = results['url_mismatches'] > 0
            
            if failed_redirects or failed_url_matches:
                if failed_redirects:
                    logger.warning(f"{results['invalid_redirects']} URLs failed redirect validation")
                if failed_url_matches:
                    logger.warning(f"{results['url_mismatches']} URLs had incorrect redirect destinations")
                return 1
            else:
                logger.info("All URLs validated successfully!")
                return 0
                
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        return 1


if __name__ == '__main__':
    exit(asyncio.run(main()))
