def check_env_vars(
    url: str | None,
    elastic_url: str | None,
    base_url_part: str | None,
    username: str | None,
    password: str | None,
    space_id: str | None,
    data_view_id: str | None,
) -> None:
    """Checks if the env variables loaded really exist.

    Returns:
        str | None: None if every variable has been loaded successfully
                    str with the error message if a variable is missing
    """
    msg = None

    if not url:
        msg = "[utils.check_env_vars] - Missing `URL` env variable"
    elif not elastic_url:
        msg = "[utils.check_env_vars] - Missing `ELASTIC_URL` env variable"
    elif not base_url_part:
        msg = "[utils.check_env_vars] - Missing `BASE_URL_PART` env variable"
    elif not username:
        msg = "[utils.check_env_vars] - Missing `USERNAME` env variable"
    elif not password:
        msg = "[utils.check_env_vars] - Missing `PASSWORD` env variable"
    elif not space_id:
        msg = "[utils.check_env_vars] - Missing `SPACE_ID` env variable"
    elif not data_view_id:
        msg = "[utils.check_env_vars] - Missing `DATA_VIEW_ID` env variable"

    if msg is not None:
        raise ValueError(msg)
