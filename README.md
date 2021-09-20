Minimal database writer API built on Python with FastAPI and SQLObject.

See the blog post at https://vxlabs.com/ "Developer experience setting up a minimal API in Go, C# and Python" (should be published before the end of October)

See you,
https://charlbotha.com/

## quickstart

Create database:

``` shell
sudo su postgres
psql < drop_and_create_db.sql
```

Install dependencies, start the dev server:

``` shell
poetry install
poetry run uvicorn main:app --reload
```
