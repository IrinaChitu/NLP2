import os
import pandas as pd
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42


def split_dataset(datasetPath, destinationPath, verbose=False):
    dataset = pd.read_csv(datasetPath)
    columns = dataset.columns
    dataset = dataset.to_numpy()

    for file in ["train.csv", "test.csv", "val.csv"]:
        assert file not in os.listdir(
            destinationPath
        ), f"There is already a `{file}` file at the path `{destinationPath}`"

    X_train, X_test, _, _ = train_test_split(
        dataset, dataset[:, 1], test_size=0.2, shuffle=True, random_state=RANDOM_STATE
    )
    X_train, X_val, _, _ = train_test_split(
        X_train, X_train[:, 1], test_size=0.25, shuffle=True, random_state=RANDOM_STATE
    )

    for data, name in zip(
        [X_train, X_test, X_val], ["train.csv", "test.csv", "val.csv"]
    ):
        dataframe = pd.DataFrame(data, columns=columns)
        dataframe.to_csv(os.path.join(destinationPath, name), index=False)

    if verbose:
        print("train shape: {}".format(X_train.shape))
        print("test shape:  {}".format(X_test.shape))
        print("val shape:   {}".format(X_val.shape))
