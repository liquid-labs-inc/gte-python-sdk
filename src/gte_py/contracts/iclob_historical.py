\
"""
Historical event querying module for CLOB contract events.

This module provides functionality to query past events
from the CLOB (Central Limit Order Book) contract.
"""
from typing import List, Optional

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.contract import ContractEvent

from .events import OrderMatchedEvent, parse_order_matched
from .utils import load_abi


class CLOBHistoricalQuerier:
    """
    Querier for historical CLOB contract events.

    Provides methods to fetch past events like OrderMatched
    from a CLOB contract within specified block ranges.
    """

    def __init__(self, web3: Web3, contract_address: ChecksumAddress):
        """
        Initialize the CLOB historical querier.

        Args:
            web3: Web3 instance connected to a provider.
            contract_address: Address of the CLOB contract.
        """
        self.web3 = web3
        self.address = contract_address
        loaded_abi = load_abi("iclob")
        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)
        self._order_matched_event: ContractEvent = self.contract.events.OrderMatched

    def query_order_matched(
        self,
        from_block: int,
        to_block: int | str = "latest",
        maker: Optional[ChecksumAddress] = None,
        taker: Optional[ChecksumAddress] = None,
    ) -> List[OrderMatchedEvent]:
        """
        Query historical OrderMatched events within a block range.

        Args:
            from_block: Starting block number (inclusive).
            to_block: Ending block number (inclusive) or 'latest'.
            maker: Optional filter by maker address.
            taker: Optional filter by taker address.

        Returns:
            A list of parsed OrderMatchedEvent objects.
        """
        argument_filters = {}
        if maker:
            argument_filters["maker"] = maker
        if taker:
            argument_filters["taker"] = taker

        try:
            raw_logs = self._order_matched_event.get_logs(
                fromBlock=from_block,
                toBlock=to_block,
                argument_filters=argument_filters if argument_filters else None,
            )
            parsed_events = [parse_order_matched(log) for log in raw_logs]
            return parsed_events
        except Exception as e:
            # TODO: Add more specific error handling based on web3 exceptions
            print(f"Error querying OrderMatched events: {e}")
            return []

