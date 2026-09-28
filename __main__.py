from pocketsmart.app import app
from pocketsmart.config import FLASK_PORT

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
