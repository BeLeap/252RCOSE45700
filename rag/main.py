import argparse

from cmd.ingest import ingest

def main():
    print("Hello from rag!")

    parser = argparse.ArgumentParser(prog="rag")
    parser.add_argument("subcmd")

    args = parser.parse_args()

    if args.subcmd == "ingest":
        ingest()


if __name__ == "__main__":
    main()
