# https://ta-lib.github.io/ta-lib-python/index.html
import pandas as pd
import numpy as np
from quantfreedom._typing import pdFrame, Optional, Array1d, Union


def testing_eval_is_below(
    want_to_evaluate: pdFrame,
    user_args: Optional[Union[list[int, float], int, float, Array1d]] = None,
    indicator_data: Optional[pdFrame] = None,
    df_prices: Optional[pdFrame] = None,
    cand_ohlc: Optional[str] = None,
) -> pdFrame:
    """eval_is_below _summary_

    _extended_summary_

    Parameters
    ----------
    want_to_evaluate : pdFrame
        I think of this like I want to evaluate if the thing i am sending like EMA is below the price or is below the indicator data which could be rsi. So it would be i want to evalute if the EMA is below the RSI.
    user_args : Optional[Union[list[int, float], int, float, Array1d]], optional
        _description_, by default None
    indicator_data : Optional[pdFrame], optional
        _description_, by default None
    df_prices : Optional[pdFrame], optional
        _description_, by default None
    cand_ohlc : Optional[str], optional
        _description_, by default None

    Returns
    -------
    pdFrame
    """
    if not isinstance(want_to_evaluate, pdFrame):
        raise ValueError("Data must be a dataframe with multindex")

    # want_to_evaluate_values = want_to_evaluate.values
    # pd_col_names = list(want_to_evaluate.columns.names) + [
    #     want_to_evaluate.columns.names[0].split("_")[0] + "_is_below"
    # ]
    # pd_multind_tuples = ()

    if isinstance(user_args, (list, Array1d)):
        eval_array = np.empty(
            (want_to_evaluate.shape[0], want_to_evaluate.shape[1] * len(user_args)), dtype=np.bool_
        )
        if not all(isinstance(x, (int, float, np.int_, np.float_)) for x in user_args):
            raise ValueError("user_args must be a list of ints or floats")
        eval_array_counter = 0
        for col in range(want_to_evaluate.shape[1]):
            temp_array = want_to_evaluate_values[:, col]
            for eval_col in range(user_args.size):
                eval_array[:, eval_array_counter] = np.where(
                    temp_array < user_args[eval_col], True, False
                )
                eval_array_counter += 1

                pd_multind_tuples = pd_multind_tuples + (
                    want_to_evaluate.columns[col] + (user_args[eval_col],),
                )

    elif isinstance(user_args, (int, float)):
        eval_array = np.where(want_to_evaluate_values < user_args, True, False)

        for col in range(want_to_evaluate.shape[1]):
            pd_multind_tuples = pd_multind_tuples + (
                want_to_evaluate.columns[col] + (user_args,),
            )

    elif isinstance(df_prices, pdFrame):
        symbols = list(want_to_evaluate.columns.levels[0])
        eval_array = np.empty_like(want_to_evaluate, dtype=np.bool_)
        if cand_ohlc == None or cand_ohlc.lower() not in (
            "open",
            "high",
            "low",
            "close",
        ):
            raise ValueError(
                "cand_ohlc must be open, high, low or close when sending price data"
            )
        price_values = getattr(df_prices, cand_ohlc).values
        if not all(isinstance(x, (np.int_, np.float_)) for x in price_values):
            raise ValueError("price data must be ints or floats")
        for col in range(want_to_evaluate.shape[1]):
            eval_array[:, col] = np.where(
                want_to_evaluate_values[:, col] < price_values, True, False
            )

            pd_multind_tuples = pd_multind_tuples + (
                want_to_evaluate.columns[col] + (cand_ohlc + "_price",),
            )

    elif isinstance(indicator_data, pdFrame):
        want_to_evaluate_name = want_to_evaluate.columns.names[-1].split("_")[
            1]
        indicator_data_name = indicator_data.columns.names[0].split("_")[0]

        pd_col_names = list(want_to_evaluate.columns.names) + [
            want_to_evaluate_name + "_is_below"
        ]

        want_to_evaluate_settings_tuple_list = want_to_evaluate.columns.to_list()

        eval_array = np.empty(
            (want_to_evaluate.shape[0], len(
                want_to_evaluate_settings_tuple_list)),
            dtype=np.bool_,
        )
        pd_multind_tuples = ()
        for count, value in enumerate(want_to_evaluate_settings_tuple_list):
            temp_evaluate_values = want_to_evaluate[value].values
            temp_indicator_values = indicator_data[value[0]].values.flatten()
            if not all(
                isinstance(x, (np.int_, np.float_)) for x in temp_evaluate_values
            ) and not all(isinstance(x, (np.int_, np.float_)) for x in temp_indicator_values):
                raise ValueError(
                    "want to eval or indicator data must be ints or floats")
            eval_array[:, count] = np.where(
                temp_evaluate_values < temp_indicator_values,
                True,
                False,
            )
            pd_multind_tuples = pd_multind_tuples + \
                (value + (indicator_data_name,),)

    else:
        raise ValueError(
            "something is wrong with what you sent please make sure the type of variable you are sending matches with the type required"
        )

    return pd.DataFrame(
        eval_array,
        index=want_to_evaluate.index,
        columns=pd.MultiIndex.from_tuples(
            tuples=list(pd_multind_tuples),
            names=pd_col_names,
        ),
    )