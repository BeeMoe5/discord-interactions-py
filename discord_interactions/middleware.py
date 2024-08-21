import os
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import nacl.signing
import nacl.utils
import nacl.encoding
import nacl.public
import nacl.exceptions
from nacl.signing import VerifyKey


class VerifyIncomingRequestsMiddleware(BaseHTTPMiddleware):
    """
    HTTP Middleware for starlette/fastapi to verify the requests are coming from discord
    """

    async def dispatch(self, request: Request, call_next):
        """
        HTTP Middleware for starlette/fastapi to verify the requests are coming from discord
        """

        public_key = os.getenv("APP_PUBKEY")
        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")
        body = await request.body()

        is_valid = self.verify_key(
            body.decode("utf-8"), signature, timestamp, public_key
        )

        if is_valid is None:  # successfully verified
            response = await call_next(request)
            return response
        else:  # unsuccessfully unverified
            raise HTTPException(is_valid["status"], is_valid["body"])

    def verify_key(
        self, body: str, signature: str, timestamp, client_public_key: str
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
