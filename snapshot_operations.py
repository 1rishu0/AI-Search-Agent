import os
import time
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional


# Load environment variables from a .env file (e.g., BRIGHTDATA_API_KEY=your_key_here)
# This keeps sensitive credentials out of the source code.
load_dotenv()

def poll_snapshot_status(snapshot_id: str, max_attempts: int=60, delay: int=5) -> bool:
    """
    Polls the BrightData API to check the progess of a dataset snapshot.

    Args:
        snapshot_id: Unique ID of the snapshot returned by the dataset creation request.
        max_attempts: Maximum number of polling attempts before timing out (default: 60).
        delay: Seconds to wait between polling attempts (default: 5).

    Returns:
        True if snapshot is ready, False if failed or timeout occurred.
    """
    # Retrieve the API Key securely from environment variables
    api_key = os.getenv("BRIGHTDATA_API_KEY")

    # Endpoint to check the current status/progress of the snapshot
    progress_url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"

    # Authorization header using header token
    headers = {"Authorization": f"Bearer {api_key}"}

    # Loop up to max_attempts times to check status
    for attempt in range(max_attempts):
        try:
            print(
                f"⏳ Checking snapshot progress...(attempt {attempt+1}/{max_attempts})"
            )

            # Make GET request to progress endpoint
            response = requests.get(progress_url, headers=headers)
            response.raise_for_status() # Raises HTTPError for  bad responses (4xx/5xx)

            # Parse JSON response
            progress_data = response.json()
            status = progress_data.get("status")

            # Snapshot is fully processed and ready for download
            if status == "ready":
                print("✅ Snapshot Completed!")
                return True

            # Snapshot processing failed
            elif status == "failed":
                print("❌ Snapshot failed")
                return False

            # Snapshot is still being generated
            elif status == "running":
                print("🔄 Still processing...")
                time.sleep(delay)

            # Unexpected status value (API might have added new states)
            else:
                print(f"❓ Unknown Status: {status}")
                time.sleep(delay)

        # Handle network errors, invalid JSON, HTTP errors after raise_for_status, etc.
        except Exception as e:
            print(f"⚠️ Error checking progress: {e}")
            time.sleep(delay)

    # Reached max attempts without completion
    print("⏰ Timeout waiting for snapshot completion")
    return False

def download_snapshot(
        snapshot_id: str, format: str="json"
) -> Optional[List[Dict[Any, Any]]]:
    """
    Downloads the completed snapshot data from BrightData.

    Args:
        snapshot_id: Unique ID of the ready snapshot.
        format: Desired output format (e.g., "json", "csv"). Defaults to "json".

    Returns:
        Parsed data (usually a list of dictionaries for JSON) if successful,
        None if download fails.
    """
    # Retrieve API key from environment
    api_key = os.getenv("BRIGHTDATA_API_KEY")

    # Construct download URL with specified format
    download_url = (
        f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format={format}"
    )

    # Authorization header
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        print("📥 Downloading snapshot data...")

        # Perform GET request to download the snapshot
        response = requests.get(download_url, headers=headers)
        response.raise_for_status() #Raise exception for HTTP errors

        # for JSON format, parse directly into Python Objects
        data = response.json()

        # Provide feedback on number of items downloaded
        item_count = len(data) if isinstance(data, list) else 1
        print(f"🎉 Successfully downloaded {item_count} items")

        return data

    # Catch any error during download (network, auth, parsing, etc.)
    except Exception as e:
        print(f"❌ Error downloading snapshot: {e}")
        return None