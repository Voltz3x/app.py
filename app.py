import os
import time
from flask import Flask, request, jsonify
import requests
from cachetools import TTLCache # --- FIX: Import the time-based cach

app = Flask(__name__)

# --- FIX: Define our cache ---
# TTLCache stands for "Time To Live Cache"
# maxsize: The maximum number of universe IDs to store.
# ttl: Time To Live in seconds. We'll store the like count for 300 seconds (5 minutes)
#      before fetching a fresh copy from Roblox. This value is tunable.
like_cache = TTLCache(maxsize=128, ttl=300)

ROBLOX_GAMES_API_BASE_URL = "https://games.roblox.com/v1/games"

@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Roblox Game Likes Proxy! Use the /getGameLikes endpoint with a universeId. Example: /getGameLikes?universeId=1234567890"

@app.route('/getGameLikes', methods=['GET'])
def get_game_likes():
    universe_id = request.args.get('universeId')

    if not universe_id:
        return jsonify({"error": "Missing 'universeId' query parameter."}), 400

    # --- FIX: Check the cache first ---
    # Before making any API call, we check if we have a recent, valid result stored.
    # The TTLCache automatically handles checking if the entry has expired.
    if universe_id in like_cache:
        cached_likes = like_cache[universe_id]
        # Return the cached data immediately. This is extremely fast and makes no API call.
        return jsonify({"likes": cached_likes, "cached": True}), 200

    # --- If the data is not in the cache, we proceed to fetch it from Roblox ---
    try:
        roblox_api_url = f"{ROBLOX_GAMES_API_BASE_URL}?universeIds={int(universe_id)}"
        response = requests.get(roblox_api_url)
        response.raise_for_status()
        data = response.json()

        if data and "data" in data and len(data["data"]) > 0:
            game_info = data["data"][0]
            favorited_count = game_info.get("favoritedCount")
            if favorited_count is not None:
                # --- FIX: Store the successful result in the cache ---
                # Before returning the data, we save it for the next 5 minutes.
                like_cache[universe_id] = favorited_count
                return jsonify({"likes": favorited_count, "cached": False}), 200
            else:
                return jsonify({"error": "favoritedCount not found in Roblox API response (unexpected).", "api_response": data}), 500
        else:
            return jsonify({"error": "Game information not found or invalid response from Roblox API (data array empty/missing).", "api_response": data}), 404

    except ValueError:
        return jsonify({"error": "Invalid 'universeId' provided. Must be a number."}), 400
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from Roblox API: {e}")
        return jsonify({"error": f"Failed to connect to Roblox API: {str(e)}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
