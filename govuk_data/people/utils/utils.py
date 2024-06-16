import re


def handle_parliamentary_secretary_post_name(
    post_name: str
) -> tuple[str, str]:
    '''
    Handle parliamentary secretary post names

    Parameters
        - post_name: The post name to be cleaned

    Returns
        - post_name: The cleaned post name
        - post_rank: The rank of the post

    Notes
        - Formats handled:
            - Parliamentary Secretary (Minister for Civil Society),
            Parliamentary Secretary (Minister for Constitutional Reform)
    '''
    # Handle parliamentary secretary post names
    if 'Parliamentary Secretary (Minister for' in post_name:
        post_name = post_name.replace(
            'Parliamentary Secretary (Minister for ',
            'Parliamentary Secretary for '
        ).replace(')', '')
        post_rank = 'PUSS'

    return post_name, post_rank


def identify_ministers_on_leave_acting(
    post_name: str
) -> tuple[str, bool, bool, str]:
    '''
    Identify ministers on leave or doing a role in an acting capacity

    Parameters
        - post_name: The post name to be checked

    Returns
        - post_name: The post name with any leave or acting capacity identified
        - is_on_leave: Whether the minister is on leave
        - is_acting: Whether the minister is doing a role in an acting capacity
        - leave_reason: The reason for the minister being on leave

    Notes
        - Formats handled:
            - Minister on Leave (Attorney General)
            - Minister on Leave (Minister of State)
            - Interim Minister of State for Energy and Clean Growth
            - Interim Parliamentary Secretary (Minister for the Constitution)
            - Parliamentary Under Secretary of State for Sport, Tourism and
            Heritage (maternity cover)
        - This should be applied before standardising post names, as we may
        need to standardise the results of this function
    '''

    # Handle on leave
    if 'Minister on Leave' in post_name:
        post_name = post_name.split('(', maxsplit=1)[1].split(')', maxsplit=1)[0]
        is_on_leave = True
        leave_reason = 'Maternity leave'
    else:
        is_on_leave = False
        leave_reason = None

    # Handle acting
    if 'Interim' in post_name:
        post_name = post_name.replace('Interim ', '')
        is_acting = True
    elif '(maternity cover)' in post_name:
        post_name = post_name.replace(' (maternity cover)', '')
        is_acting = True
    else:
        is_acting = False

    return post_name, is_on_leave, is_acting, leave_reason


def remove_joint_post_name(
    post_name: str
) -> str:
    '''
    Remove details of roles being done in a joint capacity from ministerial post names

    Parameters
        - post_name: The post name to be cleaned

    Returns
        - post_name: The cleaned post name

    Notes
        - Formats handled:
            - Minister of State (Climate, Environment and Energy – joint with FCDO and Defra)
        - This should be applied before standardising post names, as we may
        need to standardise the results of this function
    '''
    # Handle joint post names
    if ' – joint with ' in post_name:
        post_name = re.sub(r'\s\S\sjoint with\s\w*(\sand\s\w*)*', '', post_name)        # noqa: E501, F821 (needed to fend of a flake8 misfire)

    return post_name


def remove_lords_minister_post_names(
    post_name: str
) -> str:
    '''
    Remove details of Lords minister roles from post names

    Parameters
        - post_name: The post name to be cleaned

    Returns
        - post_name: The cleaned post name

    Notes
        - Formats handled:
                - Parliamentary Under Secretary of State (Minister for the Lords)
                - Minister of State for Civil Justice (Lords Minister)
                - Parliamentary Under Secretary of State for Arts and Heritage and
                DCMS Lords Minister
        - This should be applied before standardising post names, as we may
        need to standardise the results of this function
    '''
    if ' (Minister for the Lords)' in post_name:
        post_name = post_name.replace(' (Minister for the Lords)', '')
    elif ' (Lords Minister)' in post_name:
        post_name = post_name.replace(' (Lords Minister)', '')
    elif ' and DCMS Lords Minister' in post_name:
        post_name = post_name.replace(' and DCMS Lords Minister', '')

    return post_name


def standardise_mos_puss_post_name(
    post_name: str
) -> tuple[str, str]:
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

            - Minister of State for Cabinet Office -> Minister of State for Cabinet Office
            - Minister of State for Cabinet Office (Cities and Constitution) -> Minister for Cities and Constitution

            - Parliamentary Under Secretary of State and Minister for Defence Procurement -> Minister for Defence Procurement       # noqa: E501

            - Parliamentary Under Secretary of State, Minister for Faith -> Minister for Faith

            - Parliamentary Under Secretary of State and Minister for Defence Equipment, Support and Technology (including Defence Exports) -> Minister for Defence Equipment, Support and Technology (including Defence Exports)       # noqa: E501
    '''
    # Handle hyphenated PUSS post names
    if 'Under-Secretary' in post_name:
        post_name = standardise_puss_punctuation(post_name)

    # Handle cases where the post name is not a MoS or PUSS post name
    if not ('Minister of State' or 'Parliamentary Under Secretary of State' in post_name):
        return post_name, None

    # Set post rank
    if 'Parliamentary Under Secretary of State' in post_name:
        post_rank = 'PUSS'
    elif 'Minister of State' in post_name:
        post_rank = 'MoS'
    else:
        post_rank = None

    # Handle 'Minister of State at' cases
    if 'Minister of State at' in post_name:
        post_name = 'Minister of State'

    # Handle 'Minister of State for Cabinet Office' cases
    if 'Minister of State for Cabinet Office' == post_name:
        post_name = 'Minister of State'
    elif 'Minister of State for Cabinet Office (' in post_name:
        post_name = post_name.replace(
            'Minister of State for Cabinet Office (', 'Minister for '
        ).replace(')', '')

    # Handle 'Parliamentary Under Secretary of State and' cases
    if 'Parliamentary Under Secretary of State and ' in post_name:
        post_name = post_name.split('and ', maxsplit=1)[1]

    # Handle 'Parliamentary Under Secretary of State, ' cases
    if 'Parliamentary Under Secretary of State, ' in post_name:
        post_name = post_name.split(', ', maxsplit=1)[1]

    # Handle cases with brackets
    # NB: Needs to be done after handling 'Parliamentary Under Secretary of State and' cases
    # to handle 'Parliamentary Under Secretary of State and Minister for Defence Equipment,
    # Support and Technology (including Defence Exports)' correctly
    if '(' in post_name:
        if '(Minister' in post_name:
            post_name = post_name.split('(', maxsplit=1)[1].split(')', maxsplit=1)[0]
        elif 'Minister for' not in post_name:
            post_name = 'Minister for ' + post_name.split(
                '(',
                maxsplit=1
            )[1].split(')', maxsplit=1)[0]

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
