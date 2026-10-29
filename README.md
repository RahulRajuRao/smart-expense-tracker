
# Smart Expense Tracker 💰

A web-based personal finance management application built with
Python, Streamlit, SQLAlchemy, SQLite/PostgreSQL, Pandas, and Plotly.

## Features

- User registration and login
- Password hashing
- Income and expense tracking
- Category-based transaction history
- Monthly financial dashboard
- Monthly budget management
- Spending charts and budget warnings
- Transaction editing and deletion
- CSV export
- SQLite for local development
- PostgreSQL support for deployment
- Automated security unit tests

## Tech Stack

- Python
- Streamlit
- SQLAlchemy
- SQLite / PostgreSQL
- Pandas
- Plotly
- Pytest

## Project Structure

    smart-expense-tracker/
    ├── app.py
    ├── database.py
    ├── security.py
    ├── requirements.txt
    ├── .gitignore
    ├── README.md
    └── tests/
        └── test_security.py

## Installation

Install Python 3.11 or a compatible newer version.

Create and activate a virtual environment:

### Windows

    python -m venv .venv
    .venv\Scripts\activate

### macOS / Linux

    python3 -m venv .venv
    source .venv/bin/activate

Install dependencies:

    python -m pip install -r requirements.txt

Start the application:

    python -m streamlit run app.py

Open the local URL displayed in the terminal, usually
http://localhost:8501.

## Testing

    python -m pytest -q

## Database

The app uses a local SQLite database by default.
Set DATABASE_URL to a PostgreSQL connection string to use
a PostgreSQL database.

For production use, configure a persistent database and
review authentication, rate limiting, backups, and security.

## Deployment

Push the repository to GitHub and deploy app.py using
Streamlit Community Cloud.

Configure DATABASE_URL through the hosting platform's
secrets or environment-variable settings when using PostgreSQL.

Never commit passwords, database credentials, or private
financial records.

## License

MIT License
