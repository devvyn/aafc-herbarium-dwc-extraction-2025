
from __future__ import annotations
import boto3
import os
from .config import SETTINGS

_session = None
def session():
    global _session
    if _session is None:
        _session = boto3.session.Session(region_name=SETTINGS.region)
    return _session

def s3_client():
    return session().client("s3", endpoint_url=SETTINGS.endpoint_url or None)
