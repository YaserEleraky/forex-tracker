"""
main.py
نقطة الدخول الرئيسية للتطبيق (Entry Point).
"""

import sys
from cli.parser import main
from core.logger import logger

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
