import sys
from pathlib import Path

# Add project root to sys.path so "from backend.*" imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
