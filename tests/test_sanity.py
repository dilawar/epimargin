__author__ = "Dilawar Singh"
__email__ = "dilawar.s.rajput@gmail.com"

# This is from ../README.md

import epimargin.plots as plt
import pandas as pd
from epimargin.utils import setup


def _setup():
    (data, figs) = setup()  # creates convenient directories
    plt.set_theme("minimal")
    return data, figs

def test_setup():
    _setup()

def test_example():

    from epimargin.etl import download_data
    from epimargin.smoothing import notched_smoothing

    data, figs = _setup()

    download_data(data, "districts.csv", "https://api.covid19india.org/csv/latest/")

    # load raw data
    daily_reports = (
        pd.read_csv(data / "districts.csv", parse_dates=["Date"])
        .rename(str.lower, axis=1)
        .set_index(["state", "district", "date"])
        .sort_index()
        .loc["Maharashtra", "Mumbai"]
    )
    daily_cases = daily_reports["confirmed"].diff().clip(lower=0).dropna()
    # smooth/notch-filter timeseries
    smoother = notched_smoothing(window=5)
    smoothed_cases = pd.Series(data=smoother(daily_cases), index=daily_cases.index)

    # plot raw and cleaned data
    beg = "December 15, 2020"
    end = "March 1, 2021"
    training_cases = smoothed_cases[beg:end]

    plt.scatter(
        daily_cases[beg:end].index,
        daily_cases[beg:end].values,
        color="black",
        s=5,
        alpha=0.5,
        label="raw case count data",
    )
    plt.plot(
        training_cases.index,
        training_cases.values,
        color="black",
        linewidth=2,
        label="notch-filtered, smoothed case count data",
    )
    plt.PlotDevice().l_title("case timeseries for Mumbai").axis_labels(
        x="date", y="daily cases"
    ).legend().adjust(bottom=0.15, left=0.15).format_xaxis().size(9.5, 6).save(
        figs / "fig_1.svg"
    )


def main():
    test_setup()
    test_example()


if __name__ == "__main__":
    main()
