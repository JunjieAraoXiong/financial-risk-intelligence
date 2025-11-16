"""
Secure configuration loader for FEEKG.
Loads AllegroGraph credentials from .env without exposing them.
"""

import os
from dotenv import load_dotenv
from franz.openrdf.connect import ag_connect

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration container for FEEKG"""

    def __init__(self):
        self.ag_url = os.getenv('AG_URL')
        self.ag_user = os.getenv('AG_USER')
        self.ag_pass = os.getenv('AG_PASS')
        self.ag_repo = os.getenv('AG_REPO', 'feekg_dev')

        # Validate required variables (skip in production/Railway)
        # Railway sets env vars directly, no .env file needed
        is_production = os.getenv('FLASK_ENV') == 'production' or os.getenv('RAILWAY_ENVIRONMENT')
        if not is_production and not all([self.ag_url, self.ag_user, self.ag_pass]):
            raise ValueError(
                "Missing required environment variables. "
                "Please check .env file contains AG_URL, AG_USER, AG_PASS"
            )

        # Parse URL components (if URL is provided)
        self.ag_host = self._parse_host(self.ag_url) if self.ag_url else None
        self.ag_port = self._parse_port(self.ag_url) if self.ag_url else None

    def _parse_host(self, url):
        """Extract host from URL"""
        host = url.replace('https://', '').replace('http://', '')
        host = host.rstrip('/')
        if ':' in host:
            host = host.split(':')[0]
        return host

    def _parse_port(self, url):
        """Extract port from URL or use default"""
        # AllegroGraph default HTTPS port
        if ':' in url:
            parts = url.split(':')
            if len(parts) >= 3:  # http://host:port
                return int(parts[-1].rstrip('/'))
        return 10035  # Default AG port

    def get_ag_connection(self):
        """
        Create and return AllegroGraph connection using ag_connect.

        Returns:
            AllegroGraph connection object

        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Use ag_connect helper function
            conn = ag_connect(
                repo=self.ag_repo,
                host=self.ag_host,
                port=self.ag_port,
                user=self.ag_user,
                password=self.ag_pass,
                create=True,  # Create repo if it doesn't exist
                clear=False   # Don't clear existing data
            )
            return conn

        except Exception as e:
            # Don't print password in error messages
            safe_error = str(e).replace(self.ag_pass, '***')
            raise ConnectionError(f"Failed to connect to AllegroGraph: {safe_error}")

    def mask_credentials(self):
        """Return config with masked sensitive data (for logging)"""
        return {
            'ag_url': self.ag_url,
            'ag_host': self.ag_host,
            'ag_port': self.ag_port,
            'ag_user': f"{self.ag_user[:2]}***" if len(self.ag_user) > 2 else "***",
            'ag_repo': self.ag_repo,
            'ag_pass': '***'
        }


# Global config instance
config = Config()


def get_ag_connection():
    """
    Convenience function to get AllegroGraph connection.

    Returns:
        AllegroGraph connection object

    Example:
        >>> from config.secrets import get_ag_connection
        >>> conn = get_ag_connection()
        >>> size = conn.size()
        >>> print(f"Repository has {size} triples")
        >>> conn.close()
    """
    return config.get_ag_connection()


def get_masked_config():
    """
    Get configuration with masked credentials (safe for logging).

    Returns:
        dict: Configuration with masked sensitive data
    """
    return config.mask_credentials()


if __name__ == "__main__":
    # Test configuration loading
    print("Testing configuration...")
    print(f"Masked config: {get_masked_config()}")
    print("✅ Configuration loaded successfully!")
