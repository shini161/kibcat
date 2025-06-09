import re


def format_T_in_date(duration: str) -> str:
    """
    Adds 'T' to an ISO 8601 duration string if time components (H, M, S) are present
    but 'T' is missing.
    """
    if "T" in duration:
        return duration

    # Check for time components after date
    match = re.search(r"(\d+H|\d+M|\d+S)", duration)
    if match:
        # Find the position after the date part (after D, M, or Y)
        date_part_match = re.match(r"^P(?:\d+Y)?(?:\d+M)?(?:\d+D)?", duration)
        if date_part_match:
            insert_pos = date_part_match.end()
            return duration[:insert_pos] + "T" + duration[insert_pos:]
        else:
            return "PT" + duration[1:]

    return duration
