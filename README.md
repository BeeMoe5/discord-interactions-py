# discord-interactions-py
A python port made from discord's node.js user installable application module. See https://github.com/discord/discord-interactions-js/tree/main

# Tests
While the `tests` directory is me testing and random stuff, you can use it as a reference how to this tool. However, I
will still provide examples below

# Setup
You'll need to 
# Usage
First, you'll want to set up the HTTP Middleware:
```python
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from discord_interactions import verify_incoming_requests


app = FastAPI()
app.add_middleware(BaseHTTPMiddleware, dispatch=verify_incoming_requests)
```
Whenever a request is made to the app, `verify_incoming_requests` is called and verifies that its coming from discord.
If its not from discord, an error response is returned to the requester.

Next, you'll want to add a GET endpoint to the app that discord will make requests to, and process the json:
```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from discord_interactions import verify_incoming_requests, process_commands
from discord_interactions.models import InteractionType


app = FastAPI()
app.add_middleware(BaseHTTPMiddleware, dispatch=verify_incoming_requests)


@app.get('/interactions')
async def interactions(request: Request):
    _json = await request.json()
    interaction_type = InteractionType(_json['type'])

    if interaction_type == InteractionType.PING:  # ping
        return {"type": InteractionType.PONG}  # pong
    
    if interaction_type == InteractionType.APPLICATION_COMMAND:  # command

        response = await process_commands(_json)
        return response
```
This does 2 things, but I'll start with the first part: The first if statement checks if discord is sending a ping to
your app, if so then it sends a "pong" response back to discord. Now, for the second if statement: This checks if
a slash command was used on your app, if so then it processes the command using the `process_commands` coroutine

Next, you'll want to start creating a slash command:
```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from discord_interactions import verify_incoming_requests, process_commands, command
from discord_interactions.models import InteractionType, ContentModel


app = FastAPI()
app.add_middleware(BaseHTTPMiddleware, dispatch=verify_incoming_requests)


@app.get('/interactions')
async def interactions(request: Request):
    _json = await request.json()
    interaction_type = InteractionType(_json['type'])

    if interaction_type == InteractionType.PING:  # ping
        return {"type": InteractionType.PONG}  # pong
    
    if interaction_type == InteractionType.APPLICATION_COMMAND:  # command

        response = await process_commands(_json)
        return response


@command(name='ping')
async def ping(interaction):
    """ping pong"""
    return ContentModel(content="Pong!")
```
The `@command` decorator adds the command internally, so `discord-interactions-py` handles registering and running the
command. `ContentModel` is a pydantic Model, so you can create responses using python objects without using json or 
dicts. if the decorator `name` keyword isn't provided, the function name is used instead. if there isn't a docstring
provided, then "No description" is the default.

If you want to register new commands to your app, use the `register_commands` coroutine:
```python
@command(name='register')
async def register(interaction):
    await register_commands()
    return ContentModel(content='Commands have been registered!')
```
Using `register_commands` registers and updates all commands to discord using the `@command` decorator
