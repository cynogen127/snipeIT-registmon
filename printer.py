#!/usr/bin/env python3
"""
Printer to Snipe-IT Integration (Config File Version)
Reads configuration from auth.txt and printer IPs from printers.txt
"""

from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    get_cmd,
    next_cmd
)
from typing import Dict, Optional, List, Tuple
import asyncio
import logging
import warnings
import requests
import json
from datetime import datetime
import ipaddress
import argparse
import os
import sys

# Suppress warnings
warnings.filterwarnings('ignore', message='.*pysnmp-lextudio.*')
warnings.filterwarnings('ignore', message='.*Unverified HTTPS.*')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigReader:
    """Configuration file reader"""

    @staticmethod
    def read_auth_config(filepath: str = 'auth.txt') -> Dict[str, str]:
        """
        Read authentication configuration from file

        Expected format:
        url=http://192.168.0.126:8000/api/v1
        token=YOUR_TOKEN_HERE
        community=public

        Args:
            filepath: Path to auth.txt file

        Returns:
            Dictionary with config values
        """
        config = {
            'url': None,
            'token': None,
            'community': 'public'
        }

        if not os.path.exists(filepath):
            logger.error(f"Configuration file not found: {filepath}")
            return config

        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip().lower()
                        value = value.strip()

                        if key in config:
                            config[key] = value
                            logger.debug(f"Loaded config: {key}={'*' * 10 if key == 'token' else value}")

            # Validate required fields
            if not config['url']:
                logger.error("Missing 'url' in auth.txt")
            if not config['token']:
                logger.error("Missing 'token' in auth.txt")

            return config

        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            return config

    @staticmethod
    def read_printer_ips(filepath: str = 'printers.txt') -> List[str]:
        """
        Read printer IPs from file

        Args:
            filepath: Path to printers.txt file

        Returns:
            List of IP addresses
        """
        ips = []

        if not os.path.exists(filepath):
            logger.warning(f"Printer list file not found: {filepath}")
            return ips

        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Support IP, range, or subnet per line
                    ips.append(line)
                    logger.debug(f"Loaded printer target: {line}")

            logger.info(f"Loaded {len(ips)} printer target(s) from {filepath}")
            return ips

        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            return ips


