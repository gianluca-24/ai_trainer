from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    # Run on all network interfaces so you can use your phone
    app.run(host="0.0.0.0", port=5050, debug=True)
