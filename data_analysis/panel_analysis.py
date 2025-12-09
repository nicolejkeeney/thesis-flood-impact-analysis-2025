"""
panel_analysis.py

Panel regression analysis of precipitation anomalies on flood damages and affected populations.

Estimates linear and quadratic models with country-year, country-month,
admin region, and month-year fixed effects. Standard errors clustered by country.

95% confidence intervals are computed via bootstrap resampling of countries with
replacement, calculated at each precipitation anomaly.
"""

import os
import pyfixest as pf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pylatex as pl
from tqdm import tqdm

# Filepaths
DATA_DIR = "../data/"
FIGS_DIR = "../figures/"
PANEL_FILEPATH = f"{DATA_DIR}panel_dataset.csv"
PANEL_FIGS_DIR = f"{FIGS_DIR}panel_model/"

# Figure settings
FIG_DPI = 500
TITLE_FONTSIZE = 24
TICK_FONTSIZE = 20
LABEL_FONTSIZE = 23
plt.rcParams["font.family"] = "Georgia"

# Bootstrap and plotting settings
N_BOOT = (
    500  # Number of bootstrap iterations for CI (recommended: 500; use 5 for testing)
)
N_POINTS = 100  # Number of points for computing model predictions and CIs (controls plot smoothness)
X_RANGE = (-1, 5)  # Precipitation anomaly range in standard deviations


