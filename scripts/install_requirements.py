"""Optional IPv4-only pip bootstrap for hosts with broken IPv6 routing."""
import runpy
import socket
import sys
from pathlib import Path

if __name__ == "__main__":
    # Process-local transport workaround; does not modify pip or system networking.
    import pip._vendor.urllib3.util.connection as connection
    connection.allowed_gai_family = lambda: socket.AF_INET
    sys.argv = ["pip", "install", "--disable-pip-version-check", "--no-input",
                "--index-url", "https://pypi.org/simple", "--timeout", "15",
                "--retries", "1", "-r", str(Path(__file__).resolve().parents[1]/"requirements.txt")]
    runpy.run_module("pip", run_name="__main__")
