from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

def main() -> None:
    print("Starting Web API")
    app.run(debug=True)

if __name__ == "__main__":
    main()