class SnipeITClient:
    """Client for Snipe-IT API"""

    def __init__(self, base_url: str, api_token: str):
        """
        Initialize Snipe-IT client

        Args:
            base_url: Snipe-IT API base URL (e.g., http://192.168.0.126:8000/api/v1)
            api_token: Snipe-IT API token
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Verify URL format
        if '/api/v1' not in self.base_url:
            logger.warning("URL should include /api/v1 path (e.g., http://server:8000/api/v1)")

    def _make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Make API request to Snipe-IT"""
        endpoint = endpoint.lstrip('/')
        url = f"{self.base_url}/{endpoint}"

        try:
            logger.debug(f"API Request: {method} {url}")

            if method.upper() == 'GET':
                response = self.session.get(url, params=params, verify=False)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, verify=False)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, verify=False)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, json=data, verify=False)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, verify=False)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            logger.debug(f"Response Status: {response.status_code}")
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {url}")
            logger.error(f"Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    logger.error(f"Response: {e.response.text}")
                except:
                    pass
            return None

    def get_models(self, search: str = None) -> List[dict]:
        """Get all models or search for specific model"""
        params = {'limit': 500}
        if search:
            params['search'] = search

        result = self._make_request('GET', 'models', params=params)
        if result and 'rows' in result:
            return result['rows']
        return []

    def get_or_create_model(self, manufacturer: str, model_name: str, category_id: int) -> Optional[int]:
        """Get existing model ID or create new model"""
        models = self.get_models(search=model_name)
        for model in models:
            if model.get('name', '').lower() == model_name.lower():
                logger.info(f"Found existing model: {model_name} (ID: {model['id']})")
                return model['id']

        logger.info(f"Creating new model: {model_name}")
        model_data = {
            'name': model_name,
            'manufacturer_id': self.get_or_create_manufacturer(manufacturer),
            'category_id': category_id,
            'fieldset_id': None
        }

        result = self._make_request('POST', 'models', data=model_data)
        if result and result.get('status') == 'success':
            model_id = result['payload']['id']
            logger.info(f"Model created successfully (ID: {model_id})")
            return model_id

        logger.error(f"Failed to create model: {model_name}")
        return None

    def get_manufacturers(self, search: str = None) -> List[dict]:
        """Get all manufacturers or search for specific manufacturer"""
        params = {'limit': 500}
        if search:
            params['search'] = search

        result = self._make_request('GET', 'manufacturers', params=params)
        if result and 'rows' in result:
            return result['rows']
        return []

    def get_or_create_manufacturer(self, name: str) -> Optional[int]:
        """Get existing manufacturer ID or create new manufacturer"""
        manufacturers = self.get_manufacturers(search=name)
        for mfg in manufacturers:
            if mfg.get('name', '').lower() == name.lower():
                logger.info(f"Found existing manufacturer: {name} (ID: {mfg['id']})")
                return mfg['id']

        logger.info(f"Creating new manufacturer: {name}")
        mfg_data = {'name': name}

        result = self._make_request('POST', 'manufacturers', data=mfg_data)
        if result and result.get('status') == 'success':
            mfg_id = result['payload']['id']
            logger.info(f"Manufacturer created successfully (ID: {mfg_id})")
            return mfg_id

        logger.error(f"Failed to create manufacturer: {name}")
        return None

    def get_categories(self, search: str = None) -> List[dict]:
        """Get all categories or search for specific category"""
        params = {'limit': 500}
        if search:
            params['search'] = search

        result = self._make_request('GET', 'categories', params=params)
        if result and 'rows' in result:
            return result['rows']
        return []

    def get_or_create_category(self, name: str, category_type: str = 'asset') -> Optional[int]:
        """Get existing category ID or create new category"""
        categories = self.get_categories(search=name)
        for cat in categories:
            if cat.get('name', '').lower() == name.lower():
                logger.info(f"Found existing category: {name} (ID: {cat['id']})")
                return cat['id']

        logger.info(f"Creating new category: {name}")
        cat_data = {
            'name': name,
            'category_type': category_type
        }

        result = self._make_request('POST', 'categories', data=cat_data)
        if result and result.get('status') == 'success':
            cat_id = result['payload']['id']
            logger.info(f"Category created successfully (ID: {cat_id})")
            return cat_id

        logger.error(f"Failed to create category: {name}")
        return None

    def get_status_labels(self) -> List[dict]:
        """Get all status labels"""
        result = self._make_request('GET', 'statuslabels')
        if result and 'rows' in result:
            return result['rows']
        return []

    def get_deployable_status_id(self) -> Optional[int]:
        """Get ID of deployable status"""
        status_labels = self.get_status_labels()

        if not status_labels:
            logger.error("No status labels found in Snipe-IT")
            # Try to create a default deployable status
            return self.create_deployable_status()

        # First, try to find a status with deployable type
        for status in status_labels:
            status_type = status.get('status_type', '').lower()
            status_name = status.get('name', '').lower()

            # Skip non-deployable statuses
            if any(word in status_name for word in ['recycle', 'archived', 'broken', 'lost', 'repair']):
                continue

            if status_type == 'deployable':
                logger.info(f"Found deployable status: {status['name']} (ID: {status['id']})")
                return status['id']

        # Second, try to find by common deployable names
        deployable_keywords = ['ready', 'deploy', 'active', 'available', 'in stock', 'stock']
        for status in status_labels:
            status_name = status.get('name', '').lower()

            # Skip non-deployable statuses
            if any(word in status_name for word in ['recycle', 'archived', 'broken', 'lost', 'repair']):
                continue

            for keyword in deployable_keywords:
                if keyword in status_name:
                    logger.info(f"Found deployable status by keyword: {status['name']} (ID: {status['id']})")
                    return status['id']

        # Third, filter out obvious non-deployable statuses and use first remaining
        for status in status_labels:
            status_name = status.get('name', '').lower()
            status_type = status.get('status_type', '').lower()

            # Skip non-deployable statuses
            if any(word in status_name for word in ['recycle', 'archived', 'broken', 'lost', 'repair', 'dispose']):
                continue

            # Use this one
            logger.warning(f"Using status: {status['name']} (ID: {status['id']}) - Type: {status_type}")
            return status['id']

        # Last resort - try to create a new deployable status
        logger.warning("No suitable deployable status found, attempting to create one...")
        return self.create_deployable_status()

    def create_deployable_status(self) -> Optional[int]:
        """Create a new deployable status label"""
        logger.info("Creating new 'Ready to Deploy' status label...")

        status_data = {
            'name': 'Ready to Deploy',
            'status_type': 'deployable',
            'color': '00FF00',  # Green color
            'show_in_nav': True,
            'default_label': False
        }

        result = self._make_request('POST', 'statuslabels', data=status_data)
        if result and result.get('status') == 'success':
            status_id = result['payload']['id']
            logger.info(f"Status label created successfully (ID: {status_id})")
            return status_id

        logger.error("Failed to create deployable status label")
        logger.error("Please manually create a status label in Snipe-IT:")
        logger.error("  Settings → Status Labels → Create New")
        logger.error("  Name: 'Ready to Deploy', Status Type: 'Deployable'")
        return None

    def search_asset_by_serial(self, serial: str) -> Optional[dict]:
        """Search for asset by serial number"""
        result = self._make_request('GET', 'hardware', params={'search': serial, 'limit': 1})
        if result and 'rows' in result and len(result['rows']) > 0:
            asset = result['rows'][0]
            if asset.get('serial', '').upper() == serial.upper():
                return asset
        return None

    def create_asset(self, asset_data: dict) -> Optional[int]:
        """Create new asset in Snipe-IT"""
        logger.info(f"Creating asset: {asset_data.get('name', 'Unknown')}")

        result = self._make_request('POST', 'hardware', data=asset_data)
        if result and result.get('status') == 'success':
            asset_id = result['payload']['id']
            logger.info(f"Asset created successfully (ID: {asset_id})")
            return asset_id

        logger.error(f"Failed to create asset: {asset_data.get('name', 'Unknown')}")
        return None

    def update_asset(self, asset_id: int, asset_data: dict) -> bool:
        """Update existing asset in Snipe-IT"""
        logger.info(f"Updating asset ID: {asset_id}")

        result = self._make_request('PATCH', f'hardware/{asset_id}', data=asset_data)
        if result and result.get('status') == 'success':
            logger.info(f"Asset updated successfully (ID: {asset_id})")
            return True

        logger.error(f"Failed to update asset ID: {asset_id}")
        return False


class PrinterBrand:
    """Printer brand configurations"""

    STANDARD_TONER_LEVEL = '1.3.6.1.2.1.43.11.1.1.9.1'
    STANDARD_TONER_MAX = '1.3.6.1.2.1.43.11.1.1.8.1'
    STANDARD_TONER_NAME = '1.3.6.1.2.1.43.11.1.1.6.1'

    COLOR_NAMES = {
        'black': ['black', 'bk', 'k'],
        'cyan': ['cyan', 'c'],
        'magenta': ['magenta', 'm'],
        'yellow': ['yellow', 'y'],
    }

    COLOR_MAP = {1: 'black', 2: 'cyan', 3: 'magenta', 4: 'yellow'}


class PrinterScanner:
    """Printer scanner with SNMP"""

    def __init__(self, ip_address: str, community: str = 'public',
                 timeout: int = 2, retries: int = 1):
        self.ip_address = ip_address
        self.community = community
        self.timeout = timeout
        self.retries = retries
        self.port = 161

    async def _snmp_get(self, oid: str) -> Optional[any]:
        """Execute SNMP GET request"""
        try:
            iterator = await get_cmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=0),
                await UdpTransportTarget.create((self.ip_address, self.port),
                                                timeout=self.timeout,
                                                retries=self.retries),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )

            error_indication, error_status, error_index, var_binds = iterator

            if error_indication or error_status:
                return None
            return var_binds[0][1]
        except Exception:
            return None

    async def _snmp_walk(self, oid: str, max_rows: int = 100) -> List[Tuple[str, any]]:
        """Execute SNMP WALK request"""
        results = []
        try:
            count = 0
            async for (error_indication, error_status, error_index, var_binds) in next_cmd(
                    SnmpEngine(),
                    CommunityData(self.community),
                    await UdpTransportTarget.create((self.ip_address, self.port),
                                                   timeout=self.timeout,
                                                   retries=self.retries),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                    lexicographicMode=False):

                if error_indication or error_status:
                    break

                for var_bind in var_binds:
                    results.append((var_bind[0].prettyPrint(), var_bind[1].prettyPrint()))
                    count += 1
                    if count >= max_rows:
                        break

                if count >= max_rows:
                    break
        except Exception:
            pass

        return results

    def _identify_color(self, name: str) -> str:
        """Identify color from toner name"""
        name_lower = name.lower()
        for color, variations in PrinterBrand.COLOR_NAMES.items():
            for variant in variations:
                if variant in name_lower:
                    return color
        return name

    async def get_printer_info(self) -> Optional[dict]:
        """Get printer information"""
        sys_descr = await self._snmp_get('1.3.6.1.2.1.1.1.0')
        if not sys_descr:
            return None

        descr_str = str(sys_descr).lower()
        printer_keywords = ['printer', 'print', 'xerox', 'konica', 'canon',
                           'brother', 'epson', 'ricoh', 'lexmark', 'samsung', 'hp']

        if not any(keyword in descr_str for keyword in printer_keywords):
            return None

        info = {
            'ip': self.ip_address,
            'description': str(sys_descr),
            'timestamp': datetime.now().isoformat()
        }

        printer_name = await self._snmp_get('1.3.6.1.2.1.25.3.2.1.3.1')
        if printer_name:
            info['name'] = str(printer_name)

        serial = await self._snmp_get('1.3.6.1.2.1.43.5.1.1.17.1')
        if serial:
            info['serial'] = str(serial)

        page_count = await self._snmp_get('1.3.6.1.2.1.43.10.2.1.4.1.1')
        if page_count:
            try:
                info['page_count'] = int(page_count)
            except:
                pass

        info['toner'] = await self._get_toner_levels()

        return info

    async def _get_toner_levels(self) -> dict:
        """Get toner levels"""
        toner_data = {}

        for index, color in PrinterBrand.COLOR_MAP.items():
            current_oid = f"{PrinterBrand.STANDARD_TONER_LEVEL}.{index}"
            max_oid = f"{PrinterBrand.STANDARD_TONER_MAX}.{index}"

            current_level = await self._snmp_get(current_oid)
            max_level = await self._snmp_get(max_oid)

            if current_level is not None:
                try:
                    current_val = int(current_level)
                    max_val = int(max_level) if max_level is not None else 100

                    if max_val > 0:
                        percentage = round((current_val / max_val) * 100, 1)
                    else:
                        percentage = current_val

                    toner_data[color] = {
                        'current': current_val,
                        'max': max_val,
                        'percentage': percentage
                    }
                except (ValueError, TypeError):
                    pass

        if not toner_data:
            names_walk = await self._snmp_walk(PrinterBrand.STANDARD_TONER_NAME, max_rows=20)
            levels_walk = await self._snmp_walk(PrinterBrand.STANDARD_TONER_LEVEL, max_rows=20)
            max_walk = await self._snmp_walk(PrinterBrand.STANDARD_TONER_MAX, max_rows=20)

            names_dict = {oid.split('.')[-1]: value for oid, value in names_walk}
            levels_dict = {oid.split('.')[-1]: value for oid, value in levels_walk}
            max_dict = {oid.split('.')[-1]: value for oid, value in max_walk}

            for index in names_dict.keys():
                if index in levels_dict:
                    try:
                        name = names_dict[index]
                        color = self._identify_color(name)
                        current_val = int(levels_dict[index])
                        max_val = int(max_dict.get(index, 100))

                        if max_val > 0:
                            percentage = round((current_val / max_val) * 100, 1)
                        else:
                            percentage = current_val

                        toner_data[color] = {
                            'current': current_val,
                            'max': max_val,
                            'percentage': percentage,
                            'name': name
                        }
                    except (ValueError, TypeError):
                        pass

        return toner_data


