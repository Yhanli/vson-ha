"""Minimal VSON Smart cloud client (reversed from com.vson.smarthome 3.2) for WP8621N fish feeder.

CLI test: python api.py [--feed]  (reads VSON_USER/VSON_PASS from env or ./.vsonconfig)
"""
import base64
import aiohttp
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, modes

try:
    from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
except ImportError:  # cryptography < 43
    from cryptography.hazmat.primitives.ciphers.algorithms import TripleDES

BASE = "https://apis.myvsoncloud.com:16082/"
API = BASE + "vc-air-ws-1.0.2/api/air/"
IV = b"01234567"
KEY_DEV = "*|rX<xO7<6B}7PA])?dN8fgX}wOr'HQh"  # e0.b.e: device brand/model headers
KEY_USER = "cjm'|I-pE2[8=TM4[1PXRu,_xiE}j0X>px2_MqOSU=%;/HK<lB"  # e0.b.g: login name/pwd
# Static headers from commons/network/h.java (identical in every app install)
HEADERS = {"bh": "JmnuSXWflZY=", "md": "WP2810", "pid": "cup033", "ost": "2", "apt": "108",
           "apv": "3.2", "cm": "1", "mac": "S+T1TP5Nrak=", "uuid": "ScqUePab+h0=",
           "osv": "14", "language": "en", "timeZone": "GMT+00:00"}


def _cipher(key: str):
    # Java DESedeKeySpec uses first 24 key bytes
    return Cipher(TripleDES(key.encode()[:24]), modes.CBC(IV))


def encrypt(s: str, key: str = KEY_USER) -> str:
    p = padding.PKCS7(64).padder()
    data = p.update(s.encode()) + p.finalize()
    e = _cipher(key).encryptor()
    return base64.b64encode(e.update(data) + e.finalize()).decode()


class VsonError(Exception):
    pass


class VsonAuthError(VsonError):
    pass


class VsonClient:
    def __init__(self, session: aiohttp.ClientSession, account: str, password: str):
        self._s = session
        self._creds = (account.strip(), password.strip())  # app trims both (BaseActivity.getEditTextString)
        self.token: str | None = None

    async def _post(self, url: str, data: dict, retry: bool = True) -> dict | list | None:
        if self.token is None and "/m/login" not in url:
            await self.login()
        h = dict(HEADERS, mpb=encrypt("Google", KEY_DEV), mpm=encrypt("Pixel", KEY_DEV))
        if self.token:
            h["tk"] = encrypt(self.token, KEY_DEV)  # k.java: header tk = e0.b.e(tk)
        async with self._s.post(url, data=data, headers=h) as r:
            r.raise_for_status()
            j = await r.json(content_type=None)
        code = str(j.get("retCode", j.get("code")))
        if code == "1003" and retry:  # invalid/expired token -> re-login once
            self.token = None
            return await self._post(url, data, retry=False)
        if code != "0":  # server sends "0" (string) or 0
            raise VsonError(f"{url.rsplit('/', 1)[-1]}: {code} {j.get('result')}")
        return j.get("result")

    async def login(self) -> str:
        """Account is case-sensitive server-side; never lowercase it."""
        account, password = self._creds
        acct_type = "102" if "@" in account else "101"  # 101 phone, 102 email
        try:
            res = await self._post(BASE + "vc-airmas-ws-1.0.2/api/m/login",
                                   {"name": encrypt(account), "pwd": encrypt(password), "accountType": acct_type},
                                   retry=False)
        except VsonError as e:
            raise VsonAuthError(str(e)) from e
        self.token = res["tk"]
        return self.token

    async def homes(self) -> list:
        return (await self._post(API + "queryHomeList", {"page": "1"})).get("homeList", [])

    async def devices(self, home_id: str) -> list:
        return (await self._post(API + "queryEquipmentList", {"homeId": home_id, "page": 1}))["equipmentList"]

    async def feeders(self) -> list:
        """All WP8621N feeders (type 86221) across homes. ponytail: page 1 only; add paging if >1 page of devices."""
        return [d for h in await self.homes() for d in await self.devices(h["id"]) if d.get("type") == "86221"]

    async def status(self, mac: str) -> dict:
        return await self._post(API + "queryBleyHomepage", {"mac": mac})

    async def settings(self, dev_id: str) -> dict:
        return await self._post(API + "queryBleyEquipment", {"id": dev_id})

    async def feed(self, mac: str):
        return await self._post(API + "updateBleyFeed", {"mac": mac})


async def _main():
    import os, sys, json, getpass
    cfg = ".vsonconfig"  # in current dir
    if os.path.exists(cfg):  # KEY=value lines; env vars win
        for line in open(cfg, encoding="utf-8"):
            k, sep, v = line.partition("=")
            if sep and v.strip():
                os.environ.setdefault(k.strip(), v.strip())
    assert encrypt("test@example.com") == "t4TOv6OFpESvQgs7eFuN5H5OpQ+c3f/5"  # matches Java DESede output
    async with aiohttp.ClientSession() as s:
        c = VsonClient(s, os.environ.get("VSON_USER") or input("VSON account: "),
                       os.environ.get("VSON_PASS") or getpass.getpass("Password: "))
        for d in await c.feeders():
            print(json.dumps({k: d.get(k) for k in ("id", "mac", "name", "type")}))
            print("  status:", json.dumps(await c.status(d["mac"])))
            if "--feed" in sys.argv:
                print("  feed:", await c.feed(d["mac"]))


if __name__ == "__main__":
    import asyncio
    asyncio.run(_main())
