import os
import sqlite3
import traceback
import torch
import random
import bittensor as bt
from typing import List


def check_uid_availability(
    metagraph: "bt.metagraph.Metagraph", uid: int, vpermit_tao_limit: int
) -> bool:
    """Check if uid is available. The UID should be available if it is serving and has less than vpermit_tao_limit stake
    Args:
        metagraph (:obj: bt.metagraph.Metagraph): Metagraph object
        uid (int): uid to be checked
        vpermit_tao_limit (int): Validator permit tao limit
    Returns:
        bool: True if uid is available, False otherwise
    """
    # Filter non serving axons.
    if not metagraph.axons[uid].is_serving:
        return False
    # Filter validator permit > 1024 stake.
    #if metagraph.validator_permit[uid]:
    #    if metagraph.S[uid] > vpermit_tao_limit:
    #        return False
    # Available otherwise.
    return True


def get_random_uids(
    self, k: int, exclude: List[int] = None
) -> torch.LongTensor:
    """Returns k available random uids from the metagraph.
    Args:
        k (int): Number of uids to return.
        exclude (List[int]): List of uids to exclude from the random sampling.
    Returns:
        uids (torch.LongTensor): Randomly sampled available uids.
    Notes:
        If `k` is larger than the number of available `uids`, set `k` to the number of available `uids`.
    """
    candidate_uids = []
    avail_uids = []

    for uid in range(self.metagraph.n.item()):
        uid_is_available = check_uid_availability(
            self.metagraph, uid, self.config.neuron.vpermit_tao_limit
        )
        uid_is_not_excluded = exclude is None or uid not in exclude

        if uid_is_available:
            avail_uids.append(uid)
            if uid_is_not_excluded:
                candidate_uids.append(uid)

    # Check if candidate_uids contain enough for querying, if not grab all avaliable uids
    available_uids = candidate_uids
    if len(candidate_uids) < k:
        available_uids += random.sample(
            [uid for uid in avail_uids if uid not in candidate_uids],
            k - len(candidate_uids),
        )
    uids = torch.tensor(random.sample(available_uids, k))
    return uids

def get_all_uids(
    self, exclude: List[int] = None
) -> torch.LongTensor:
    """Returns k available random uids from the metagraph.
    Args:
        k (int): Number of uids to return.
        exclude (List[int]): List of uids to exclude from the random sampling.
    Returns:
        uids (torch.LongTensor): Randomly sampled available uids.
    Notes:
        If `k` is larger than the number of available `uids`, set `k` to the number of available `uids`.
    """
    candidate_uids = []
    avail_uids = []
    for uid in range(self.metagraph.n.item()):
        uid_is_available = check_uid_availability(
            self.metagraph, uid, self.config.neuron.vpermit_tao_limit
        )
        uid_is_not_excluded = exclude is None or uid not in exclude

        if uid_is_available or os.getenv('ENV') == 'pytest':
            avail_uids.append(uid)
            if uid_is_not_excluded:
                candidate_uids.append(uid)

    available_uids = candidate_uids
    uids = torch.tensor(available_uids)
    return uids


def get_miner_data_by_uid(db_path, uid: int):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    result = None
    try:
        c = cursor.execute(
            """
            select miner_hotkey, miner_uid, node_ip, registered_date,last_updated,blocktime,blocklisted
            from miners
            where miner_uid = ?
            order by registered_date desc
            limit 1
            """,
            (uid,)
        )
        result: sqlite3.Row = c.fetchone()
    except Exception as e:
        bt.logging.error(e)
        bt.logging.error(traceback.format_exc())
    conn.close()
    return result


def miner_count_in_db(db_path) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    result = None
    try:
        c = cursor.execute(
            """
            select count(*)
            from miners
            """
        )
        result: int = c.fetchone()[0]
    except Exception as e:
        bt.logging.error(e)
        bt.logging.error(traceback.format_exc())
    conn.close()
    return result