class NetworkScanner:
    """Network scanner"""

    def __init__(self, community: str = 'public', timeout: int = 2, max_concurrent: int = 50):
        self.community = community
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)

    def parse_ip_range(self, ip_range: str) -> List[str]:
        """Parse IP range into list of IPs"""
        ips = []
        try:
            if '/' in ip_range:
                network = ipaddress.ip_network(ip_range, strict=False)
                ips = [str(ip) for ip in network.hosts()]
            elif '-' in ip_range:
                parts = ip_range.split('-')
                if len(parts) == 2:
                    base_ip = parts[0].strip()
                    end_octet = int(parts[1].strip())
                    ip_parts = base_ip.split('.')
                    if len(ip_parts) == 4:
                        base = '.'.join(ip_parts[:3])
                        start_octet = int(ip_parts[3])
                        for i in range(start_octet, end_octet + 1):
                            ips.append(f"{base}.{i}")
            else:
                ips = [ip_range.strip()]
        except Exception as e:
            logger.error(f"Error parsing IP range '{ip_range}': {e}")
        return ips

    async def scan_single_host(self, ip: str) -> Optional[dict]:
        """Scan a single host"""
        async with self.semaphore:
            try:
                scanner = PrinterScanner(ip, self.community, self.timeout)
                info = await scanner.get_printer_info()
                if info:
                    logger.info(f"✓ Found printer at {ip}")
                return info
            except Exception as e:
                logger.debug(f"Error scanning {ip}: {e}")
                return None

    async def scan_network(self, ip_list: List[str]) -> List[dict]:
        """Scan multiple IPs"""
        logger.info(f"Scanning {len(ip_list)} IP addresses...")
        tasks = [self.scan_single_host(ip) for ip in ip_list]
        results = await asyncio.gather(*tasks)
        printers = [r for r in results if r is not None]
        logger.info(f"Found {len(printers)} printer(s)")
        return printers


