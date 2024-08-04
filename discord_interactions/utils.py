import os
from fastapi import Request, HTTPException
import aiohttp
import nacl.signing
import nacl.utils
import nacl.encoding
import nacl.public
import nacl.exceptions
from nacl.signing import VerifyKey
from .models import EmbedModel, ContentModel

_commands = []


def verify_key(
    body: str, signature: str, timestamp, client_public_key: str
) -> dict | None:
    """
    Use this to verify that the incoming request is from discord

    Parameters
    ----------
    body : str
        The decoded request body
    signature : str
        The signature given from discord
    timestamp : str
        The timestamp given from discord
    client_public_key : str
        The public key of your discord app

    Returns
    -------
    dict
        If dict is returned, the request is not verified to be discord. You'll want to return this as a response
    None
        If None is returned, there is nothing to be worried about, and you can continue processing the request/response
    """
    verify_key = VerifyKey(bytes.fromhex(client_public_key))
    smessage = f"{timestamp}{body}".encode()

    try:
        verify_key.verify(smessage, bytes.fromhex(signature))
    except nacl.exceptions.BadSignatureError:
        return {"status": 401, "body": "Bad request signature"}


async def discord_request(endpoint: str, **request_options) -> aiohttp.ClientResponse:
    """
    Make a request to discord

    Parameters
    ----------
    endpoint : str
        The endpoint fragment of discord's API
    **request_options
        Any extra options you want to give to the request

    Returns
    -------
    aiohttp.ClientResponse
        The Response from discord
    """
    url = "https://discord.com/api/v10" + endpoint
    bot_token = os.getenv("APP_TOKEN")

    headers = {
        "Authorization": "Bot " + bot_token,
        "Content-Type": "application/json",
    }

    if request_options.get("headers") is not None:
        headers.update(request_options["headers"])

    async with aiohttp.ClientSession() as client:
        resp = await client.request(url=url, headers=headers, **request_options)
        resp.raise_for_status()
        return resp


async def register_commands() -> aiohttp.ClientResponse:
    """
    Bulk registers all commands that used the @command decorator. See https://discord.com/developers/docs/interactions/application-commands#bulk-overwrite-global-application-commands

    Returns
    -------
    aiohttp.ClientResponse
        The Response from discord
    """

    body = []

    for c in _commands:

        obj = {
            "name": c["name"],
            "type": 1,
            "description": c["command_func"].__doc__ or "No description",
            "integration_types": [1],
            "contexts": [0],
        }
        body.append(obj)
    app_id = os.getenv("app_id")
    resp = await discord_request(
        f"/applications/{app_id}/commands", method="PUT", json=body
    )
    return resp


async def process_commands(_json):
    name = _json["data"]["name"]

    command_ = next(filter(lambda obj: obj["name"] == name, _commands))

    if isinstance(command_, dict):
        response = command_["response"]
        return_type = command_["command_func"].__annotations__["return"]
        returned = await command_["command_func"](_json)

        if issubclass(return_type, EmbedModel):
            response["data"]["embeds"] = [returned.dict()]
        elif issubclass(return_type, ContentModel):
            response["data"].update(returned.dict())
        else:
            raise TypeError(f"{return_type} is not supported as a return type")

        return response


def command(name: str = None):
    def dec(command_func, *args, **kwargs):
        command_obj = {
            "name": name if name is not None else command_func.__name__,
            "command_func": command_func,
            "type": 4,
            "response": {
                "type": 4,
                "data": {
                    "flags": 64,
                },
            },
        }

        _commands.append(command_obj)

    return dec


async def verify_incoming_requests(request: Request, call_next):
    """
    HTTP Middleware for starlette/fastapi to verify the requests are coming from discord
    """

    client_key = os.getenv("APP_PUBKEY")
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    body = await request.body()

    is_valid_request = verify_key(
        body.decode("utf-8"), signature, timestamp, client_key
    )

    if is_valid_request is None:  # successfully verified
        resp = await call_next(request)
        return resp
    else:  # unsuccessfully unverified
        raise HTTPException(is_valid_request["status"], is_valid_request["body"])
