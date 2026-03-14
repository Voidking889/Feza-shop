# 1.install requirements
----pip install uvicorn FastApi uvicorn pydantic pydantic-settings sqlalchemy aiosqlite stripe pyjwt passlib[bcrypt] python-dotenv
# 2.Start the server
----python -m uvicorn app.main:app --port 8000 --reload