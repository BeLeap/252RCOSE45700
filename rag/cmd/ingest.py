import argparse
import glob

from ingest.load_files import load_files


def main():
    parser = argparse.ArgumentParser(prog="ingest")
    parser.add_argument("--path")

    args = parser.parse_args()

    target_files = glob.glob(args.path)
    print(f"{len(target_files)} files will be ingested!")

    load_files(target_files=target_files)


if __name__ == "__main__":
    main()
