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
    router_address=to_checksum_address("0x0465d91c4d05Ee2EdaF6896E806a5F20Eeb71839"),
    launchpad_address=to_checksum_address("0xA2615452E816E86EC577F0E65cd2c94Cd3E2270D"),
    clob_manager_address=to_checksum_address("0xcc8ebeFf517CC027cF19E6569fd948405BB964bD"),
    perp_manager_address=to_checksum_address("0x8e981E2B700F7c249F182dF4E74A66e90664c056"),
    account_manager_address=to_checksum_address("0x13C1e1A76eC1Bd6073A26981aA3375eCb07846BE"),
    operator_address=to_checksum_address("0xEA172E9cDd7eefAEC54a1ba724416e277E81B9E1"),
    weth_address=to_checksum_address("0x1872b2A8FD83C07D1cCcEe1341a01221843178DE"),
    collateral_asset_address=to_checksum_address("0xDB9D607C0D7709C8d2a3a841c970A554AF9B8B45"),
)