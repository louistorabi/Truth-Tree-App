# Truth-Tree-App
This Application turns Arguments into truth trees.

//IN TERMINAL: 

First, start the python backend server:
-change directory to backend: cd C:\Users\louis\Downloads\Truth-Tree-App\logic-backend
-activate virtual environment: .\.venv\Scripts\Activate.ps1
*restarting backend: python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
**leave this terminal window open whilst using 
***site for testing if server works = http://192.168.50.131:8000/health

Then, start expo to load the app:
-change directory to logic-app: cd C:\Users\louis\Downloads\Truth-Tree-App\logic-app
-start expo with cache clear= npx expo start -c
