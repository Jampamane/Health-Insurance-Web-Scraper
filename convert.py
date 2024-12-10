import pandas as pd
import json
import time

def main():
    with open("output.json", "r") as file:
        json_string = file.read()

    data = json.loads(json_string)

    df = pd.DataFrame(data)
    df.to_csv("output.csv", index=False)


if __name__ == "__main__":
    main()