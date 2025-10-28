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
    rpc_http="https://carrot.megaeth.com/rpc",
    rpc_ws=os.environ.get("MEGAETH_TESTNET_RPC_WS", "wss://carrot.megaeth.com/ws"),
    block_explorer="https://megaexplorer.xyz",
    performance_dashboard="https://uptime.megaeth.com",
    experimental_eips=["EIP-7702"],
    eip_1559_base_fee_price=0.0025,
    eip_1559_max_block_size=2_000_000_000,
    eip_1559_target_block_size=1_000_000_000,
    block_time="10ms for mini blocks, 1s for EVM blocks",
    router_address=to_checksum_address("0x427e373fDdEB61AB4c7bD0CF7a72b90300510126"),
    launchpad_address=to_checksum_address("0x3EE715d443c0e1ffa1110ab87132d0375c885745"),
    clob_manager_address=to_checksum_address("0x48A98077ea84c6D8dbe76157c5EAd1CeC7A0fb38"),
    perp_manager_address=to_checksum_address("0x75598cFaD8912ef7AB801d1f57437eF758176727"),
    account_manager_address=to_checksum_address("0x5A3b510173d7771D8f8075C8271f78798d826070"),
    operator_address=to_checksum_address("0xCCDB3Fa82999Ed47CD8A45c03da4be675ffcddC6"),
    weth_address=to_checksum_address("0x776401b9BC8aAe31A685731B7147D4445fD9FB19"),
    collateral_asset_address=to_checksum_address("0xe9b6e75c243b6100ffcb1c66e8f78f96feea727f"),
)