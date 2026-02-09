from api.index import app

if __name__ == '__main__':
    print("Starting US Market Analyst Dashboard...")
    print("URL: http://localhost:5000")
    app.run(debug=True, port=5000)
