import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Base URL for Roblox Games API
ROBLOX_GAMES_API_BASE_URL = "https://games.roblox.com/v1/games"

# --- NEW: Route for the root URL ("/") ---
@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Roblox Game Likes Proxy! Use the /getGameLikes endpoint with a universeId. Example: /getGameLikes?universeId=1234567890"

# --- EXISTING: Route for /getGameLikes ---
@app.route('/getGameLikes', methods=['GET'])
def get_game_likes():
    # Get universeId from query parameters (e.g., /getGameLikes?universeId=12345)
    universe_id = request.args.get('universeId')

    if not universe_id:
        return jsonify({"error": "Missing 'universeId' query parameter."}), 400

    try:
        # Construct the full Roblox API URL
        # Note: The Roblox API often expects integers for universeIds, ensure conversion if needed
        roblox_api_url = f"{ROBLOX_GAMES_API_BASE_URL}?universeIds={int(universe_id)}"

        # Make a request to the Roblox API
        response = requests.get(roblox_api_url)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        data = response.json()

        # Parse the JSON response
        if data and "data" in data and len(data["data"]) > 0:
            game_info = data["data"][0]
            favorited_count = game_info.get("favoritedCount")
            if favorited_count is not None:
                return jsonify({"likes": favorited_count}), 200
            else:
                return jsonify({"error": "favoritedCount not found in Roblox API response."}), 500
        else:
            return jsonify({"error": "Game information not found or invalid response from Roblox API."}), 404

    except ValueError:
        # Added a specific error for non-integer universeId, as int() conversion would fail
        return jsonify({"error": "Invalid 'universeId' provided. Must be a number."}), 400
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from Roblox API: {e}")
        return jsonify({"error": f"Failed to connect to Roblox API: {str(e)}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

# This part tells Replit how to run your Flask app
if __name__ == '__main__':
    # Replit sets the PORT environment variable.
    # Flask needs to listen on 0.0.0.0 to be externally accessible.
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
