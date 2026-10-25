import argparse

from .targets.movies import check_movies
from .loader import load_config, load_state, save_state
from .targets.node_lts import check_node_lts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=["movies", "node_lts"])
    args = parser.parse_args()

    state = load_state()
    config = load_config()

    if args.target == "node_lts":
        check_node_lts(state, config["webhook_url"])
    else:
        check_movies(state, config)

    save_state(state)


if __name__ == "__main__":
    main()
