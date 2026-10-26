import argparse

from .targets.movies import check_movies
from .loader import config_path, load_config
from .targets.node_lts import check_node_lts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=["movies", "node_lts"])
    args = parser.parse_args()

    config = load_config()

    if args.target == "node_lts":
        check_node_lts(config["webhook_url"])
    else:
        if not config["tmdb_token"]:
            raise SystemExit(f"Set tmdb_token in {config_path}")
        check_movies(config)


if __name__ == "__main__":
    main()
