def standardise_mos_puss_post_name(
    post_name: str
) -> str:
    '''
    Standardise different MoS, PUSS post name formats

    Parameters
        - post_name: The post name to be standardised

    Returns
        - post_name: The standardised post name
        - post_rank: The rank of the post

    Notes
        - Formats handled:
            - Minister for Policing, Fire and Criminal Justice and Victims -> No change
            - Parliamentary Under Secretary of State for Environment and Rural Affairs -> No change

            - Minister of State (Crime and Policing) -> Minister for Crime and Policing
            - Parliamentary Under Secretary of State (Americas, Caribbean and the Overseas Territories) -> Minister for Americas, Caribbean and the Overseas Territories        # noqa: E501

            - Minister of State (Minister for Africa) -> Minister for Africa
            - Parliamentary Under Secretary of State (Minister for AI and Intellectual Property) -> Minister for AI and Intellectual Property       # noqa: E501

            - Minister of State at the Northern Ireland Office -> Minister of State

            - Parliamentary Under Secretary of State and Minister for Defence Procurement -> Minister for Defence Procurement       # noqa: E501

            - Parliamentary Under Secretary of State, Minister for Faith -> Minister for Faith
    '''
    # Handle hyphenated PUSS post names
    if 'Under-Secretary' in post_name:
        post_name = standardise_puss_punctuation(post_name)

    # Set post rank
    if 'Parliamentary Under Secretary of State' in post_name:
        post_rank = 'PUSS'
    elif 'Minister' in post_name:
        post_rank = 'MoS'
    else:
        post_rank = None

    # Handle cases with brackets
    if '(' in post_name:
        post_name = post_name.split('(')[1].split(')')[0]
        if 'Minister for' not in post_name:
            post_name = 'Minister for ' + post_name

    # Handle 'Minister of State at' cases
    if 'Minister of State at' in post_name:
        post_name = 'Minister of State'

    # Handle 'Parliamentary Under Secretary of State and' cases
    if 'Parliamentary Under Secretary of State and ' in post_name:
        post_name = post_name.split('and ')[1]

    # Handle 'Parliamentary Under Secretary of State, ' cases
    if 'Parliamentary Under Secretary of State, ' in post_name:
        post_name = post_name.split(', ')[1]

    post_name = post_name.strip()

    return post_name, post_rank


def standardise_puss_punctuation(
    post_name: str
) -> str:
    '''
    Standardise punctuation in PUSS post names

    Parameters
        - post_name: The post name to be standardised

    Returns
        - post_name: The standardised post name

    Notes
        None
    '''
    # Handle hyphenated PUSS post names
    post_name = post_name.replace('Under-Secretary', 'Under Secretary')

    return post_name