class PrinterToSnipeIT:
    """Main integration class"""

    def __init__(self, snipeit_url: str, api_token: str, community: str = 'public'):
        self.snipeit = SnipeITClient(snipeit_url, api_token)
        self.community = community
        self.category_id = None
        self.status_id = None

    def initialize(self):
        """Initialize required Snipe-IT entities"""
        logger.info("Initializing Snipe-IT integration...")

        self.category_id = self.snipeit.get_or_create_category('Printers', 'asset')
        if not self.category_id:
            logger.error("Failed to get/create Printer category")
            return False

        self.status_id = self.snipeit.get_deployable_status_id()
        if not self.status_id:
            logger.error("Failed to get status label")
            return False

        logger.info("Initialization complete")
        return True

    def extract_manufacturer_model(self, description: str, name: str) -> Tuple[str, str]:
        """Extract manufacturer and model from printer info"""
        manufacturers = ['FUJI XEROX', 'XEROX', 'HP', 'CANON', 'BROTHER',
                        'EPSON', 'RICOH', 'KONICA MINOLTA', 'SAMSUNG', 'LEXMARK']

        manufacturer = 'Unknown'
        model = 'Unknown'

        name_upper = name.upper()
        for mfg in manufacturers:
            if mfg in name_upper:
                manufacturer = mfg.title()
                model = name.replace(mfg, '').replace('Multifunction Printer', '') \
                           .replace('Multifunction System', '').strip()
                if model:
                    return manufacturer, model
                break

        desc_upper = description.upper()
        for mfg in manufacturers:
            if mfg in desc_upper:
                manufacturer = mfg.title()
                parts = description.split(';')
                if parts:
                    model = parts[0].replace(mfg, '').strip()
                if model and model != 'Unknown':
                    return manufacturer, model
                break

        if model == 'Unknown' and name:
            model = name

        return manufacturer, model

    def format_toner_status(self, toner_data: dict) -> str:
        """Format toner data into readable string"""
        if not toner_data:
            return "No toner data available"

        status_parts = []
        for color, data in sorted(toner_data.items()):
            pct = data.get('percentage', 0)
            current = data.get('current', 0)
            max_val = data.get('max', 0)

            if pct < 20:
                status_icon = "✗ CRITICAL"
            elif pct < 50:
                status_icon = "⚠ LOW"
            else:
                status_icon = "✓ OK"

            status_parts.append(f"{color.upper()}: {pct}% ({current}/{max_val}) {status_icon}")

        return "\n".join(status_parts)

    def create_or_update_printer(self, printer_info: dict) -> bool:
        """Create or update printer in Snipe-IT"""
        ip = printer_info.get('ip', 'Unknown')
        serial = printer_info.get('serial', '').strip()
        name = printer_info.get('name', f"Printer-{ip}")
        description = printer_info.get('description', '')
        page_count = printer_info.get('page_count')
        toner = printer_info.get('toner', {})

        if not serial:
            logger.warning(f"Printer at {ip} has no serial number, using IP as identifier")
            serial = ip.replace('.', '-')

        manufacturer, model_name = self.extract_manufacturer_model(description, name)

        logger.info(f"Processing: {name} ({manufacturer} {model_name})")
        logger.info(f"  Serial: {serial}, IP: {ip}")

        model_id = self.snipeit.get_or_create_model(manufacturer, model_name, self.category_id)
        if not model_id:
            logger.error(f"Failed to get/create model for {name}")
            return False

        asset_data = {
            'model_id': model_id,
            'status_id': self.status_id,
            'serial': serial,
            'name': name,
        }

        notes_parts = [
            f"IP Address: {ip}",
            f"Description: {description[:100]}",
            f"Last Scanned: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]

        if page_count is not None:
            notes_parts.append(f"Total Pages: {page_count:,}")

        if toner:
            notes_parts.append("\nToner Status:")
            notes_parts.append(self.format_toner_status(toner))

        asset_data['notes'] = "\n".join(notes_parts)

        existing_asset = self.snipeit.search_asset_by_serial(serial)

        if existing_asset:
            asset_id = existing_asset['id']
            logger.info(f"  → Updating existing asset (ID: {asset_id})")
            success = self.snipeit.update_asset(asset_id, asset_data)
        else:
            logger.info(f"  → Creating new asset")
            asset_id = self.snipeit.create_asset(asset_data)
            success = asset_id is not None

        if success:
            logger.info(f"  ✓ Successfully processed {name}")
        else:
            logger.error(f"  ✗ Failed to process {name}")

        return success

    async def scan_and_sync(self, ip_targets: List[str], concurrent: int = 50):
        """Scan network and sync printers to Snipe-IT"""
        if not self.initialize():
            logger.error("Initialization failed, aborting")
            return

        scanner = NetworkScanner(self.community, timeout=2, max_concurrent=concurrent)

        # Parse all IP targets
        all_ips = []
        for target in ip_targets:
            ips = scanner.parse_ip_range(target)
            all_ips.extend(ips)
            logger.debug(f"Target '{target}' expanded to {len(ips)} IP(s)")

        if not all_ips:
            logger.error("No valid IPs to scan")
            return

        logger.info(f"Total IPs to scan: {len(all_ips)}")

        printers = await scanner.scan_network(all_ips)

        if not printers:
            logger.warning("No printers found")
            return

        logger.info(f"\nSyncing {len(printers)} printer(s) to Snipe-IT...")

        success_count = 0
        failed_count = 0

        for printer in printers:
            if self.create_or_update_printer(printer):
                success_count += 1
            else:
                failed_count += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"Sync Complete!")
        logger.info(f"  Success: {success_count}")
        logger.info(f"  Failed: {failed_count}")
        logger.info(f"  Total: {len(printers)}")
        logger.info(f"{'='*60}")


