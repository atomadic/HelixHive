"""
Evolution Market for HelixHive – enables trait trading, auctions, and serendipity matching.
Agents can list traits for sale, search for complementary traits via Leech similarity,
and participate in auctions for synthetic traits. All transactions require council approval.
"""

import logging
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from agent import Agent
from memory import LeechProjection
import helixdb

logger = logging.getLogger(__name__)


class Market:
    """
    Handles trait listings, auctions, and reputation-based trading.
    """

    def __init__(self, db: 'helixdb.HelixDB', genome: Any):
        self.db = db
        self.genome = genome
        self.min_reputation = genome.data.get('market', {}).get('min_reputation', 10)
        self.auction_duration = genome.data.get('market', {}).get('auction_duration', 3600)  # 1 hour in ticks? Actually in seconds
        self.max_listings_per_agent = genome.data.get('market', {}).get('max_listings_per_agent', 5)

    # ----------------------------------------------------------------------
    # Trait Listings
    # ----------------------------------------------------------------------

    def list_trait(self, agent: Agent, trait_name: str, trait_value: float,
                   price: int) -> Optional[str]:
        """
        Create a new trait listing.
        Returns listing_id if successful, None if agent lacks reputation or too many listings.
        """
        if agent.reputation < self.min_reputation:
            logger.warning(f"Agent {agent.agent_id} reputation {agent.reputation} below minimum {self.min_reputation}")
            return None

        # Check number of active listings for this agent
        active_listings = self._get_active_listings(agent.agent_id)
        if len(active_listings) >= self.max_listings_per_agent:
            logger.warning(f"Agent {agent.agent_id} already has {len(active_listings)} active listings (max {self.max_listings_per_agent})")
            return None

        # Compute Leech vector for this trait (optional, for similarity search)
        # We can use the trait name's HD word vector and project to Leech
        hd_vec = HD.from_word(trait_name)  # HD is imported from memory
        leech_vec = LeechProjection.project(hd_vec)

        listing_id = str(uuid.uuid4())
        listing = {
            'listing_id': listing_id,
            'seller_id': agent.agent_id,
            'trait_name': trait_name,
            'trait_value': float(trait_value),
            'price': price,
            'leech_vector': leech_vec.tolist(),
            'created_at': time.time(),
            'status': 'active'
        }
        self.db.add_node('TraitListing', listing_id, properties=listing)
        # No commit; caller will commit after batch
        logger.info(f"Agent {agent.agent_id} listed trait {trait_name}={trait_value} for {price} reputation")
        return listing_id

    def search_traits(self, buyer: Agent, query_vector: Optional[np.ndarray] = None,
                      max_price: Optional[int] = None,
                      min_similarity: float = 0.7) -> List[Dict]:
        """
        Search for active trait listings.
        If query_vector is provided (buyer's Leech vector), returns listings ranked by
        Leech similarity * (1/price) heuristic.
        Otherwise returns all active listings sorted by price.
        """
        # Get all active listings
        all_listings = self._get_all_active_listings()

        if not all_listings:
            return []

        # Filter by price
        if max_price is not None:
            all_listings = [l for l in all_listings if l['price'] <= max_price]

        if not all_listings:
            return []

        # If no query vector, sort by price ascending
        if query_vector is None:
            all_listings.sort(key=lambda x: x['price'])
            return all_listings

        # Compute similarity scores
        scored = []
        for listing in all_listings:
            leech = np.array(listing['leech_vector'])
            sim = LeechProjection.similarity(query_vector, leech)
            if sim >= min_similarity:
                # Score = similarity / price (higher is better)
                score = sim / (listing['price'] + 1)  # avoid division by zero
                scored.append((score, listing))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return [l for _, l in scored]

    def buy_trait(self, buyer: Agent, listing_id: str) -> Optional[Dict]:
        """
        Initiate a purchase of a listed trait.
        Returns a proposal dict that needs council approval, or None if invalid.
        """
        listing = self._get_listing(listing_id)
        if not listing or listing['status'] != 'active':
            logger.warning(f"Listing {listing_id} not active")
            return None

        if buyer.agent_id == listing['seller_id']:
            logger.warning("Buyer cannot be the seller")
            return None

        if buyer.reputation < listing['price']:
            logger.warning(f"Buyer {buyer.agent_id} has insufficient reputation ({buyer.reputation} < {listing['price']})")
            return None

        # Create purchase proposal
        proposal = {
            'type': 'market_purchase',
            'proposer_id': buyer.agent_id,
            'description': f"Purchase trait {listing['trait_name']}={listing['trait_value']} from {listing['seller_id']} for {listing['price']} reputation",
            'tags': ['market', 'purchase'],
            'changes': {
                'listing_id': listing_id,
                'buyer_id': buyer.agent_id,
                'seller_id': listing['seller_id'],
                'trait_name': listing['trait_name'],
                'trait_value': listing['trait_value'],
                'price': listing['price']
            },
            'timestamp': time.time()
        }
        return proposal

    # ----------------------------------------------------------------------
    # Auctions
    # ----------------------------------------------------------------------

    def create_auction(self, seller: Agent, trait_name: str, trait_value: float,
                       starting_price: int, duration: Optional[int] = None) -> Optional[str]:
        """
        Create a new auction for a synthetic or existing trait.
        Duration in seconds; if None, uses genome default.
        Returns auction_id.
        """
        if seller.reputation < self.min_reputation:
            logger.warning(f"Seller {seller.agent_id} reputation too low for auction")
            return None

        if duration is None:
            duration = self.auction_duration

        auction_id = str(uuid.uuid4())
        end_time = time.time() + duration

        # Compute Leech vector for trait (for similarity)
        hd_vec = HD.from_word(trait_name)
        leech_vec = LeechProjection.project(hd_vec)

        auction = {
            'auction_id': auction_id,
            'seller_id': seller.agent_id,
            'trait_name': trait_name,
            'trait_value': float(trait_value),
            'starting_price': starting_price,
            'current_bid': starting_price,
            'current_bidder': None,
            'leech_vector': leech_vec.tolist(),
            'end_time': end_time,
            'status': 'active',
            'created_at': time.time()
        }
        self.db.add_node('Auction', auction_id, properties=auction)
        logger.info(f"Auction {auction_id} created by {seller.agent_id} for {trait_name}={trait_value}")
        return auction_id

    def place_bid(self, bidder: Agent, auction_id: str, bid_amount: int) -> Optional[bool]:
        """
        Place a bid on an active auction.
        Returns True if bid placed (as edge), False if invalid, None if auction ended.
        """
        auction = self._get_auction(auction_id)
        if not auction or auction['status'] != 'active':
            logger.warning(f"Auction {auction_id} not active")
            return None

        if time.time() >= auction['end_time']:
            # Auction ended, will be processed later
            return None

        if bidder.reputation < bid_amount:
            logger.warning(f"Bidder {bidder.agent_id} has insufficient reputation")
            return False

        if bid_amount <= auction['current_bid']:
            logger.warning(f"Bid {bid_amount} not higher than current bid {auction['current_bid']}")
            return False

        # Update auction node with new highest bid
        auction['current_bid'] = bid_amount
        auction['current_bidder'] = bidder.agent_id
        self.db.update_node(auction_id, properties=auction)

        # Record bid as an edge
        self.db.add_edge(bidder.agent_id, auction_id, 'BID', properties={
            'amount': bid_amount,
            'timestamp': time.time()
        })
        logger.info(f"Bid of {bid_amount} placed by {bidder.agent_id} on auction {auction_id}")
        return True

    def process_auctions(self) -> List[Dict]:
        """
        Check for ended auctions and generate purchase proposals for winners.
        Called periodically (e.g., each heartbeat).
        Returns list of proposal dicts for council approval.
        """
        proposals = []
        now = time.time()
        auctions = self._get_all_active_auctions()
        for auction in auctions:
            if now >= auction['end_time'] and auction['status'] == 'active':
                # Auction ended
                if auction['current_bidder'] is not None:
                    # Winner exists
                    proposal = {
                        'type': 'market_purchase',
                        'proposer_id': auction['current_bidder'],
                        'description': f"Auction win: {auction['trait_name']}={auction['trait_value']} from {auction['seller_id']} for {auction['current_bid']} reputation",
                        'tags': ['market', 'auction'],
                        'changes': {
                            'auction_id': auction['auction_id'],
                            'buyer_id': auction['current_bidder'],
                            'seller_id': auction['seller_id'],
                            'trait_name': auction['trait_name'],
                            'trait_value': auction['trait_value'],
                            'price': auction['current_bid']
                        },
                        'timestamp': now
                    }
                    proposals.append(proposal)
                    # Mark auction as completed
                    auction['status'] = 'completed'
                    self.db.update_node(auction['auction_id'], properties=auction)
                else:
                    # No bids, mark as expired
                    auction['status'] = 'expired'
                    self.db.update_node(auction['auction_id'], properties=auction)
        return proposals

    # ----------------------------------------------------------------------
    # Council Integration
    # ----------------------------------------------------------------------

    def apply_purchase(self, changes: Dict):
        """
        Apply an approved purchase (called by proposals engine).
        Transfers trait, updates reputation, and marks listing/auction as sold.
        """
        if 'listing_id' in changes:
            # Direct purchase
            listing_id = changes['listing_id']
            listing = self._get_listing(listing_id)
            if not listing or listing['status'] != 'active':
                raise ValueError(f"Listing {listing_id} not active")
            buyer_id = changes['buyer_id']
            seller_id = changes['seller_id']
            price = changes['price']
            trait_name = changes['trait_name']
            trait_value = changes['trait_value']

            # Update buyer's agent
            buyer_node = self.db.get_node(buyer_id)
            if not buyer_node:
                raise ValueError(f"Buyer {buyer_id} not found")
            # We need to load the full agent to modify traits
            buyer = Agent.load_from_db(self.db, buyer_id)
            buyer.traits[trait_name] = trait_value
            buyer.reputation -= price
            buyer.save_to_db(self.db)

            # Update seller's agent
            seller = Agent.load_from_db(self.db, seller_id)
            seller.reputation += price
            seller.save_to_db(self.db)

            # Mark listing as sold
            listing['status'] = 'sold'
            self.db.update_node(listing_id, properties=listing)

            # Record transaction
            self._record_transaction(buyer_id, seller_id, trait_name, trait_value, price, 'purchase')

        elif 'auction_id' in changes:
            # Auction win
            auction_id = changes['auction_id']
            auction = self._get_auction(auction_id)
            if not auction or auction['status'] != 'completed':
                raise ValueError(f"Auction {auction_id} not completed")
            buyer_id = changes['buyer_id']
            seller_id = changes['seller_id']
            price = changes['price']
            trait_name = changes['trait_name']
            trait_value = changes['trait_value']

            # Apply same as purchase
            buyer = Agent.load_from_db(self.db, buyer_id)
            buyer.traits[trait_name] = trait_value
            buyer.reputation -= price
            buyer.save_to_db(self.db)

            seller = Agent.load_from_db(self.db, seller_id)
            seller.reputation += price
            seller.save_to_db(self.db)

            # Auction already marked completed
            self._record_transaction(buyer_id, seller_id, trait_name, trait_value, price, 'auction')

        else:
            raise ValueError("Purchase changes missing listing_id or auction_id")

    # ----------------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------------

    def _get_active_listings(self, agent_id: str) -> List[Dict]:
        """Return active listings for a specific agent."""
        nodes = self.db.query_nodes_by_label('TraitListing')
        active = []
        for node in nodes:
            props = node.properties
            if props.get('seller_id') == agent_id and props.get('status') == 'active':
                active.append(props)
        return active

    def _get_all_active_listings(self) -> List[Dict]:
        """Return all active trait listings."""
        nodes = self.db.query_nodes_by_label('TraitListing')
        return [n.properties for n in nodes if n.properties.get('status') == 'active']

    def _get_listing(self, listing_id: str) -> Optional[Dict]:
        node = self.db.get_node(listing_id)
        if node and node.label == 'TraitListing':
            return node.properties
        return None

    def _get_all_active_auctions(self) -> List[Dict]:
        nodes = self.db.query_nodes_by_label('Auction')
        return [n.properties for n in nodes if n.properties.get('status') == 'active']

    def _get_auction(self, auction_id: str) -> Optional[Dict]:
        node = self.db.get_node(auction_id)
        if node and node.label == 'Auction':
            return node.properties
        return None

    def _record_transaction(self, buyer_id: str, seller_id: str, trait_name: str,
                            trait_value: float, price: int, tx_type: str):
        """Record a completed transaction for audit."""
        tx_id = str(uuid.uuid4())
        tx = {
            'transaction_id': tx_id,
            'buyer_id': buyer_id,
            'seller_id': seller_id,
            'trait_name': trait_name,
            'trait_value': trait_value,
            'price': price,
            'type': tx_type,
            'timestamp': time.time()
        }
        self.db.add_node('Transaction', tx_id, properties=tx)
        self.db.add_edge(buyer_id, tx_id, 'BOUGHT')
        self.db.add_edge(seller_id, tx_id, 'SOLD')


# Standalone functions for orchestrator/proposals engine to call

def process_market_actions(db: 'helixdb.HelixDB', genome: Any) -> List[Dict]:
    """
    Called each heartbeat to process auctions and generate proposals.
    Returns list of proposal dicts (for council).
    """
    market = Market(db, genome)
    proposals = market.process_auctions()
    return proposals


def apply_market_purchase(db: 'helixdb.HelixDB', genome: Any, changes: Dict):
    """
    Called by proposals engine when a market purchase proposal is approved.
    """
    market = Market(db, genome)
    market.apply_purchase(changes)
