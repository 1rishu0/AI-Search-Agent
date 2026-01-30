# Here we are Implementing all of the Operations related to the web scraping into using the bright data service
# quote_plus allow us to turn a normal string into a string that we could include in a query parameter in our URL.

from dotenv import load_dotenv
import os
import requests
from urllib.parse import quote_plus
from snapshot_operations import download_snapshot, poll_snapshot_status

load_dotenv()

# this is the dataset_id of the snapshot of the brightdata for reddit because to go fetch data live we need to have proper fetched data which will come in snapshot to download
dataset_id = "aiewaifh_wfhe"

# we are going to create a reusable funtion that we can use any time we want to send a request to bright data , So we automatically could include the correct headers for out authentication.
def _make_api_request(url, **kwargs):
    api_key = os.getenv("BRIGHTDATA_API_KEY")

    # we need to set these headers because we need to set these headers to tell bearer data who we are.
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers, **kwargs)
        # what this means is we are going to raise and exception if we don't  get an okay status.
        response.raise_for_status()
        return response.json()
    # raise this exception if we have any networking exceptions
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None
    except Exception as e:
        print(f"Unknown error: {e}")
        return None


# we are going to write this function kind of dynamically because this will allow us to search any search engine that bright data supports so that we can reuse this function multiple times
def serp_search(query, engine="google"):
    if engine == "google":
        base_url = "https://www.google.com/search"
    elif engine == "bing":
        base_url = "https://www.bing.com/search"
    else:
        raise ValueError(f"Unknown engine {engine}")

    # This is where we are going to send the request and we are going to pass essentially the search URL that we want to search and get the data back from.
    url = "https://api.brightdata.com/request"

    # now we create payload which have zone that contain the name of the zone in brightdata website
    payload = {
        "zone": "ai_agent2",
        # quote_plus is going to take whatever the user typed in which is going to be our search string, it gonna turn it into a format that we can actually pass correctly in a query parameter for this url
        # brd_json to 1 is brightdata json enabled, so essentially we want our response back in json format.
        "url": f"{base_url}?q={quote_plus(query)}&brd_json=1",
        "format": "raw"
    }

    # now we are going to make request to our api with above payload
    full_response = _make_api_request(url, params=payload)
    if not full_response:
        return None

    extracted_data = {
        "knowledge": full_response.get("knowledge",{}),
        "organic": full_response.get("organic",[])
    }

    return extracted_data


# we are going to write a function that will allow us to download the snapshot, which is how we are going to get the data.
def _trigger_and_download_snapshot(trigger_url, params, data, operation_name="operation"):
    # we are going to make an API request to the brightdata then we are going to get the snapshot information and we are going to pull that snapshot until it's  ready and download it.
    trigger_result = _make_api_request(trigger_url, params=params, json=data)
    if not trigger_result:
        return None

    snapshot_id = trigger_result.get("snapshot_id")
    if not snapshot_id:
        return None

    # It is continually pull the snapshot until it eventually gets a result of true or false.
    if not poll_snapshot_status(snapshot_id):
        return None

    # we are going to download the snapshot with this snapshot id which will contain our scraped data
    raw_data = download_snapshot(snapshot_id)
    return raw_data


# So now this function should actually do is if we do reddit search, it should essentially trigger this scrape operation to start happening, then it will pull the snapshot, as soon as snapshot is ready, we are going to download the snapshot through _trigger_and_download_snapshot function and with that we get raw data and from raw data we take whatever data we need like title and url and append in parsed_data and return it
def reddit_search_api(keyword, date="All time", sort_by="Hot", num_of_posts=75):
    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"

    params = {
        "dataset_id": "aiewaifh_wfhe",
        "include_errors": "true",
        "type": "discover_new",
        # this indicates what type of kind of search we are doing essentially
        "discover_by": "keyword"
    }

    # next we are going to indicate the data we are searching for
    # there is dictionary inside the list , which mean we can send 100 or even thousand multiple strings asyncronously to the api
    data = [
        {
            "keyword": keyword,
            "date": date,
            "sort_by": sort_by,
            "num_of_posts": num_of_posts,
        }
    ]

    raw_data = _trigger_and_download_snapshot(trigger_url, params, data, operation_name="reddit")

    if not raw_data:
        return None

    # what I want to do is I want to take all of the data that was returned to us and I just want to get the information from this data that I care about.
    # that's because I don't want to pass all this unnecessary array data to my LLM when I start checking which hosts we actually want to download or when to get the information from.
    parsed_data = []
    for post in raw_data:
        parsed_post = {
            "title": post.get("title"),
            "url": post.get("url"),
        }
        parsed_data.append(parsed_post)

    return {"parsed_posts": parsed_data, "total_found": len(parsed_data)}

# In this function we are sending urls to the func and then trigger the url with inserting the parameter and data of each url and put all the relevant variable in the trigger_download_snapshot function for the retrieval of raw data which is basically the comments and take relevant information from each comment and add in the list and return it with its length.
def reddit_post_retrieval(urls, days_back=10, load_all_replies=False, comment_limit=""):
    if not urls:
        return None

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"

    # dataset_id here is different from the dataset_id at reddit_search_api function
    params = {
        "dataset_id": "sfgsgr_sgere",
        "include_errors": "true",
    }

    data = [
        {
            "url": url,
            "days_back": days_back,
            "load_all_replies": load_all_replies,
            "comment_limit": comment_limit,
        }
        for url in urls
    ]

    raw_data = _trigger_and_download_snapshot(trigger_url, params, data, operation_name="reddit comments")

    if not raw_data:
        return None

    parsed_comments = []

    for comment in raw_data:
        parsed_comment = {
            "comment_id": comment.get("comment_id"),
            "content": comment.get("comment"),
            "date": comment.get("date_posted"),
        }
        parsed_comments.append(parsed_comment)

    return {"comments": parsed_comments, "total_retrieved": len(parsed_comments)}