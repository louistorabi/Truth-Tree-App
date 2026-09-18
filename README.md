##Truth Tree App

This application turns logical arguments into truth trees and generates truth tables.

## In Terminal

First, start the Python backend server:

    cd logic-backend
    .venv\Scripts\Activate.ps1
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Leave this terminal open while using the application.

To test that the backend is running, open:

    http://localhost:8000/health

Then, in a new terminal, start Expo:

    cd logic-app
    npx expo start -c

Open the application through Expo Go.

For physical-device testing, make sure the phone and computer are on the same network and that `EXPO_PUBLIC_API_BASE_URL` in `logic-app/.env` points to the computer's local IP address on port 8000.
