import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- CHANGE THIS LINE ---
# Base URL for Roblox Games API to get favoritedCount
ROBLOX_GAMES_API_BASE_URL = "https://games.roblox.com/v1/games" # <-- THIS IS THE CORRECT ENDPOINT

# --- The rest of your app.py remains the same ---
@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Roblox Game Likes Proxy! Use the /getGameLikes endpoint with a universeId. Example: /getGameLikes?universeId=1234567890"

@app.route('/getGameLikes', methods=['GET'])
def get_game_likes():
    universe_id = request.args.get('universeId')

    if not universe_id:
        return jsonify({"error": "Missing 'universeId' query parameter."}), 400

    try:
        # Note: The endpoint itself expects 'universeIds', and the parameter should match.
        # So the URL will be: https://games.roblox.com/v1/games?universeIds=12345
        roblox_api_url = f"{ROBLOX_GAMES_API_BASE_URL}?universeIds={int(universe_id)}"

        response = requests.get(roblox_api_url)
        response.raise_for_status()

        data = response.json()

        if data and "data" in data and len(data["data"]) > 0:
            game_info = data["data"][0]
            # --- CHANGE THIS LINE ---
            # Now we correctly get 'favoritedCount' from this endpoint's response
            favorited_count = game_info.get("favoritedCount")
            if favorited_count is not None:
                return jsonify({"likes": favorited_count}), 200
            else:
                # This error should now be rare if the ID is valid
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
