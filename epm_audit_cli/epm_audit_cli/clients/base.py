"""
Base API client for EPM Audit CLI.

Provides common functionality for making authenticated HTTP requests
to EPM Cloud APIs with retry logic and error handling.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from epm_audit_cli.exceptions import (
    EPMError,
    EPMConnectionError,
    EPMAuthenticationError,
    EPMRateLimitError,
    EPMValidationError,
)

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """
    Base API client for EPM Cloud REST APIs.

    Handles authentication headers, request retry logic, rate limiting,
    and error handling. Subclass for specific API endpoints.
    """

    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 5  # seconds

    def __init__(
        self,
        base_url: str,
        token: str,
        app_id: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """
        Initialize API client.

        Args:
            base_url: Base URL for API (e.g., https://company-fccs.epm.us-phoenix-1.oraclecloud.com)
            token: OAuth access token
            app_id: Application ID for logging
            timeout: Request timeout in seconds
        """
        # Ensure base URL doesn't have trailing slash
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.app_id = app_id
        self.timeout = timeout

        # Create requests session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        logger.debug(f"Initialized API client for {app_id}: {base_url}")

    def _getHeaders(self) -> Dict[str, str]:
        """
        Get HTTP headers for API requests.

        Returns:
            Dictionary of HTTP headers including auth
        """
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON request body
            headers: Additional headers

        Returns:
            Response JSON data

        Raises:
            EPMConnectionError: If connection fails
            EPMAuthenticationError: If authentication fails
            EPMRateLimitError: If rate limited
            EPMError: For other API errors
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = self._getHeaders()
        if headers:
            request_headers.update(headers)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=request_headers,
                timeout=self.timeout,
            )

            # Handle rate limiting with retry
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited, retrying after {retry_after}s")
                time.sleep(retry_after)
                return self._request(method, endpoint, params, json_data, headers)

            # Handle successful responses
            if response.status_code == 204:
                return {"success": True}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError as e:
            raise EPMConnectionError(
                f"Connection failed to {url}: {str(e)}",
                suggestion="Check if VPN is connected and hostname is correct",
            )
        except requests.exceptions.Timeout as e:
            raise EPMConnectionError(
                f"Request timed out after {self.timeout}s to {url}: {str(e)}",
                suggestion="EPM instance may be in maintenance or experiencing high load",
            )
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)

        # Should not reach here
        return {}

    def _handle_http_error(self, error: requests.exceptions.HTTPError) -> None:
        """
        Handle HTTP errors and raise appropriate exceptions.

        Args:
            error: HTTPError exception

        Raises:
            EPMAuthenticationError: For 401/403 errors
            EPMValidationError: For 400 errors
            EPMRateLimitError: For 429 errors
            EPMError: For other errors
        """
        response = error.response
        status_code = response.status_code

        if status_code == 401:
            raise EPMAuthenticationError(
                "Authentication failed: Token expired or invalid",
                suggestion="Run 'epm login <app>' to refresh credentials",
            )
        elif status_code == 403:
            raise EPMAuthenticationError(
                f"Permission denied: {response.text}",
                suggestion="Check required roles in EPM Cloud administration",
            )
        elif status_code == 404:
            raise EPMValidationError(
                f"Resource not found: {response.text}",
                suggestion="Verify the application ID and endpoint path",
            )
        elif status_code == 400:
            raise EPMValidationError(
                f"Bad request: {response.text}",
                suggestion="Check API parameters and request format",
            )
        elif status_code == 429:
            raise EPMRateLimitError(
                "Rate limit exceeded",
                suggestion="Wait before retrying or use --limit flag",
            )
        else:
            raise EPMError(
                f"API error ({status_code}): {response.text}",
                code=status_code,
            )

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response data
        """
        return self._request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make POST request.

        Args:
            endpoint: API endpoint
            json_data: JSON request body

        Returns:
            Response data
        """
        return self._request("POST", endpoint, json_data=json_data)

    def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make PUT request.

        Args:
            endpoint: API endpoint
            json_data: JSON request body

        Returns:
            Response data
        """
        return self._request("PUT", endpoint, json_data=json_data)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Make DELETE request.

        Args:
            endpoint: API endpoint

        Returns:
            Response data
        """
        return self._request("DELETE", endpoint)

    def _paginated_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Make paginated GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            limit: Maximum results to return

        Returns:
            List of results
        """
        if params is None:
            params = {}

        all_results: List[Dict[str, Any]] = []
        offset = 0
        page_size = min(limit, 100)  # API typically uses 100 max

        while len(all_results) < limit:
            params["offset"] = offset
            params["limit"] = page_size

            response = self.get(endpoint, params)
            items = response.get("items", response.get("result", []))

            if not items:
                break

            all_results.extend(items)

            if len(items) < page_size:
                break  # No more pages

            offset += page_size

        return all_results[:limit]

    def verify_connection(self) -> Dict[str, Any]:
        """
        Verify connection by making a lightweight API call.

        Returns:
            Connection info including version and endpoints

        Raises:
            EPMConnectionError: If connection fails
        """
        info: Dict[str, Any] = {}

        try:
            # Try interop API for version info
            response = self.get("/interop/rest/v1/info")
            info["api_version"] = response.get("apiVersion", "unknown")
            info["service"] = response.get("serviceName", "unknown")
        except EPMError:
            pass

        try:
            # Try applications endpoint
            response = self.get(
                "/interop/rest/v1/applications",
                params={"limit": 1}
            )
            info["applications_available"] = True
            info["app_count"] = response.get("totalResults", 0)
        except EPMError:
            info["applications_available"] = False

        return info