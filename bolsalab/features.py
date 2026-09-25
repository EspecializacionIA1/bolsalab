"""Feature engineering y construcción de los datasets de entrenamiento.



"""


def build_profile_dataset() -> None:
    raise NotImplementedError


def build_market_dataset() -> None:
    raise NotImplementedError


def main() -> None:
    build_profile_dataset()
    build_market_dataset()


if __name__ == "__main__":
    main()
