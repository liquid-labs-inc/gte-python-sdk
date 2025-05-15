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
from dataclasses import dataclass

from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address


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
    weth_address: ChecksumAddress = None


TESTNET_CONFIG = NetworkConfig(
    name="MegaETH Testnet",
    api_url="https://api-testnet.gte.xyz",
    ws_url="wss://api-testnet.gte.xyz/ws",
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
    router_address=to_checksum_address("0x86470efcEa37e50F94E74649463b737C87ada367"),
    launchpad_address=to_checksum_address("0x0B6cD1DefCe3189Df60A210326E315383fbC14Ed"),
    clob_manager_address=to_checksum_address("0xfB78cfDc3f64e71F83DbB49D3Ab81b63AeD971af"),
    weth_address=to_checksum_address("0x776401b9BC8aAe31A685731B7147D4445fD9FB19"),
)
