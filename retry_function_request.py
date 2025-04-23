import logging
import sys
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from unittest.mock import Mock

class CustomError(Exception):
    """Custom exception for retry logic."""

    def __init__(self, message: str) -> None:
        """
        Initializes the exception with the error message.

        :param message: The error message detailing the issue.
        :type message: str
        """
        self.message = message
    def __str__(self):
        """
        Returns a string representation of the exception.

        :return: A string message describing the JSON parsing error.
        :rtype: str
        """
        return f"Failed to parse JSON from CRE response. Error: {self.message}"
# logging configs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logging.getLogger("urllib3").setLevel(logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
def confgure_session():
    #  retries + session
    retries = Retry(
        total=4,
        backoff_factor=0.5, #{backoff factor} * (2 ** ({number of previous retries})) 
        status_forcelist=[429, 500, 502, 503, 504]
    )

    session = Session()
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

def log_request_details(method: str, url: str, **kwargs):
    """
    Logs the details of an HTTP request.

    :param method: HTTP method (e.g., 'GET', 'POST').
    :param url: The URL to which the request is being sent.
    :param kwargs: Additional arguments such as headers or data.
    """
    logging.debug(f"Preparing HTTP request:")
    logging.debug(f"Method: {method}")
    logging.debug(f"URL: {url}")
    if 'headers' in kwargs:
        logging.debug(f"Headers: {kwargs['headers']}")
    if 'data' in kwargs:
        logging.debug(f"Body: {kwargs['data']}")

# Retry with the tenacity library 
@retry(
    stop=stop_after_attempt(4), 
    wait=wait_exponential(multiplier=0.5, min=0.1, max=1800),  
    retry=retry_if_exception_type(CustomError)  
)
def json_from_request(*args, **kwargs):
    """
    Makes http request using the session and retries on specific errors.
    """
    session = confgure_session()
    log_request_details(args[0], args[1], **kwargs)  # Log the request details

    response = session.request(*args, **kwargs)
    response.raise_for_status() 
    try:
        return response.json()  
    except Exception as ce: 
        custom_error = CustomError(message=str(ce))
        logging.error(custom_error)       
        raise custom_error
        


if __name__ == "__main__":

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    session = confgure_session()
    #session.request = Mock(return_value=mock_response)
    try:
        url1 = "https://jsonplaceholder.typicode.com/posts/1"
        url = "https://mocked-url.com"
        url2 = "https://example.com" 
        method = "GET"
        result = json_from_request(method,url2)
        print(result)
        logging.info(f"This branch is under dev")
        logging.info("mod3.1")
    except Exception as e:
        logging.error(f"Failed to retrieve data: {e}")
        