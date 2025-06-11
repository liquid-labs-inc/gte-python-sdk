from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar('T')


async def paged_request(request: Callable[[int, int], Awaitable[list[T]]], page_size: int, total_limit: int) -> list[T]:
    """
    Perform a paged request to fetch data in chunks.
    :param request:  A callback function that takes limit and offset as arguments and returns a list of results.
    :param page_size:
    :param total_limit:
    :return:
    """
    results = []
    page_size_adjusted = page_size + 1
    while len(results) < total_limit:
        # Fetch the next page of results
        new_results = await request(page_size_adjusted, len(results))
        results.extend(new_results[:page_size])
        if len(new_results) == page_size_adjusted:
            continue
        else:
            break
    return results
