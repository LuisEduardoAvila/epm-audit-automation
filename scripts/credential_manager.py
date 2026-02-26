#!/usr/bin/env python3
"""
EPM Secure Credential Manager

Manages OAuth tokens, credentials, and connections for all EPM applications.
Supports OCI Vault, environment variables, and keyring backends.

Features:
- OAuth 2.0 token management with automatic refresh
- Shared tokens across application suites (prod/test/dev)
- Multi-backend credential storage (OCI Vault, env, keyring)
- Environment isolation (production, test, development)
- Extensible for any EPM application type

Usage:
    from credential_manager import CredentialManager
    
    creds = CredentialManager('config/applications.yaml')
    token = creds.get_oauth_token('fccs_prod')
    app_config = creds.get_application('fccs_prod')
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import yaml


class SecureCredentialStore:
    """
    Abstract credential storage backend
    """
    
    def get(self, key: str) -> str:
        """Get credential value"""
        raise NotImplementedError
    
    def set(self, key: str, value: str):
        """Set credential value"""
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        """Check if credential exists"""
        raise NotImplementedError


class OCIVaultBackend(SecureCredentialStore):
    """
    OCI Vault Secrets backend
    """
    
    def __init__(self, compartment_id: str = None):
        self.compartment_id = compartment_id
        self._secrets_cache = {}
        
        try:
            from oci import config as oci_config
            from oci.secrets import SecretsClient
            
            self._oci_config = oci_config.from_file()
            self._client = SecretsClient(self._oci_config)
            logging.info("OCI Vault backend initialized")
        except ImportError:
            raise RuntimeError(
                "OCI Python SDK not installed. "
                "Run: pip install oci"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OCI: {e}")
    
    def _parse_ref(self, ref: str) -> tuple:
        """
        Parse OCI vault reference
        Format: oci_vault://secret-name or ocid1.vaultsecret.oc1..xxx
        """
        if ref.startswith('oci_vault://'):
            secret_name = ref.replace('oci_vault://', '')
            return ('name', secret_name)
        elif ref.startswith('ocid1.vaultsecret'):
            return ('ocid', ref)
        else:
            return ('name', ref)
    
    def get(self, key: str) -> str:
        if key in self._secrets_cache:
            return self._secrets_cache[key]
        
        ref_type, ref_value = self._parse_ref(key)
        
        try:
            if ref_type == 'ocid':
                response = self._client.get_secret_bundle(secret_id=ref_value)
            else:
                # Search by name
                response = self._client.get_secret_bundle_by_name(
                    secret_name=ref_value,
                    vault_id=self.compartment_id
                )
            
            # Extract secret content
            secret_content = response.data.secret_bundle_content.content
            
            # Decode if base64
            import base64
            try:
                decoded = base64.b64decode(secret_content).decode('utf-8')
            except:
                decoded = secret_content
            
            # Cache for session
            self._secrets_cache[key] = decoded
            
            logging.debug(f"Retrieved secret: {ref_value}")
            return decoded
            
        except Exception as e:
            logging.error(f"Failed to retrieve secret {key}: {e}")
            raise
    
    def set(self, key: str, value: str):
        # OCI Vault update requires versioning
        # Implementation depends on specific use case
        raise NotImplementedError("Use OCI CLI or Console for updates")
    
    def exists(self, key: str) -> bool:
        try:
            self.get(key)
            return True
        except:
            return False


class EnvironmentBackend(SecureCredentialStore):
    """
    Environment variable backend (for testing/development)
    """
    
    def get(self, key: str) -> str:
        # Convert reference to env var name
        # e.g., "oci_vault://epm-oauth-prod" → EPM_OAUTH_PROD
        if '://' in key:
            key = key.split('/')[-1]
        
        env_key = key.upper().replace('-', '_')
        
        value = os.environ.get(env_key)
        if value is None:
            raise KeyError(f"Environment variable {env_key} not set")
        
        return value
    
    def set(self, key: str, value: str):
        env_key = key.upper().replace('-', '_')
        os.environ[env_key] = value
    
    def exists(self, key: str) -> bool:
        try:
            self.get(key)
            return True
        except:
            return False


class KeyringBackend(SecureCredentialStore):
    """
    OS keyring backend (secure local storage)
    """
    
    def __init__(self, service_name: str = "epm-audit-automation"):
        self.service_name = service_name
        
        try:
            import keyring
            self._keyring = keyring
        except ImportError:
            raise RuntimeError(
                "keyring not installed. "
                "Run: pip install keyring"
            )
    
    def get(self, key: str) -> str:
        # Parse reference
        if '://' in key:
            key = key.split('/')[-1]
        
        password = self._keyring.get_password(self.service_name, key)
        if password is None:
            raise KeyError(f"Credential {key} not found in keyring")
        
        return password
    
    def set(self, key: str, value: str):
        if '://' in key:
            key = key.split('/')[-1]
        
        self._keyring.set_password(self.service_name, key, value)
    
    def exists(self, key: str) -> bool:
        try:
            self.get(key)
            return True
        except:
            return False


class OAuthTokenManager:
    """
    Manages OAuth 2.0 tokens with automatic refresh
    """
    
    def __init__(self, credential_store: SecureCredentialStore):
        self._store = credential_store
        self._tokens = {}  # token cache
        self._lock_file = Path.home() / '.epm_audit' / 'oauth_tokens.json'
        
        # Ensure cache directory exists
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load cached tokens
        self._load_cached_tokens()
    
    def _load_cached_tokens(self):
        """Load tokens from disk cache"""
        try:
            if self._lock_file.exists():
                with open(self._lock_file) as f:
                    cached = json.load(f)
                    for scope, token_data in cached.items():
                        # Check if still valid
                        if self._is_token_valid(token_data):
                            self._tokens[scope] = token_data
        except Exception as e:
            logging.warning(f"Failed to load cached tokens: {e}")
    
    def _save_cached_tokens(self):
        """Save tokens to disk cache"""
        try:
            with open(self._lock_file, 'w') as f:
                json.dump(self._tokens, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Failed to save token cache: {e}")
    
    def _is_token_valid(self, token_data: Dict) -> bool:
        """Check if token is still valid"""
        if 'expires_at' not in token_data:
            return False
        
        # Refresh 5 minutes before expiry
        expiry = datetime.fromisoformat(token_data['expires_at'])
        return datetime.utcnow() < expiry - timedelta(minutes=5)
    
    def get_token(self, scope_config: Dict) -> str:
        """
        Get OAuth token for scope
        
        Returns valid token, fetching new one if needed
        """
        scope_name = scope_config['name']
        
        # Check cache
        if scope_name in self._tokens:
            if self._is_token_valid(self._tokens[scope_name]):
                logging.debug(f"Using cached token for {scope_name}")
                return self._tokens[scope_name]['access_token']
        
        # Fetch new token
        logging.info(f"Fetching new OAuth token for {scope_name}")
        
        try:
            token_data = self._fetch_token(scope_config)
            
            # Cache token
            self._tokens[scope_name] = token_data
            self._save_cached_tokens()
            
            return token_data['access_token']
            
        except Exception as e:
            logging.error(f"Failed to fetch token: {e}")
            raise
    
    def _fetch_token(self, scope_config: Dict) -> Dict:
        """
        Fetch new OAuth token from identity provider
        """
        import requests
        
        token_url = scope_config['token_url']
        client_id = self._store.get(scope_config['client_id_ref'])
        client_secret = self._store.get(scope_config['client_secret_ref'])
        scope = scope_config.get('scope', 'urn:opc:idm:tac.scope.epm')
        
        # OAuth 2.0 Client Credentials flow
        response = requests.post(
            token_url,
            data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': scope
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        
        response.raise_for_status()
        token_response = response.json()
        
        # Calculate expiry
        expires_in = token_response.get('expires_in', 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        return {
            'access_token': token_response['access_token'],
            'token_type': token_response.get('token_type', 'Bearer'),
            'expires_at': expires_at.isoformat(),
            'scope': scope,
            'fetched_at': datetime.utcnow().isoformat()
        }
    
    def invalidate_token(self, scope_name: str):
        """Force token refresh next time"""
        if scope_name in self._tokens:
            del self._tokens[scope_name]
            self._save_cached_tokens()


class CredentialManager:
    """
    Main credential management interface
    """
    
    def __init__(self, config_path: str, backend_type: str = 'auto'):
        """
        Initialize credential manager
        
        Args:
            config_path: Path to applications.yaml
            backend_type: 'oci_vault', 'env', 'keyring', or 'auto'
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize credential backend
        self._backend = self._init_backend(backend_type)
        
        # Initialize OAuth token manager
        self._oauth = OAuthTokenManager(self._backend)
        
        logging.info(f"CredentialManager initialized with {backend_type} backend")
    
    def _load_config(self) -> Dict:
        """Load application configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        
        with open(self.config_path) as f:
            return yaml.safe_load(f)
    
    def _init_backend(self, backend_type: str) -> SecureCredentialStore:
        """Initialize credential backend"""
        
        if backend_type == 'auto':
            # Auto-detect: prefer OCI Vault if available, else keyring, else env
            try:
                backend = OCIVaultBackend()
                logging.info("Using OCI Vault backend")
                return backend
            except Exception as e:
                logging.warning(f"OCI Vault unavailable: {e}")
            
            try:
                backend = KeyringBackend()
                logging.info("Using keyring backend")
                return backend
            except Exception as e:
                logging.warning(f"Keyring unavailable: {e}")
            
            logging.info("Using environment backend")
            return EnvironmentBackend()
        
        elif backend_type == 'oci_vault':
            return OCIVaultBackend()
        elif backend_type == 'keyring':
            return KeyringBackend()
        elif backend_type == 'env':
            return EnvironmentBackend()
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")
    
    def get_application(self, app_id: str) -> Dict:
        """Get application configuration"""
        apps = self.config.get('applications', {})
        
        if app_id not in apps:
            raise KeyError(f"Application {app_id} not found in config")
        
        app = apps[app_id]
        
        # Enrich with environment metadata
        env_id = app.get('environment')
        if env_id and env_id in self.config.get('environments', {}):
            app['_environment_meta'] = self.config['environments'][env_id]
        
        # Enrich with type metadata
        type_id = app.get('type')
        if type_id and type_id in self.config.get('types', {}):
            app['_type_meta'] = self.config['types'][type_id]
        
        return app
    
    def get_applications_by_environment(self, environment: str) -> List[str]:
        """Get list of application IDs in environment"""
        apps = self.config.get('applications', {})
        return [
            app_id for app_id, app in apps.items()
            if app.get('environment') == environment
        ]
    
    def get_applications_by_type(self, app_type: str) -> List[str]:
        """Get list of application IDs by type"""
        apps = self.config.get('applications', {})
        return [
            app_id for app_id, app in apps.items()
            if app.get('type') == app_type
        ]
    
    def get_oauth_token(self, app_id: str) -> str:
        """
        Get OAuth token for application
        
        Handles shared tokens across application suites
        """
        app = self.get_application(app_id)
        
        # Get token scope
        token_scope = app['authentication'].get('token_scope', 'default')
        
        # Get scope config
        oauth_config = self.config.get('oauth', {})
        if token_scope not in oauth_config:
            raise KeyError(f"OAuth scope {token_scope} not defined in config")
        
        scope_config = oauth_config[token_scope]
        
        return self._oauth.get_token(scope_config)
    
    def get_connection_url(self, app_id: str) -> str:
        """Get base connection URL for application"""
        app = self.get_application(app_id)
        return app['connection']['base_url']
    
    def get_region(self, app_id: str) -> str:
        """Get OCI region for application"""
        app = self.get_application(app_id)
        return app['connection'].get('region', 'us-phoenix-1')
    
    def get_headers(self, app_id: str) -> Dict[str, str]:
        """Get HTTP headers with authentication"""
        token = self.get_oauth_token(app_id)
        
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def list_environments(self) -> List[str]:
        """List available environments"""
        return list(self.config.get('environments', {}).keys())
    
    def list_application_types(self) -> List[str]:
        """List supported application types"""
        return list(self.config.get('types', {}).keys())
    
    def list_applications(self) -> List[Dict]:
        """List all applications with metadata"""
        apps = []
        for app_id, app in self.config.get('applications', {}).items():
            apps.append({
                'id': app_id,
                'name': app['name'],
                'type': app['type'],
                'environment': app['environment'],
                'criticality': app.get('metadata', {}).get('criticality', 'medium')
            })
        return apps
    
    def is_sox_relevant(self, app_id: str) -> bool:
        """Check if application is SOX-relevant"""
        app = self.get_application(app_id)
        return app.get('metadata', {}).get('sox_relevant', False)
    
    def get_audit_schedule(self, app_id: str) -> Dict:
        """Get audit schedule for application"""
        app = self.get_application(app_id)
        env = app.get('environment', 'production')
        
        audit_config = self.config.get('audit', {})
        schedules = audit_config.get('default_schedule', {})
        
        return schedules.get(env, {})


def main():
    """CLI for credential management"""
    parser = argparse.ArgumentParser(description='EPM Credential Manager')
    parser.add_argument('--config', default='config/applications.yaml',
                       help='Configuration file path')
    parser.add_argument('--backend', default='auto',
                       choices=['auto', 'oci_vault', 'env', 'keyring'],
                       help='Credential backend type')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List applications
    list_apps = subparsers.add_parser('list-apps', help='List configured applications')
    list_apps.add_argument('--env', help='Filter by environment')
    list_apps.add_argument('--type', help='Filter by type')
    
    # Get connection info
    get_conn = subparsers.add_parser('get-connection', help='Get connection info')
    get_conn.add_argument('app', help='Application ID')
    
    # Test OAuth
    test_oauth = subparsers.add_parser('test-oauth', help='Test OAuth token retrieval')
    test_oauth.add_argument('app', help='Application ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize manager
    try:
        manager = CredentialManager(args.config, args.backend)
    except Exception as e:
        print(f"Error initializing credential manager: {e}")
        sys.exit(1)
    
    # Execute command
    if args.command == 'list-apps':
        apps = manager.list_applications()
        
        if args.env:
            apps = [a for a in apps if a['environment'] == args.env]
        if args.type:
            apps = [a for a in apps if a['type'] == args.type]
        
        print("\nConfigured Applications:")
        print("-" * 80)
        print(f"{'ID':<20} {'Name':<30} {'Type':<15} {'Env':<10}")
        print("-" * 80)
        for app in apps:
            print(f"{app['id']:<20} {app['name']:<30} {app['type']:<15} {app['environment']:<10}")
        print()
    
    elif args.command == 'get-connection':
        try:
            app = manager.get_application(args.app)
            print(f"\nApplication: {app['name']}")
            print(f"Base URL: {manager.get_connection_url(args.app)}")
            print(f"Region: {manager.get_region(args.app)}")
            print(f"Environment: {app['environment']}")
            print(f"SOX Relevant: {'Yes' if manager.is_sox_relevant(args.app) else 'No'}")
            
            # Show schedule
            schedule = manager.get_audit_schedule(args.app)
            if schedule:
                print(f"\nAudit Schedule:")
                for report_type, cron in schedule.items():
                    print(f"  {report_type}: {cron}")
            
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif args.command == 'test-oauth':
        try:
            print(f"\nTesting OAuth for {args.app}...")
            token = manager.get_oauth_token(args.app)
            print(f"✓ Token retrieved successfully")
            print(f"  Length: {len(token)} characters")
            print(f"  Prefix: {token[:20]}...")
        except Exception as e:
            print(f"✗ Failed: {e}")
            sys.exit(1)


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()
