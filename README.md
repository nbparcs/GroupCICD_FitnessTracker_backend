# GroupCICD_FitnessTracker_backend

A comprehensive fitness tracking application backend built with Django and Django REST Framework. This API powers a fitness tracking platform that helps users monitor their workouts, meals, steps, and overall health metrics.

## 🚀 Features
.

### 🔐 User Authentication
- JWT-based authentication system
- User registration with email verification
- Password reset functionality
- Secure token refresh mechanism

### 💪 Workouts Management
- Create and track workout sessions
- Log exercise types, duration, and intensity
- Track progress over time
- Set and achieve fitness goals

### 🍽️ Meals & Nutrition
- Log daily meals and snacks
- Track macronutrients and calories
- Save favorite meals for quick logging
- Set daily nutritional goals

### 👣 Steps & Activity
- Log daily step counts
- Track distance covered
- Set daily step goals
- View activity trends over time

## 🛠️ Technology Stack

### Backend
- Python 3.8+
- Django 5.2+
- Django REST Framework
- PostgreSQL
- JWT Authentication

### Development Tools
- Docker & Docker Compose
- GitHub Actions (CI/CD)
- Postman (API Testing)

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12+
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dearn1/FitnessTrackerApp_backend.git
   cd FitnessTrackerApp_backend
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with the following variables:
   ```
   SECRET_KEY=your-secret-key-here
   DB_HOST=postgres-host
   DB_USER=your-db-user
   DB_PASSWORD=your-db-password
   DB_NAME=your-db-name
   DB_PORT=your-db-port
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (admin)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## 📚 API Documentation

### Authentication
- `POST /api/auth/register/` - Register a new user
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/logout/` - Logout (invalidate token)

### Workouts
- `GET /api/workouts/` - List all workouts
- `POST /api/workouts/` - Create a new workout
- `GET /api/workouts/{id}/` - Get workout details
- `PUT /api/workouts/{id}/` - Update a workout
- `DELETE /api/workouts/{id}/` - Delete a workout

### Meals
- `GET /api/meals/` - List all meals
- `POST /api/meals/` - Log a new meal
- `GET /api/meals/{id}/` - Get meal details
- `PUT /api/meals/{id}/` - Update a meal
- `DELETE /api/meals/{id}/` - Delete a meal

### Steps
- `GET /api/steps/` - Get step count history
- `POST /api/steps/` - Log daily steps
- `GET /api/steps/summary/` - Get steps summary

## 🐳 Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Run database migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## 🧪 Testing

Run tests using:
```bash
python manage.py test
```

## 🔄 CI/CD

This project uses GitHub Actions for continuous integration and deployment to Azure-VM. The workflow includes:
- Running tests on push to main branch
- Running linting and code quality checks
- Automatic deployment to Azure-VM on successful tests
