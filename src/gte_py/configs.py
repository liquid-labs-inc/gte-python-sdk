"""
Network Name	MegaETH Testnet
Chain ID	6342
Network ID	6342
Native Token (Symbol)	MegaETH Testnet Ether (ETH)
Native Token Decimals	18
RPC HTTP URL	https://api-testnet.gte.xyz/v1/exchange
RPC WebSocket URL	wss://carrot.megaeth.com/ws
Block Explorer	Performance Dashboard: https://uptime.megaeth.com
Community Explorer: https://megaexplorer.xyz
Experimental EIPs Supported	EIP-7702
EIP-1559 Base Fee Price	0.0025 Gwei
EIP-1559 Max Block Size	2 Giga gas
EIP-1559 Target Block Size	50% (1 Giga gas)
Block Time	10ms for mini blocks
1s for EVM blocks

"""

import os
from dotenv import load_dotenv
from dataclasses import dataclass

from eth_typing import ChecksumAddress
from eth_utils.address import to_checksum_address

load_dotenv()

@dataclass
class NetworkConfig:
    """
    Configuration for a blockchain network.
    """

    name: str
    api_url: str
    ws_url: str
    chain_id: int
    native_token: str
    rpc_http: str
    rpc_ws: str
    block_explorer: str
    performance_dashboard: str
    experimental_eips: list[str]
    eip_1559_base_fee_price: float
    eip_1559_max_block_size: int
    eip_1559_target_block_size: int
    block_time: str
    router_address: ChecksumAddress
    launchpad_address: ChecksumAddress
    clob_manager_address: ChecksumAddress
    perp_manager_address: ChecksumAddress
    account_manager_address: ChecksumAddress
    operator_address: ChecksumAddress
    weth_address: ChecksumAddress
    collateral_asset_address: ChecksumAddress


TESTNET_CONFIG = NetworkConfig(
    name="MegaETH Testnet",
    api_url="https://dev-api.gte.xyz/v1",
    ws_url="wss://dev-api.gte.xyz/ws",
    chain_id=6342,
    native_token="MegaETH Testnet Ether (ETH)",
    rpc_http=os.environ.get("MEGAETH_TESTNET_RPC_HTTP", "https://api-testnet.gte.xyz/v1/exchange"),
    rpc_ws=os.environ.get("MEGAETH_TESTNET_RPC_WS", "wss://carrot.megaeth.com/ws"),
    block_explorer="https://megaexplorer.xyz",
    performance_dashboard="https://uptime.megaeth.com",
    experimental_eips=["EIP-7702"],
    eip_1559_base_fee_price=0.0025,
    eip_1559_max_block_size=2_000_000_000,
    eip_1559_target_block_size=1_000_000_000,
    block_time="10ms for mini blocks, 1s for EVM blocks",
    router_address=to_checksum_address("0x9D7C72614BAC0ded1c71bf3051510e457CA42523"),
    launchpad_address=to_checksum_address("0x978D817F54d60E7CDE2c3DE4195e9C94A60CF45B"),
    clob_manager_address=to_checksum_address("0x242F153ABe6585f12a788A150cEd1899D1E19621"),
    perp_manager_address=to_checksum_address("0x75598cFaD8912ef7AB801d1f57437eF758176727"),
    account_manager_address=to_checksum_address("0xbbAfd85eb0A8770c0BefC7a2B7593Ed216711869"),
    operator_address=to_checksum_address("0x62DA32Bd335f16D071Ee67183A64cdc8dF97e8d1"),
    weth_address=to_checksum_address("0x776401b9BC8aAe31A685731B7147D4445fD9FB19"),
    collateral_asset_address=to_checksum_address("0xe9b6e75c243b6100ffcb1c66e8f78f96feea727f"),
)