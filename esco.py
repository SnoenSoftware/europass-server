import requests
from functools import lru_cache


@lru_cache(maxsize=128)
def get_esco_occupation(uri: str, language_code: str) -> str:
    """
    Fetches occupation data from the ESCO API for a given occupation URI and language code.

    :param uri: The URI of the occupation in the ESCO system.
    :param language_code: The language code for the desired language (e.g., 'en', 'fr').
    :return: A dictionary containing the occupation data.
    """

    url = f"https://ec.europa.eu/esco/api/resource/occupation?uri={uri}"

    headers = {
        "Accept": "application/json",
    }

    # All languages are returned, we will filter later
    request = requests.get(url, headers=headers)
    if request.status_code != 200:
        raise Exception(
            f"Failed to fetch data from ESCO API: {request.status_code} {request.reason}"
        )
    data = request.json()
    if not data:
        raise Exception("No data found for the given occupation URI.")
    # Filter the data for the specified languages
    return data.get("preferredLabel", {}).get(language_code, "")
