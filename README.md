# REST

Your normal REST API coding activity

# Requirements
- Python 3.5

## Setup
Install `virtualenv` if you don't have one already

``` 
$ pip install virtualenv
```

Go to the project folder and setup your virtualenv

``` 
$ cd path/to/dubai/
$ virtualenv venv
$ source virtualenv/scripts/activate
```

Install the Python dependencies

``` 
$ pip install -r requirements.txt
```

Set up environmental variables

```
$ touch .env
```

i.e.

```
SECRET_KEY=<your_secret_key>
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=potus@whitehouse.gov
EMAIL_HOST_PASSWORD=donaldtrump
EMAIL_PORT=587
```

Migrate the database

``` 
$ python manage.py migrate
```

Start the server

``` 
$ python manage.py runserver
```

Go to `http://localhost:8000` and start surfing!

## Setup OAuth2

You need to set up an OAuth2 application first. You can do so by going to `http://localhost:8000/o/applications`. Be sure to set client type to **public** and grant type to **password-based**. After creating an application, be sure to save the **client ID** and **client secret** somewhere safe.

## Usage

Here are the endpoints. Use any method (`curl`, `Postman`, etc.) you like to access these.

1. **POST** `/api/register/`
    - Registers a new user account
    - Params: `email`, `password`, `first_name` (optional), `last_name` (optional)
    - Returns the registered user and sends a verification e-mail containing the activation link to the user's e-mail
    - **Note:** Copy the verification key found in the activation link, and send a POST request to `#2` with the token as the parameter
2. **POST** `/api/verify-email/`
    - Activates the user account
    - Params: `key` (verification token)
    - Returns the user
3. **POST**`/api/login/`
    - Logins the user 
    - Params: `username`, `password`, `grant_type`, `client_id`
    - Returns the OAuth2 bearer token which you can use to access `/api/users/`, `/api/change-password/`, and `/api/profile/`
    - **Note:** `grant_type` must be `password`, `client_id` must be the client ID of your application. The data must be also sent and encoded as `x-www-url-form urlencoded`.
4. **GET** `/api/users/`
    - Lists all the users
    - Returns all the users. If a valid token is not provided, fields like `email` and `last_name` will be omitted.
5. **POST** `/api/change-password/`
    - Changes the user's password
    - Params: `old_password` and `new_password`
    - Returns `OK` is successful
5. `/api/profile/`
    - Views and updates the user's profile
    - **GET**
        - Returns the logged-in user's profile
    - **PUT** or **PATCH**
        - Params: `email`, `first_name`, `last_name`
        - Returns logged-in user's new profile

## Testing

Run the tests command below

``` 
$ python manage.py test
```