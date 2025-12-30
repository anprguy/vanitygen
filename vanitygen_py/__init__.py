# Bitcoin Vanity Address Generator Package
import sys

if sys.version_info < (3, 7):
    print("Error: Python 3.7 or higher is required.")
    sys.exit(1)

# Export main classes
from .hybrid_generator import HybridGenerator, COINCURVE_AVAILABLE
from .balance_checker import BalanceChecker
from .bitcoin_keys import BitcoinKey
from .crypto_utils import hash160, base58check_encode, bech32_encode

__all__ = [
    'HybridGenerator',
    'BalanceChecker', 
    'BitcoinKey',
    'hash160',
    'base58check_encode',
    'bech32_encode',
    'COINCURVE_AVAILABLE'
]
