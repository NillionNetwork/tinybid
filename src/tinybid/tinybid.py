"""
Minimal pure-Python library that implements a basic single-item
first-price auction via a secure multi-party computation (MPC)
protocol.
"""
from __future__ import annotations
from typing import Dict, List, Set, Tuple, Sequence, Iterable
import doctest
import secrets
from modulo import modulo
from bitlist import bitlist
import tinynmc

class node:
    """
    Data structure for maintaining the information associated with a node
    and performing node operations.

    Suppose that a workflow is supported by three nodes (parties performing
    a decentralized auction). The :obj:`node` objects would be instantiated
    locally by each of these three parties.

    >>> nodes = [node(), node(), node()]

    The preprocessing workflow that the nodes must execute can be simulated
    using the :obj:`preprocess` function. The number of bids that a workflow
    requires must be known, and it is assumed that all permitted bid prices
    are integers greater than or equal to ``0`` and strictly less than a fixed
    maximum value. The number of bids and the number of distinct prices must
    be supplied to the :obj:`preprocess` function.

    >>> preprocess(nodes, bids=4, prices=16)

    Each bidder must then submit a request for the opportunity to submit a bid.
    The bidders can create :obj:`request` instances for this purpose. In the
    example below, each of the four bidders creates such a request.

    >>> request_zero = request(identifier=0)
    >>> request_one = request(identifier=1)
    >>> request_two = request(identifier=2)
    >>> request_three = request(identifier=3)

    Each bidder can deliver their request to each node, and each node can then
    locally use its :obj:`masks` method to generate masks that can be returned
    to the requesting bidder.

    >>> masks_zero = [node.masks(request_zero) for node in nodes]
    >>> masks_one = [node.masks(request_one) for node in nodes]
    >>> masks_two = [node.masks(request_two) for node in nodes]
    >>> masks_three = [node.masks(request_three) for node in nodes]

    Each bidder can then generate locally a :obj:`bid` instance (*i.e.*, a
    masked bid price).

    >>> bid_zero = bid(masks_zero, 7)
    >>> bid_one = bid(masks_one, 11)
    >>> bid_two = bid(masks_two, 2)
    >>> bid_three = bid(masks_three, 11)

    Every bidder can broadcast its masked bid to all the nodes. Each node
    can locally assemble these as they arrive. Once a node has received all
    masked bids, it can determine its shares of the overall outcome of the
    auction using the :obj:`outcome` method.

    >>> shares = [
    ...     node.outcome([bid_zero, bid_one, bid_two, bid_three])
    ...     for node in nodes
    ... ]

    The overall outcome can be reconstructed from the shares by the auction
    operator using the :obj:`reveal` function. The outcome is represented as
    a :obj:`set` containing the :obj:`int` identifiers of the winning bidders.

    >>> list(sorted(reveal(shares)))
    [1, 3]
    """
    def masks( # pylint: disable=arguments-renamed,redefined-outer-name
            self: node,
            request: Iterable[Tuple[int, int]]
        ) -> List[Dict[Tuple[int, int], modulo]]:
        """
        Return masks for a given request.

        :param request: Request from bidder.
        """
        return [ # pylint: disable=no-member
            tinynmc.node.masks(self._nodes[i], request)
            for i in range(self._prices) # pylint: disable=no-member
        ]

    def outcome(self: node, bids: Sequence[bid]) -> List[modulo]:
        """
        Perform computation to determine a share of the auction outcome.

        :param bids: Sequence of masked bids.
        """
        prices = len(bids[0])
        return [ # pylint: disable=no-member
            self._nodes[i].compute(
                getattr(self, '_signature'),
                [bid[i] for bid in bids]
            )
            for i in range(prices)
        ]

class request(List[Tuple[int, int]]):
    """
    Data structure for representing a request to submit a bid. A request can be
    submitted to each node to obtain corresponding masks for a bid.

    :param identifier: Integer identifying the requesting bidder.

    The example below demonstrates how requests can be created.

    >>> request(identifier=1),
    ([(0, 1)],)
    >>> request(identifier=3),
    ([(0, 3)],)
    """
    def __init__(self: request, identifier: int) -> request:
        self.append((0, identifier))

