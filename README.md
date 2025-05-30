# Weather App

A Django-based weather application that allows users to check weather conditions for cities worldwide, save favorite cities, and track search history.

## Features

- User authentication (signup, login, logout)
- Weather search for any city
- Save favorite cities
- View search history
- User profiles
- Responsive design

## Prerequisites

- Python 3.x
- Django
- OpenWeatherMap API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/weather-app.git
cd weather-app
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root and add:
```
WEATHER_API_KEY=your_api_key_here
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## Usage

1. Register a new account or login
2. Search for a city to see its current weather
3. Add cities to your favorites
4. View your search history and profile

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 