async def async_main(args):
    """Async main function"""
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Read configuration
    if args.use_config:
        logger.info("Reading configuration from auth.txt...")
        config = ConfigReader.read_auth_config(args.auth_file)

        if not config['url'] or not config['token']:
            logger.error("Invalid configuration in auth.txt")
            sys.exit(1)

        url = config['url']
        token = config['token']
        community = config.get('community', 'public')
    else:
        # Use command line arguments
        if not args.url or not args.token:
            logger.error("--url and --token required when not using --use-config")
            sys.exit(1)
        url = args.url
        token = args.token
        community = args.community

    # Read printer IPs
    if args.use_printer_file:
        logger.info(f"Reading printer IPs from {args.printer_file}...")
        ip_targets = ConfigReader.read_printer_ips(args.printer_file)

        if not ip_targets:
            logger.error(f"No valid IPs found in {args.printer_file}")
            sys.exit(1)
    elif args.target:
        ip_targets = [args.target]
    else:
        logger.error("No IP targets specified. Use --target or --use-printer-file")
        sys.exit(1)

    # Run sync
    integrator = PrinterToSnipeIT(
        snipeit_url=url,
        api_token=token,
        community=community
    )

    await integrator.scan_and_sync(ip_targets, concurrent=args.concurrent)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Scan printers and sync to Snipe-IT (Config File Version)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration Files:

