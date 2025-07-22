"""
Helper classes and functions for Stack Overflow to GitHub Discussions migration.
"""

import os
import logging
import time
from github import Github, Auth
import requests

# Setup logging
logger = logging.getLogger(__name__)

class RateLimiter:
    """Manages API rate limiting with configurable intervals."""
    
    def __init__(self, min_interval: float = 1.0):
        """Initialize rate limiter with minimum interval between requests.
        
        Args:
            min_interval: Minimum seconds between API calls (default: 1.0)
        """
        self._last_api_call_time = 0
        self._min_interval = min_interval
    
    def wait_if_needed(self):
        """Ensure minimum time between API requests."""
        current_time = time.time()
        time_since_last_call = current_time - self._last_api_call_time
        
        if time_since_last_call < self._min_interval:
            sleep_time = self._min_interval - time_since_last_call
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self._last_api_call_time = time.time()
    
    def set_interval(self, interval: float):
        """Set the minimum interval between API calls.
        
        Args:
            interval: Minimum seconds between API calls
        """
        self._min_interval = interval
        logger.info(f"API interval set to {self._min_interval} seconds")
    
    @property
    def min_interval(self) -> float:
        """Get the current minimum interval."""
        return self._min_interval


class GitHubAuthManager:
    """Manages GitHub App authentication and token refresh."""
    
    def __init__(self):
        self._github_auth = None
        self._github_client = None
        self._initialized = False
    
    def initialize(self):
        """Initialize GitHub authentication using environment variables for App Auth.
        """
        installation_id = os.environ.get("GHD_INSTALLATION_ID")
        app_id = os.environ.get("GHD_APP_ID")
        # This should be the path to the private key file
        private_key_path = os.environ.get("GHD_PRIVATE_KEY")

        if not installation_id or not app_id or not private_key_path:
            raise ValueError("GHD_INSTALLATION_ID, GHD_APP_ID, and GHD_PRIVATE_KEY environment variables must be set")
        
        if not installation_id.isdigit() or not app_id.isdigit():
            raise ValueError("GHD_INSTALLATION_ID and GHD_APP_ID must be numeric")
        
        with open(private_key_path, "r") as key_file:
            private_key_content = key_file.read()

        self._github_auth = Auth.AppAuth(int(app_id), private_key_content).get_installation_auth(int(installation_id))
        self._github_client = Github(auth=self._github_auth)
        self._initialized = True
        
    def refresh_token(self):
       self.initialize()
    
    def get_token(self):
        """Get the GitHub token"""
        if not self._initialized:
            raise Exception("GitHub auth not initialized. Call initialize() first.")
        
        return  self._github_auth.token
    
    def get_client(self):
        """Get the current GitHub client."""
        if not self._initialized:
            raise Exception("GitHub auth not initialized. Call initialize() first.")
        return self._github_client
    
    @property
    def is_initialized(self):
        """Check if the auth manager has been initialized."""
        return self._initialized



class GraphQLHelper:
    """Helper class for GraphQL operations."""
    
    def __init__(self, github_auth_manager: GitHubAuthManager, rate_limiter: RateLimiter = None):
        """Initialize with GitHub auth manager and optional rate limiter.
        
        Args:
            github_auth_manager: Instance of GitHubAuthManager
            rate_limiter: Optional RateLimiter instance
        """
        self.github_auth_manager = github_auth_manager
        self.rate_limiter = rate_limiter or RateLimiter()

    def github_graphql_request(self, query, variables=None):
        """Helper to make a GitHub GraphQL API request and handle errors."""
        # Apply rate limiting before making the request
        self.rate_limiter.wait_if_needed()
        
        # Get current token (refresh if needed)
        current_token = self.github_auth_manager.get_token()
        
        headers = {
            'Authorization': f'bearer {current_token}',
            'Accept': 'application/vnd.github+json'
        }
        retry_count = 0
        max_retries = 5  
        base_sleep_time = 3
        
        while True:
            response = requests.post(
                'https://api.github.com/graphql',
                json={'query': query, 'variables': variables or {}},
                headers=headers
            )
            
            try:
                result = response.json()
            except Exception as e:
                logger.error(f"Failed to parse GraphQL response: {e}")
                raise
            
            if 'errors' in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                retry_count += 1
                if retry_count > max_retries:
                    logger.error("Max retries exceeded, aborting request.")
                    raise Exception(f"GraphQL errors: {result['errors']}")

                # Progressive backoff: 3, 7.5, 15, 37.5, 117 seconds
                sleep_time = base_sleep_time * (2.5 ** (retry_count - 1))
                logger.warning(f"Rate limit hit, retrying {retry_count}/{max_retries} after {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                continue
               
            if 'data' not in result:
                # Check if it's a credentials error in the response
                if 'message' in result and 'credentials' in result['message'].lower():
                    logger.warning("Bad credentials in response, attempting to refresh token...")
                    try:
                        current_token = self.github_auth_manager.refresh_token()
                        if current_token:
                            headers['Authorization'] = f'bearer {current_token}'
                            logger.info("Token refreshed, retrying request...")
                            continue
                        else:
                            raise Exception("Failed to refresh token")
                    except Exception as e:
                        logger.error(f"Token refresh failed: {e}")
                        raise Exception(f"Authentication failed: {result}")
                
                logger.error(f"No data in GraphQL response: {result}")
                raise Exception(f"No data in GraphQL response: {result}")
            
            return result['data']  
