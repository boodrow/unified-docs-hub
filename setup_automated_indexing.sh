#!/bin/bash

# Setup script for automated indexing
# For macOS, we'll use launchd instead of systemd

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_FILE="$HOME/Library/LaunchAgents/com.unified-docs-hub.indexer.plist"

echo "Setting up automated indexing for Unified Docs Hub..."

# Make the Python script executable
chmod +x "$SCRIPT_DIR/automated_index_updater.py"

# Create launchd plist file for macOS
cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.unified-docs-hub.indexer</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$SCRIPT_DIR/automated_index_updater.py</string>
        <string>--once</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    
    <key>StartCalendarInterval</key>
    <array>
        <!-- Run every day at 2 AM -->
        <dict>
            <key>Hour</key>
            <integer>2</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <!-- Run every day at 2 PM -->
        <dict>
            <key>Hour</key>
            <integer>14</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>
    
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/automated_indexing.log</string>
    
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/automated_indexing_error.log</string>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

echo "Created launchd plist at: $PLIST_FILE"

# Create a manual run script
cat > "$SCRIPT_DIR/run_automated_index.sh" <<'EOF'
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
EOF

chmod +x "$SCRIPT_DIR/run_automated_index.sh"

echo ""
echo "Setup complete! To enable automated indexing:"
echo ""
echo "1. Load the service:"
echo "   launchctl load $PLIST_FILE"
echo ""
echo "2. To run manually:"
echo "   $SCRIPT_DIR/run_automated_index.sh {once|update|discover|continuous}"
echo ""
echo "3. To check status:"
echo "   launchctl list | grep unified-docs-hub"
echo ""
echo "4. To stop the service:"
echo "   launchctl unload $PLIST_FILE"
echo ""
echo "The service will run twice daily (2 AM and 2 PM) when loaded."
