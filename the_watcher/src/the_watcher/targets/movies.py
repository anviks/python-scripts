import colorsys
from io import BytesIO
from itertools import zip_longest
from math import ceil
from PIL import Image
import requests

from ..loader import Config, is_notified, mark_notified


def theme_color(img) -> tuple[int, int, int]:
    q = img.quantize(colors=8)
    palette = q.getpalette()

    best, best_score = None, -1
    for count, index in q.getcolors():
        r, g, b = palette[index * 3 : index * 3 + 3]
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if v < 0.2 or v > 0.95:  # skip near-black and near-white
            continue
        score = count * s * s * v
        if score > best_score:
            best, best_score = (r, g, b), score

    return best or (128, 128, 128)  # fallback for grayscale images


def dominant_color_from_url(url: str) -> tuple[int, int, int]:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content)).convert("RGBA")
    img.thumbnail((150, 150))

    pixels = [p[:3] for p in img.getdata() if p[3] > 128]  # type: ignore
    rgb = Image.new("RGB", (len(pixels), 1))
    rgb.putdata(pixels)

    return theme_color(rgb)


def tmdb_get(path: str, token: str) -> dict:
    resp = requests.get(
        f"https://api.themoviedb.org/3{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def check_movies(config: Config):
    for movie in config["movies"]:
        if is_notified("movies", str(movie)):
            continue

        response = tmdb_get(f"/movie/{movie}/watch/providers", config["tmdb_token"])

        provider_names = sorted(
            {
                p["provider_name"]
                for val in response["results"].values()
                for kind, providers in val.items()
                if kind != "link"
                for p in providers
            }
        )

        if not provider_names:
            continue

        info = tmdb_get(f"/movie/{movie}", config["tmdb_token"])
        title = info["title"]
        poster_path = info["poster_path"]

        width = max(map(len, provider_names))
        half = ceil(len(provider_names) / 2)
        table = "\n".join(
            f"{a:<{width}}  {b:<{width}}"
            for a, b in zip_longest(
                provider_names[:half], provider_names[half:], fillvalue=""
            )
        )

        embed: dict = {
            "title": f"🎬  {title} is now available!",
            "description": f"Available on **{len(provider_names)}** services\n```\n{table}\n```",
        }
        if poster_path:
            r, g, b = dominant_color_from_url(
                f"https://image.tmdb.org/t/p/w342{poster_path}"
            )
            embed["color"] = (r << 16) | (g << 8) | b
            embed["image"] = {
                "url": f"https://image.tmdb.org/t/p/original{poster_path}"
            }

        requests.post(
            config["webhook_url"], json={"embeds": [embed]}, timeout=10
        ).raise_for_status()
        mark_notified("movies", str(movie))
