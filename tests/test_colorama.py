"""Quick test to verify colorama is working with the logger."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test colorama import
try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True, strip=False)
    print(f"✅ colorama imported successfully (version: {colorama.__version__})")
    print(f"   COLORAMA_AVAILABLE should be True")
except ImportError as e:
    print(f"❌ colorama import failed: {e}")
    sys.exit(1)

# Test logger colorama detection
from artemis.utils.logger import COLORAMA_AVAILABLE, get_logger

print(f"\nCOLORAMA_AVAILABLE in logger: {COLORAMA_AVAILABLE}")

if not COLORAMA_AVAILABLE:
    print("❌ Logger is not detecting colorama!")
    print("   This means colors won't work in console output.")
else:
    print("✅ Logger detected colorama - colors should work!")

# Test actual logger output
print("\n" + "="*60)
print("Testing logger output (should show colors in console):")
print("="*60)

logger = get_logger("test_colorama")
logger.debug("This is a DEBUG message (should be cyan)")
logger.info("This is an INFO message (should be green)")
logger.warning("This is a WARNING message (should be yellow)")
logger.error("This is an ERROR message (should be red)")
logger.critical("This is a CRITICAL message (should be bright red)")

print("\n" + "="*60)
print("If you see colors above, colorama is working!")
print("If not, check that you're running in a terminal that supports colors.")
print("="*60)

