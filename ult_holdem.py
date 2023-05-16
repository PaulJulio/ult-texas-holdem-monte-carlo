from phevaluator import evaluate_cards
import random

suits = ['d', 's', 'c', 'h']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
cards = []
for r in ranks:
    for s in suits:
        cards.append(r + s)
# adjust the following values to test your preferred strategy
# the ranks index of the minimum rank pair to bet preflop
# ex: 1 means bet a pair of 3s but not 2s; 9 means to bet Jacks but not Tens
MIN_PAIR = 1
# for the above index of ranks, if that rank is the highest card, what is the lowest card to bet preflop with
# two can't be highest but is included for completeness
# ex: ranks[9] is the Jack, so PREFLOP_ANY[9] is the ranks index of the lower card to bet any jack on
# 13 is equivalent to never since the ranks are index 0-12
PREFLOP_ANY = [13, 13, 13, 13, 13, 13, 13, 13, 13, 8, 6, 3, 0]
PREFLOP_SUITED = [13, 13, 13, 13, 13, 13, 13, 13, 7, 6, 4, 0, 0]


def play():
    dealer = []
    player = []
    table = []
    deck = random.sample(cards, len(cards))  # shuffle
    while len(player) < 2:
        player.append(deck[0])  # copy top card to player hand
        deck = deck[1:]  # pop the top card off the deck
        dealer.append(deck[0])
        deck = deck[1:]

    while len(table) < 5:
        table.append(deck[0])
        deck = deck[1:]

    prank = evaluate_cards(player[0], player[1], table[0], table[1], table[2], table[3], table[4])
    drank = evaluate_cards(dealer[0], dealer[1], table[0], table[1], table[2], table[3], table[4])
    print(f'Player Cards: {player[0]} {player[1]} Rank: {prank}')
    print(f'Dealer Cards: {dealer[0]} {dealer[1]} Rank: {drank}')
    print(f'Table  Cards: {table[0]} {table[1]} {table[2]} {table[3]} {table[4]}')
    print(f'Dealer Outs: {dealer_outs(player, table)}')


def dealer_outs(player, table):
    # NOTE: this is not checking for "double-card" outs (so if the dealer needs two spades for a flush,
    # it won't be counted here)
    # what will be counted are boats, over-pairs, trips, and single-card-needed for a straight or flush
    visible = player + table
    prank = evaluate_cards(*visible)
    outs = 0
    deck = list(filter(lambda x: x not in visible, cards))
    for card in deck:
        dealer_possible = table + [card]
        drank = evaluate_cards(*dealer_possible)
        if drank < prank:
            outs += 1
    return outs


def sim_hand(player, runs):
    # given a hand as a list and the number of time to simulate it, do runs simulations and report on results
    deck = list(filter(lambda x: x not in player, cards))
    wins = 0
    losses = 0
    ties = 0
    while wins + losses + ties < runs:
        shuffled = random.sample(deck, len(deck))
        dealer = []
        table = []
        while len(dealer) < 2:
            dealer.append(shuffled[0])
            shuffled = shuffled[1:]
        while len(table) < 5:
            table.append(shuffled[0])
            shuffled = shuffled[1:]
        pcards = player + table
        dcards = dealer + table
        prank = evaluate_cards(*pcards)
        drank = evaluate_cards(*dcards)
        if prank < drank:
            wins += 1
        if drank < prank:
            losses += 1
        if prank == drank:
            ties += 1
    print(f'Cards: {player}')
    print(f'W:{wins} L:{losses} T:{ties} R:{wins+losses+ties}')
    print(f'W%:{wins/runs*100} L%:{losses/runs*100} T%:{ties/runs*100}')


def sim_card_off(rank, runs):
    # this is a convenience function to run all possibilities of the given rank with the 13 ranks in another suit
    # handy for giving odds pre-flop to build a chart for when to 4-bet
    for r in ranks:
        hand = [rank+'s', r+'h']
        sim_hand(hand, runs)


