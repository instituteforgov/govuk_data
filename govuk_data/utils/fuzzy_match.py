# !/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Callable, Hashable, Literal, Optional

import pandas as pd
from rapidfuzz import fuzz, process, utils


# Define fuzzy matching function
def fuzzy_match(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    column_left: Hashable,
    column_right: Hashable,
    score_cutoff: int = 90,
    limit: int = 1,
    clean_strings: bool = True,
    drop_na: bool = True,
    scorer: Callable = fuzz.WRatio,
    scorer_kwargs: dict[str, Any] = {},
) -> pd.DataFrame:
    '''
        Fuzzy match two dataframes.

            Parameters:
                - df_left: The base dataframe which we want to find matches
                for
                - df_right: The dataframe in which we want to look for matches
                to values in df_left
                - column_left, column_right: Columns on which to match
                - score_cutoff: A score below which any matches
                will be dropped
                - limit: The number of matches to find for each row
                in df_left
                - clean_strings: Whether to apply rapidfuzz's default_process
                processor, which converts strings to lowercase, removes
                non-alphanumeric characters and trims whitespace
                - drop_na: Whether to drop rows where no matches are found
                - scorer: The scorer to use for fuzzy matching
                - scorer_kwargs: Keyword arguments to pass to scorer

            Returns:
                - df_matches: A dataframe of matches with a MultiIndex
                with index names df_left_id and df_right_id, consisting of
                the ids from df_left and df_right, and columns match_string,
                match_score. Where df_left or df_right has a MultiIndex,
                the relevant index is a tuple

            Notes:
                - This adds matches as rows rather than columns, to ensure a
                tidy dataset
                - The maximum number of matches that can be returned is
                len(df_left) * limit
                - None, np.nan and pd.NA in column_left or column_right are
                considered not to match with anything
    '''
    # Create a series of matches
    # NB: Passing a series to process.extract() yields a series named column_left
    # where the index is the index of df_left and the values are lists of tuples,
    # of the form [(<value>, <score>, <index>), ...] - in this case the match
    # value from df_right, the match score and index of df_right. Where df_right
    # has a MultiIndex, the index is a tuple
    # Ref: https://stackoverflow.com/a/63725864/4659442
    series_matches = df_left[column_left].apply(
        lambda x: process.extract(
            x,
            df_right[column_right],
            limit=limit,
            score_cutoff=score_cutoff,
            processor=utils.default_process if clean_strings else None,
            scorer=scorer,
            **scorer_kwargs
        )
    )

    # Drop empty matches
    if drop_na:
        series_matches = series_matches[
            series_matches.apply(lambda x: len(x) > 0)
        ]

    # Convert matches to a dataframe in long form
    df_matches = series_matches.to_frame()
    df_matches.index.name = 'df_left_id'
    df_matches = df_matches.explode(column_left)

    # Convert match tuple to columns
    df_matches = pd.DataFrame(
        index=df_matches.index,
        data=df_matches[column_left].tolist(),
        columns=['match_string', 'match_score', 'df_right_id']
    )

    # Convert indexes to tuples where df_left and/or df_right have MultiIndexes
    # as otherwise any subsequent merging will fail
    # NB: This is done before adding df_right_id to the index, as otherwise
    # df_right_id would become part of df_left_id
    # NB: Flattening df_matches index is only needed where df_left has a
    # MultiIndex, as in the case where df_right has a MultiIndex the df_right
    # index will have been a single, named column in df_matches
    if df_left.index.nlevels > 1:
        df_matches.index = pd.MultiIndex.to_flat_index(df_matches.index)
        df_matches.index.name = 'df_left_id'

    # Add df_right id to index, meaning it will consist of df_left id and
    # df_right id
    # NB: This will be a unique index, as long as df_left and df_right have
    # unique indexes
    df_matches.set_index(['df_right_id'], append=True, inplace=True)

    return df_matches