class bid(List[Dict[Tuple[int, int], modulo]]):
    """
    Data structure for representing a bid that can be broadcast to nodes.

    :param masks: Collection of masks to be applied to the bid price.
    :param price: Non-negative integer representing the bid price.

    Suppose masks have already been obtained from the nodes via the steps
    below.

    >>> nodes = [node(), node(), node()]
    >>> preprocess(nodes, bids=4, prices=16)
    >>> identifier = 2
    >>> price = 7
    >>> masks = [node.masks(request(identifier)) for node in nodes]

    This method can be used to mask the bid price (in preparation for
    broadcasting it to the nodes).
    
    >>> isinstance(bid(masks, price), bid)
    True
    """
    def __init__(
            self: bid,
            masks: List[List[Dict[Tuple[int, int], modulo]]],
            price: int
        ):
        """
        Create a masked bid price that can be broadcast to nodes.
        """
        modulus = list(masks[0][0].values())[0].modulus
        prices = len(masks[0])
        for i in range(prices):
            masks_i = [mask[i] for mask in masks]
            key = list(masks_i[0].keys())[0]
            identifier = key[1]
            coordinate_to_value = {}
            coordinate_to_value[key] = (
                2**(2**(identifier + 1))
                if i == price else (
                    1
                    if i > price else
                    1 + secrets.randbelow(modulus - 1)
                )
            )
            self.append(tinynmc.masked_factors(coordinate_to_value, masks_i))

def preprocess(nodes: Sequence[node], bids: int, prices: int):
    """
    Simulate a preprocessing workflow among the supplied nodes for a workflow
    that supports the specified number of bids and distinct prices (where
    prices are assumed to be integers greater than or equal to ``0`` and
    strictly less than the value ``prices``).

    :param nodes: Collection of nodes involved in the workflow.
    :param bids: Number of bids.
    :param prices: Number of distinct prices (from ``0`` to ``prices``).

    The example below performs a preprocessing workflow involving three nodes.

    >>> nodes = [node(), node(), node()]
    >>> preprocess(nodes, bids=4, prices=16)
    """
    signature = [bids]

    for node_ in nodes:
        setattr(node_, '_signature', signature)
        setattr(node_, '_prices', prices)
        setattr(node_, '_bids', [])
        setattr(node_, '_nodes', [
            tinynmc.node()
            for _ in range(prices)
        ])

    for i in range(prices):
        # pylint: disable=protected-access
        tinynmc.preprocess(
            signature,
            [node_._nodes[i] for node_ in nodes]
        )

def reveal(shares: List[List[modulo]]) -> Set[int]:
    """
    Reconstruct the auction outcome from the shares obtained from each node.

    :param shares: Outcome shares (where each share is a list of components,
        with one component per permitted price).

    Suppose the shares below are returned from the three nodes in a workflow.

    >>> p = 4215209819
    >>> shares = [
    ...     [modulo(3, p), modulo(5, p), modulo(4, p)],
    ...     [modulo(1, p), modulo(2, p), modulo(9, p)],
    ...     [modulo(8, p), modulo(0, p), modulo(8, p)]
    ... ]

    This method combines such shares into an overall outcome be reconstructing
    the individual components and decoding the identifiers of the winning
    bidders.

    >>> reveal(shares)
    {1}
    """
    prices = len(shares[0])
    for i in reversed(range(prices)):
        shares_i = [share[i] for share in shares]
        bits = bitlist(int(sum(shares_i)).bit_length() - 1, length=5)[:-1]
        outcome = {
            identifier
            for (identifier, bit) in enumerate(reversed(bits))
            if bit == 1
        }
        if len(outcome) > 0:
            return outcome

    return set() # pragma: no cover

if __name__ == '__main__':
    doctest.testmod() # pragma: no cover