1. auth.txt (Required when using --use-config):
   url=http://192.168.0.126:8000/api/v1
   token=YOUR_API_TOKEN_HERE
   community=public

2. printers.txt (Required when using --use-printer-file):
   192.168.1.245
   192.168.1.246
   192.168.1.247
   192.168.1.248
   # Or use ranges/subnets:
   192.168.1.1-254
   192.168.2.0/24

Examples:
  # Use config files (EASIEST METHOD)
  %(prog)s --use-config --use-printer-file

  # Use custom config files
  %(prog)s --use-config --auth-file my_auth.txt --use-printer-file --printer-file my_printers.txt

  # Use command line (no config files)
  %(prog)s --target 192.168.1.0/24 --url http://snipeit.local/api/v1 --token YOUR_TOKEN
        """
    )

    # Config file options
    parser.add_argument('--use-config', action='store_true',
                       help='Read URL and token from auth.txt')
    parser.add_argument('--auth-file', default='auth.txt',
                       help='Path to auth config file (default: auth.txt)')
    parser.add_argument('--use-printer-file', action='store_true',
                       help='Read printer IPs from printers.txt')
    parser.add_argument('--printer-file', default='printers.txt',
                       help='Path to printer IP file (default: printers.txt)')

    # Command line options (alternative to config files)
    parser.add_argument('--target',
                       help='IP address, range, or subnet (if not using --use-printer-file)')
    parser.add_argument('--url',
                       help='Snipe-IT API URL (if not using --use-config)')
    parser.add_argument('--token',
                       help='Snipe-IT API token (if not using --use-config)')

    # Other options
    parser.add_argument('-c', '--community', default='public',
                       help='SNMP community string (default: public, or from auth.txt)')
    parser.add_argument('--concurrent', type=int, default=50,
                       help='Maximum concurrent scans (default: 50)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    asyncio.run(async_main(args))


if __name__ == '__main__':
    main()
