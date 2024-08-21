import os
import aiohttp
from .models import EmbedModel, ContentModel


_commands = []


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
