import argparse
import glob

def main():
    parser = argparse.ArgumentParser(prog="ingest")
    parser.add_argument("--path")

    args = parser.parse_args()

    target_files = glob.glob(args.path)
    print(f"{len(target_files)} files will be ingested!")

if __name__ == "__main__":
    main()

