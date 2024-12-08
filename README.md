# Recipe Search Application

This is a Flask-based web application that allows users to search for recipes, view recipe details, manage their accounts, and view their search history.

## Features

- User registration and login
- Search for recipes using the Spoonacular API
- View detailed information about recipes
- Manage user account (change password, delete account)
- View and delete search history

## Prerequisites

- Python 3.12+
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Migrate
- python-dotenv
- spoonacular

## Setup

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/recipe-search-app.git
    cd recipe-search-app
    ```

2. **Create and activate a virtual environment:**

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**

    Create a `.env` file in the root directory of the project and add the following variables:

    ```env
    SECRET_KEY=your_secret_key
    SQLALCHEMY_DATABASE_URI=sqlite:///site.db  # or your preferred database URI
    SPOONACULAR_API_KEY=your_spoonacular_api_key
    ```

5. **Initialize the database:**

    ```sh
    flask db init
    flask db migrate -m "Initial migration."
    flask db upgrade
    ```

6. **Run the application:**

    ```sh
    flask run
    ```

    The application will be available at `http://127.0.0.1:5000`.

## Usage

- **Register:** Create a new user account.
- **Login:** Log in to your account.
- **Search Recipes:** Use the search bar to find recipes.
- **View Recipe Details:** Click on a recipe to view detailed information.
- **Dashboard:** Manage your account and view or delete your search history.

## API Endpoints

- **Register:** `POST /api/register`
- **Login:** `POST /api/login`
- **Search Recipes:** `POST /api/search`
- **Get Recipe Details:** `GET /api/search/<int:recipe_id>`
- **Get Search History:** `GET /api/search_history`
- **Delete Search History:** `DELETE /delete_search_history/<int:item_id>`

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.