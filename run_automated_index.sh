#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Running automated index updater..."
cd "$SCRIPT_DIR"

# Run with different options
case "$1" in
    "once")
        python3 automated_index_updater.py --once
        ;;
    "update")
        python3 automated_index_updater.py --update-only
        ;;
    "discover")
        python3 automated_index_updater.py --discover-only
        ;;
    "continuous")
        python3 automated_index_updater.py
        ;;
    *)
        echo "Usage: $0 {once|update|discover|continuous}"
        echo "  once       - Run one complete cycle then exit"
        echo "  update     - Update existing repos only"
        echo "  discover   - Discover new repos only"
        echo "  continuous - Run continuously (default)"
        python3 automated_index_updater.py --once
        ;;
esac