# Define fuzzy merging function
def fuzzy_merge(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    column_left: Hashable,
    column_right: Hashable,
    score_cutoff: int = 90,
    limit: int = 1,
    clean_strings: bool = True,
    drop_na: bool = True,
    drop_cols: Literal[None, 'left', 'right', 'both', 'match'] = None,
    scorer: Callable = fuzz.WRatio,
    scorer_kwargs: dict[str, Any] = {},
    suffixes: tuple[Optional[str], Optional[str]] = ('_df_left', '_df_right'),
):
    '''
        Fuzzy merge two dataframes.

            Parameters:
                - df_left: The base dataframe which we want to merge with df_right
                - df_right: The dataframe in which we want to merge with df_left
                - column_left, column_right: Columns on which to match df_left
                and df_right
                - score_cutoff: A score below which any matches
                will be dropped
                - limit: The number of matches to find for each row
                in df_left
                - clean_strings: Whether to apply rapidfuzz's default_process
                processor, which converts strings to lowercase, removes
                non-alphanumeric characters and trims whitespace
                - drop_na: Whether to drop rows where no matches are found
                - drop_cols: Which columns to drop in the output dataframe.
                Behaviour is as follows:
                    - None: Drop match_string
                    - left: Drop columns from df_left and match_string
                    - right: Drop columns from df_right and match_string
                    - both: Drop columns from both df_left and df_right and
                    match_string
                    - match: Drop match_string, match_score
                Note that match_string is dropped in all cases as it's the same
                as column_right
                - scorer: The scorer to use for fuzzy matching
                - scorer_kwargs: Keyword arguments to pass to scorer
                - suffixes: Suffixes to add to columns from df_left and df_right

            Returns:
                - df_output: A dataframe of merged data with a MultiIndex
                with ids from df_left and df_right. Where df_left or
                df_right has a MultiIndex, the relevant index is a tuple.
                Columns differ depending on the value of drop_cols, as follows:
                    - None: match_score, columns from df_left and columns from
                    df_right
                    - left: match_score, columns from df_right
                    - right: match_score, columns from df_left
                    - both: match_score
                    - match: columns from df_left and columns from df_right

            Notes:
                - This adds matches as rows rather than columns, to ensure a
                tidy dataset
                - The merge carried out is a left merge, so all rows from
                df_left are retained
                - The maximum number of matches that can be returned is
                len(df_left) * limit
                - None, np.nan and pd.NA in column_left or column_right are
                considered not to match with anything
    '''

    # Fuzzy match datasets
    df_matches = fuzzy_match(
        df_left,
        df_right,
        column_left,
        column_right,
        score_cutoff=score_cutoff,
        limit=limit,
        clean_strings=clean_strings,
        drop_na=drop_na,
        scorer=scorer,
        scorer_kwargs=scorer_kwargs,
    )

    # Convert indexes to tuples where df_left and/or df_right have MultiIndexes
    # as otherwise any subsequent merging will fail
    # NB: We do this on copies of df_left and/or df_right, and use these in the
    # subsequent merge, so that we don't modify the original dataframes
    df_left_flat_index = df_left.copy()
    df_right_flat_index = df_right.copy()

    if df_left.index.nlevels > 1:
        df_left_flat_index.index = pd.MultiIndex.to_flat_index(df_left_flat_index.index)
        df_left_flat_index.index.name = 'df_left_id'
    if df_right.index.nlevels > 1:
        df_right_flat_index.index = pd.MultiIndex.to_flat_index(df_right_flat_index.index)

    # Merge data
    # NB: Where we refer to df_left_id and df_right_id this is possible because fuzzy_match()
    # applies this naming - suffixes is only used to set subsequent column naming
    # NB: We need to handle the case where there are no matches, as merging df_left_flat_index
    # and df_matches where df_matches is empty results in a dataframe featuring df_left_id
    # but not df_right_id, causing a second merge() operation to fail
    # NB: Where drop_na is True or all rows from df_left are matched, the output of the
    # first merge() operation will have a MultiIndex made up of the indexes of df_left and
    # df_right. Where there are some unmatched rows from df_left and drop_na is False,
    # the output, df_interim, will have a single-level index consisting of
    #   a. a tuple of the indexes of df_left and df_right where a match was found, and
    #   b. NaNs where no match was found
    # and df_left_id will have been added as a column
    # NB: Where we have a single-level index, we replace the index with a MultiIndex
    # in which NaNs - representing unmatched rows from df_left - are replaced with the
    # index of df_left and the index of df_right, before proceeding with the merge
    # NB: x.name accesses the index of the row
    if df_matches.empty:
        df_output = df_left_flat_index.merge(
            df_matches,
            how='inner',
            left_index=True,
            right_on='df_left_id',
        ).set_index('df_left_id')
        df_output = df_output.assign(df_right_id=[]).set_index('df_right_id', append=True)

        # Add suffix to all columns bar match_string, match_score
        # NB: We're not able to use the suffixes arg of merge() as the fact
        # there are no matches means the suffixes aren't used
        df_output.columns = [
            col + suffixes[0] if col not in ['match_string', 'match_score'] else col
            for col in df_output.columns
        ]

    elif drop_na or df_left_flat_index.index.isin(
        df_matches.index.get_level_values('df_left_id')
    ).all():
        df_output = df_left_flat_index.merge(
            df_matches,
            how='inner',
            left_index=True,
            right_on='df_left_id'
        ).merge(
            df_right_flat_index,
            how='left',
            left_on='df_right_id',
            right_index=True,
            suffixes=suffixes
        )
    else:
        df_interim = df_left_flat_index.merge(
            df_matches,
            how='outer',
            left_index=True,
            right_on='df_left_id'
        )

        df_interim.index = df_interim.apply(
            lambda x: (x['df_left_id'], float('NaN')) if pd.isnull(x.name) else x.name,
            axis=1,
        )

        df_interim.drop(columns=['df_left_id'], inplace=True)

        df_interim.index = pd.MultiIndex.from_tuples(
            df_interim.index,
            names=['df_left_id', 'df_right_id']
        )

        df_output = df_interim.merge(
            df_right_flat_index,
            how='left',
            left_on='df_right_id',
            right_index=True,
            suffixes=suffixes
        )

    # Drop match_string column
    df_output.drop(columns=['match_string'], inplace=True)

    # Move match_score column to be first column
    df_output = df_output[
        ['match_score'] + [col for col in df_output.columns if col != 'match_score']
    ]

    # Drop columns
    if drop_cols == 'left':
        df_output.drop(
            columns=[col for col in df_output.columns if col.endswith(suffixes[0])],
            inplace=True
        )
    elif drop_cols == 'right':
        df_output.drop(
            columns=[col for col in df_output.columns if col.endswith(suffixes[1])],
            inplace=True
        )
    elif drop_cols == 'both':
        df_output.drop(
            columns=[
                col for col in df_output.columns
                if col.endswith(suffixes[0]) or col.endswith(suffixes[1])
            ],
            inplace=True
        )
    elif drop_cols == 'match':
        df_output.drop(columns=['match_score'], inplace=True)
    elif drop_cols is not None:
        raise ValueError(
            f'Invalid value for drop_cols: {drop_cols}. '
            'Valid values are None, "left", "right", "both", "match".'
        )

    return df_output
