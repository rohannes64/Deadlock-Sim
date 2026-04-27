from flask import Flask, render_template, request, jsonify
from collections import defaultdict
import random

app = Flask(__name__)

# --------------------------------------------------
# Core Deadlock Algorithms  |  
# R3E052B43, R3E052B44, R3E052B45
# -------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")




if __name__ == "__main__":
    app.run(debug=True, port=5000)
