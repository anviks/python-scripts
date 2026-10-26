import colorsys
from io import BytesIO
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


def check_movies(config: Config):
    for movie in config["movies"]:
        if is_notified("movies", str(movie)):
            continue

        response = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie}/watch/providers",
            headers={"Authorization": f"Bearer {config['tmdb_token']}"},
        ).json()

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

        info = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie}",
            headers={"Authorization": f"Bearer {config['tmdb_token']}"},
        ).json()
        title = info["title"]
        poster_path = info["poster_path"]

        width = max(map(len, provider_names))
        table = ""
        row_count = ceil(len(provider_names) / 2)
        for i in range(row_count):
            a = provider_names[i]
            b = provider_names[i + row_count // 2]
            table += a + " " * (width - len(a) + 2) + b + "\n"

        poster_url = f"https://image.tmdb.org/t/p/original{poster_path}"
        r, g, b = dominant_color_from_url(poster_url)
        color = (r << 16) | (g << 8) | b

        payload = {
            "embeds": [
                {
                    "title": f"🎬  {title} is now available!",
                    "description": f"Available on **{len(provider_names)}** services\n```\n{table}\n```",
                    "color": color,
                    "image": {"url": poster_url},
                },
            ],
        }

        requests.post(config["webhook_url"], json=payload)
        mark_notified("movies", str(movie))