def sim_card_suited(rank, runs):
    # this is a convenience function to run all possibilities of the given rank with the 12 ranks in the same suit
    # handy for giving odds pre-flop to build a chart for when to 4-bet
    for r in ranks:
        hand = [rank+'s', r+'s']
        if r != rank:
            sim_hand(hand, runs)



def rank(card):
    return card[0:1]


def suit(card):
    return card[1:]


def is_suited(c1, c2):
    if suit(c1) == suit(c2):
        return 1
    return 0


def order_hole_cards(hole_cards):
    r1 = rank(hole_cards[0])
    r2 = rank(hole_cards[1])
    v1 = ranks.index(r1)
    v2 = ranks.index(r2)
    if v1 < v2:
        return[hole_cards[1], hole_cards[0]]
    return hole_cards


def bet_pre_flop(hole_cards):
    hole_cards = order_hole_cards(hole_cards)
    # do we have a pair large enough to bet?
    if rank(hole_cards[0]) == rank(hole_cards[1]):
        if ranks.index(rank(hole_cards[0])) >= MIN_PAIR:
            return 1
        return 0
    high_card_index = ranks.index(rank(hole_cards[0]))
    low_card_index = ranks.index(rank(hole_cards[1]))
    if PREFLOP_ANY[high_card_index] <= low_card_index:
        return 1
    if suit(hole_cards[0]) == suit(hole_cards[1]):
        if PREFLOP_SUITED[high_card_index] <= low_card_index:
            return 1
    return 0


def rank_check():
    # in order to check for payouts on the Trips side bet, we need to know the ranks that qualify for each payout
    rank = evaluate_cards('2s', '2c', '3h', '3d', '4s')
    print(f'Worst two-pair hand rank {rank}')  # 3325 - I needed this for the post-flop betting check
    rank = evaluate_cards('Ah', 'As', 'Kh', 'Ks', 'Qh')
    print(f'Best two-pair hand rank {rank}')  # 2468 - this is the lowest rank hand that does not qualify for trips
    rank = evaluate_cards('2h', '2s', '2d', '3s', '4h')
    print(f'Worst trips hand rank {rank}')  # 2467
    rank = evaluate_cards('Ah', 'As', 'Ad', 'Ks', 'Qh')
    print(f'Best trips hand rank {rank}')  # 1610
    rank = evaluate_cards('2h', '3s', '4d', '5s', 'Ah')
    print(f'Worst straight hand rank {rank}')  # 1609
    rank = evaluate_cards('Th', 'Js', 'Qd', 'Ks', 'Ah')
    print(f'Best straight hand rank {rank}')  # 1600
    rank = evaluate_cards('2h', '3h', '4h', '5h', '7h')
    print(f'Worst flush hand rank {rank}')  # 1599
    rank = evaluate_cards('Ah', 'Kh', 'Qh', 'Jh', '9h')
    print(f'Best flush hand rank {rank}')  # 323
    rank = evaluate_cards('2h', '2s', '2d', '3s', '3h')
    print(f'Worst full house hand rank {rank}')  # 322
    rank = evaluate_cards('Ah', 'As', 'Ad', 'Ks', 'Kh')
    print(f'Best full house hand rank {rank}')  # 167
    rank = evaluate_cards('2h', '2s', '2d', '2c', '3h')
    print(f'Worst quads hand rank {rank}')  # 166
    rank = evaluate_cards('Ah', 'As', 'Ad', 'Ac', 'Kh')
    print(f'Best quads hand rank {rank}')  # 11
    rank = evaluate_cards('2h', '3h', '4h', '5h', 'Ah')
    print(f'Worst straight flush hand rank {rank}')  # 10
    rank = evaluate_cards('Th', 'Jh', 'Qh', 'Kh', 'Ah')
    print(f'Best straight flush (royal flush) hand rank {rank}')  # 1