def plot_model_predictions(
    beta1_damages_linear,
    beta1_damages_quad,
    beta2_damages_quad,
    beta1_affected_linear,
    beta1_affected_quad,
    beta2_affected_quad,
    damages_linear_intercept,
    damages_quad_intercept,
    affected_linear_intercept,
    affected_quad_intercept,
    damages_linear_ci=None,  # Add these
    damages_quad_ci=None,
    affected_linear_ci=None,
    affected_quad_ci=None,
    x_range=X_RANGE,
    n_points=N_POINTS,
    savepath=None,
):
    """
    Plot linear and quadratic model predictions with confidence intervals.

    ... existing parameters ...
    damages_linear_ci : tuple of arrays, optional
        (lower, upper) bounds for damages linear model CI
    damages_quad_ci : tuple of arrays, optional
        (lower, upper) bounds for damages quadratic model CI
    affected_linear_ci : tuple of arrays, optional
        (lower, upper) bounds for affected linear model CI
    affected_quad_ci : tuple of arrays, optional
        (lower, upper) bounds for affected quadratic model CI
    """

    x_vals = np.linspace(x_range[0], x_range[1], n_points)

    # Calculate predictions (existing code)
    damages_linear = beta1_damages_linear * x_vals + damages_linear_intercept
    affected_linear = beta1_affected_linear * x_vals + affected_linear_intercept
    damages_quad = (
        beta1_damages_quad * x_vals
        + beta2_damages_quad * x_vals**2
        + damages_quad_intercept
    )
    affected_quad = (
        beta1_affected_quad * x_vals
        + beta2_affected_quad * x_vals**2
        + affected_quad_intercept
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    # Plot lines
    linear_color = "#0173B2"
    quad_color = "#CC3311"
    ax2.plot(x_vals, affected_linear, label="linear", color=linear_color, linewidth=2)
    ax2.plot(x_vals, affected_quad, label="quadratic", color=quad_color, linewidth=2)
    ax1.plot(x_vals, damages_linear, label="linear", color=linear_color, linewidth=2)
    ax1.plot(x_vals, damages_quad, label="quadratic", color=quad_color, linewidth=2)

    # Add shading if CIs provided
    alpha = 0.25  # How transparent the shading should be
    if damages_linear_ci is not None:
        ax1.fill_between(
            x_vals,
            damages_linear_ci[0],
            damages_linear_ci[1],
            alpha=alpha,
            color=linear_color,
            linewidth=0,
        )
    if damages_quad_ci is not None:
        ax1.fill_between(
            x_vals,
            damages_quad_ci[0],
            damages_quad_ci[1],
            alpha=alpha,
            color=quad_color,
            linewidth=0,
        )
    if affected_linear_ci is not None:
        ax2.fill_between(
            x_vals,
            affected_linear_ci[0],
            affected_linear_ci[1],
            alpha=alpha,
            color=linear_color,
            linewidth=0,
        )
    if affected_quad_ci is not None:
        ax2.fill_between(
            x_vals,
            affected_quad_ci[0],
            affected_quad_ci[1],
            alpha=alpha,
            color=quad_color,
            linewidth=0,
        )

    # Rest of plotting code unchanged
    ax2.set_ylabel("ln(total affected)", fontsize=LABEL_FONTSIZE)
    ax2.set_title("Total People Affected", fontsize=LABEL_FONTSIZE + 1)
    ax1.set_ylabel("ln(damages)", fontsize=LABEL_FONTSIZE)
    ax1.set_title("GDP-Standardized Damages", fontsize=LABEL_FONTSIZE + 1)

    for ax in ax1, ax2:
        ax.set_xlabel("precipitation anomaly", fontsize=LABEL_FONTSIZE)
        ax.legend(fontsize=LABEL_FONTSIZE)
        ax.tick_params(axis="both", labelsize=TICK_FONTSIZE)

    plt.suptitle(
        "Flood impacts versus precipitation\n(admin1-month panel regression)",
        fontsize=TITLE_FONTSIZE,
    )
    plt.tight_layout()

    if savepath:
        plt.savefig(savepath, dpi=FIG_DPI, bbox_inches="tight")
        print(f"Saved figure to {savepath}")


def quad_perc_change(beta1, beta2, x1=0, x2=1):
    """
    Calculate percent change for log-linear quadratic model.
    Percent Change = (exp(β₁(x₂ - x₁) + β₂(x₂² - x₁²)) - 1) × 100
    To compute a 1SD, 2SD, 3SD, etc change, use x1=0, x2=1,2,3, etc.
    x1=0 gives change relative to the mean

    Parameters
    ----------
    beta1 : float
        Linear coefficient
    beta2 : float
        Quadratic coefficient
    x1 : float, optional
        Initial value of independent variable
    x2 : float, optional
        Final value of independent variable

    Returns
    -------
    float
        Percent change
    """
    return (np.exp(beta1 * (x2 - x1) + beta2 * (x2**2 - x1**2)) - 1) * 100


def ols_linear(panel_df, verbose=True):
    """
    Fit log-linear OLS panel models for economic damages and people affected.

    Parameters
    ----------
    panel_df : pandas.DataFrame
        Panel dataset containing standardized damages and precipitation anomalies.
    verbose : bool, optional
        If True, print model summaries. Default is True.

    Returns
    -------
    damages_model : pyfixest model object
        Fitted model for economic damages.
    people_affected_model : pyfixest model object
        Fitted model for people affected.
    beta_damages : float
        Coefficient on precipitation anomaly from damages model.
    beta_affected : float
        Coefficient on precipitation anomaly from people affected model.
    """

    # Economic damages (GDP-standardized)
    damages_model = pf.feols(
        f"ln_damages_gdp_standardized ~ precip_std_anom | `country-yr` + `country-mon` + adm1_code + `mon-yr`",
        data=panel_df,
        vcov={"CRV1": "country"},
    )

    # Total people affected (normalized)
    people_affected_model = pf.feols(
        f"ln_total_affected_normalized ~ precip_std_anom | `country-yr` + `country-mon` + adm1_code + `mon-yr`",
        data=panel_df,
        vcov={"CRV1": "country"},
    )

    # Extract coefficients from the fitted model
    beta_damages = damages_model.coef().loc["precip_std_anom"]
    beta_affected = people_affected_model.coef().loc["precip_std_anom"]

    # Print results to console
    if verbose:
        print(
            "OLS log-linear model results for Total Damages\n======================================"
        )
        print(damages_model.summary())
        print(
            "OLS log-linear model results for Total People Affected\n======================================"
        )
        print(people_affected_model.summary())

    return damages_model, people_affected_model, beta_damages, beta_affected


def log_linear_perc_change(beta, x):
    """
    Compute percent change from a log-linear model.
    x is the number of standard deviations

    Parameters
    ----------
    beta : float or array-like
        Coefficient from the log-linear regression.
    x : float or array-like
        Independent variable value(s).

    Returns
    -------
    float or array-like
        Percent change corresponding to `x`.
    """
    return (np.exp(x * beta) - 1) * 100


def ols_quad(panel_df, verbose=True):
    """
    Fit log-quadratic OLS models for damages and people affected.

    Parameters
    ----------
    panel_df : pandas.DataFrame
        Panel dataset containing standardized damages and precipitation anomalies.
    verbose : bool, optional
        If True, print model summaries. Default is True.

    Returns
    -------
    damages_model_quad : pyfixest model object
        Fitted model for economic damages.
    people_affected_model_quad : pyfixest model object
        Fitted model for people affected.
    beta1_damages_quad : float
        Linear coefficient for damages.
    beta2_damages_quad : float
        Quadratic coefficient for damages.
    beta1_affected_quad : float
        Linear coefficient for people affected.
    beta2_affected_quad : float
        Quadratic coefficient for people affected.
    """

    # Economic damages (GDP-standardized)
    damages_model_quad = pf.feols(
        f"ln_damages_gdp_standardized ~ poly(precip_std_anom, 2, raw=True) | `country-yr` + `country-mon` + adm1_code + `mon-yr`",
        data=panel_df,
        vcov={"CRV1": "country"},
    )

    # Total people affected (normalized)
    people_affected_model_quad = pf.feols(
        f"ln_total_affected_normalized ~ poly(precip_std_anom, 2, raw=True) | `country-yr` + `country-mon` + adm1_code + `mon-yr`",
        data=panel_df,
        vcov={"CRV1": "country"},
    )

    # Print results to console
    if verbose:
        print(
            "OLS log-quadratic model results for Total Damages\n======================================"
        )
        print(damages_model_quad.summary())
        print(
            "OLS log-quadratic model results for Total People Affected\n======================================"
        )
        print(people_affected_model_quad.summary())

    # Extract coefficients from the fitted quadratic models
    beta1_damages_quad = damages_model_quad.coef().loc[
        "poly(precip_std_anom, 2, raw=True)[0]"
    ]  # linear term
    beta2_damages_quad = damages_model_quad.coef().loc[
        "poly(precip_std_anom, 2, raw=True)[1]"
    ]  # quadratic term
    beta1_affected_quad = people_affected_model_quad.coef().loc[
        "poly(precip_std_anom, 2, raw=True)[0]"
    ]  # linear term
    beta2_affected_quad = people_affected_model_quad.coef().loc[
        "poly(precip_std_anom, 2, raw=True)[1]"
    ]  # quadratic term

    return (
        damages_model_quad,
        people_affected_model_quad,
        beta1_damages_quad,
        beta2_damages_quad,
        beta1_affected_quad,
        beta2_affected_quad,
    )


def print_perc_change_formatted(
    percent_change_damages, percent_change_affected, sd_num=1
):
    """
    Print percent changes from a panel model in a formatted style.

    Parameters
    ----------
    percent_change_damages : float
        Percent change in GDP-standardized damages.
    percent_change_affected : float
        Percent change in normalized total people affected.
    sd_num : int, optional
        Number of standard deviations for the precipitation anomaly (default is 1).
    """
    print(
        f"\nAverage effect of a {sd_num}-SD precipitation anomaly on the impact\n================================"
    )
    print(f"Percent change in GDP-standardized damages: {percent_change_damages:.1f}%")
    print(
        f"Percent change in normalized total people affected: {percent_change_affected:.1f}%"
    )


def make_pdf(tab, file):
    """
    Create a PDF from a LaTeX table string.

    Parameters
    ----------
    tab : str
        LaTeX table string to render.
    file : str
        Output PDF filename without extension.

    Returns
    -------
    None
        Generates PDF file at specified path.
    """
    doc = pl.Document()
    doc.packages.append(pl.Package("booktabs"))
    doc.packages.append(pl.Package("threeparttable"))
    doc.packages.append(pl.Package("makecell"))

    with (
        doc.create(pl.Section("Panel Regression Results")),
        doc.create(pl.Table(position="htbp")) as table,
    ):
        table.append(pl.NoEscape(tab))

    doc.generate_pdf(file, clean_tex=True)
    print(f"Saved LaTeX file to {file}.pdf")


def bootstrap_predictions(
    panel_df, model_func, x_vals, n_boot=1000, cluster_var="country"
):
    """
    Bootstrap predictions across x values.

    Parameters
    ----------
    panel_df : pandas.DataFrame
        Panel dataset
    model_func : callable
        Model fitting function
    x_vals : array-like
        X values for predictions
    n_boot : int
        Number of bootstrap iterations
    cluster_var : str
        Clustering variable

    Returns
    -------
    tuple
        (damages_preds, affected_preds) each shape (n_boot, len(x_vals))
    """
    unique_clusters = panel_df[cluster_var].unique()
    damages_preds = []
    affected_preds = []

    for i in tqdm(range(n_boot), desc="Bootstrapping"):
        boot_clusters = np.random.choice(
            unique_clusters, size=len(unique_clusters), replace=True
        )
        boot_df = panel_df[panel_df[cluster_var].isin(boot_clusters)]

        coeffs = model_func(boot_df, verbose=False)[2:]

        if model_func is ols_linear:  # Linear
            beta_dam, beta_aff = coeffs
            dam_pred = beta_dam * x_vals
            aff_pred = beta_aff * x_vals
        elif model_func is ols_quad:  # Quadratic
            beta1_dam, beta2_dam, beta1_aff, beta2_aff = coeffs
            dam_pred = beta1_dam * x_vals + beta2_dam * x_vals**2
            aff_pred = beta1_aff * x_vals + beta2_aff * x_vals**2
        else:
            raise ValueError(f"Unknown model function: {model_func}")

        damages_preds.append(dam_pred)
        affected_preds.append(aff_pred)

    return np.array(damages_preds), np.array(affected_preds)


def main():
    # Make output dir if it doesn't already exist
    os.makedirs(PANEL_FIGS_DIR, exist_ok=True)

    # Read in data
    panel_df = pd.read_csv(PANEL_FILEPATH)
    panel_df.rename(columns={"adm0_name": "country"}, inplace=True)

    ## LINEAR MODEL

    # Build model & compute betas for each impact var
    (
        damages_linear_model,
        affected_linear_model,
        beta_damages_linear,
        beta_affected_linear,
    ) = ols_linear(panel_df, verbose=True)

    # Percent change of x standard deviation(s)
    x = 1  # Number of standard deviations
    perc_change_damages_linear = log_linear_perc_change(beta_damages_linear, x=x)
    perc_change_affected_linear = log_linear_perc_change(beta_affected_linear, x=x)
    print_perc_change_formatted(
        perc_change_damages_linear, perc_change_affected_linear, sd_num=x
    )

    ## QUADRATIC MODEL

    # Build model & compute betas for each impact var
    (
        damages_quad_model,
        affected_quad_model,
        beta1_damages_quad,
        beta2_damages_quad,
        beta1_affected_quad,
        beta2_affected_quad,
    ) = ols_quad(panel_df, verbose=True)

    # Percent change of x standard deviation(s)
    x = 1  # Number of standard deviations
    perc_change_damages_quad = quad_perc_change(
        beta1_damages_quad, beta2_damages_quad, x1=0, x2=x
    )
    perc_change_affected_quad = quad_perc_change(
        beta1_affected_quad, beta2_affected_quad, x1=0, x2=x
    )
    print_perc_change_formatted(
        perc_change_damages_quad, perc_change_affected_quad, sd_num=x
    )

    ## COMPUTE BOOTSTRAP CONFIDENCE INTERVALS

    # Compute bootstrapped predictions across x values by resampling countries
    # i.e. compute damages for precip anom x_val_i for a subset of countries
    x_vals = np.linspace(X_RANGE[0], X_RANGE[1], N_POINTS)
    dam_linear_boot, aff_linear_boot = bootstrap_predictions(
        panel_df, ols_linear, x_vals, n_boot=N_BOOT
    )
    dam_quad_boot, aff_quad_boot = bootstrap_predictions(
        panel_df, ols_quad, x_vals, n_boot=N_BOOT
    )

    # Calculate 95th perc CIs
    damages_linear_ci = (
        np.percentile(dam_linear_boot, 2.5, axis=0),
        np.percentile(dam_linear_boot, 97.5, axis=0),
    )
    damages_quad_ci = (
        np.percentile(dam_quad_boot, 2.5, axis=0),
        np.percentile(dam_quad_boot, 97.5, axis=0),
    )
    affected_linear_ci = (
        np.percentile(aff_linear_boot, 2.5, axis=0),
        np.percentile(aff_linear_boot, 97.5, axis=0),
    )
    affected_quad_ci = (
        np.percentile(aff_quad_boot, 2.5, axis=0),
        np.percentile(aff_quad_boot, 97.5, axis=0),
    )

    ## MAKE FIGURES

    # Make table
    labels = {
        "ln_damages_gdp_standardized": "Damages",
        "ln_total_affected_normalized": "People Affected",
        "poly(precip_std_anom, 2, raw=True)[0]": r"$\beta 1$",
        "poly(precip_std_anom, 2, raw=True)[1]": r"$\beta 2$",
        "precip_std_anom": r"$\beta$",
        # "f2": "Year",
    }

    tab = pf.etable(
        [
            damages_linear_model,
            affected_linear_model,
            damages_quad_model,
            affected_quad_model,
        ],
        labels=labels,
        model_heads=["Linear", "Linear", "Quadratic", "Quadratic"],
        head_order="hd",
        type="tex",
        # signif_code=[0.001],
        # notes=mynotes,
        show_fe=False,
        show_se_type=True,
    )

    # Compile latex to pdf & display a button with the hyperlink to the pdf
    make_pdf(tab, f"{PANEL_FIGS_DIR}panel_model_stats")

    # # Capture the fixed effects in a single intercept value
    # damages_mean = panel_df["ln_damages_gdp_standardized"].mean()
    # affected_mean = panel_df["ln_total_affected_normalized"].mean()
    # x_mean = panel_df["precip_std_anom"].mean()

    # # Calculate linear intercepts
    # linear_damages_intercept = damages_mean - beta_damages_linear * x_mean
    # linear_affected_intercept = affected_mean - beta_affected_linear * x_mean
    # print(linear_affected_intercept)
    # print(linear_damages_intercept)

    # Make lineplots
    plot_model_predictions(
        beta1_damages_linear=beta_damages_linear,
        beta1_damages_quad=beta1_damages_quad,
        beta2_damages_quad=beta2_damages_quad,
        beta1_affected_linear=beta_affected_linear,
        beta1_affected_quad=beta1_affected_quad,
        beta2_affected_quad=beta2_affected_quad,
        damages_linear_intercept=0,
        damages_quad_intercept=0,
        affected_linear_intercept=0,
        affected_quad_intercept=0,
        damages_linear_ci=damages_linear_ci,
        damages_quad_ci=damages_quad_ci,
        affected_linear_ci=affected_linear_ci,
        affected_quad_ci=affected_quad_ci,
        savepath=f"{PANEL_FIGS_DIR}ols_linear_quad_regression.png",
    )


if __name__ == "__main__":
    main()
