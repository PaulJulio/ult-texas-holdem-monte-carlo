from phevaluator import evaluate_cards
import random
import csv

suits = ['d', 's', 'c', 'h']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
cards = []
for r in ranks:
    for s in suits:
        cards.append(r + s)
# adjust the following values to test your preferred pre-flop strategy
# we'll check the rank's index of the minimum rank pair to bet preflop
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
    bet_large = 0
    bet_medium = 0
    bet_small = 0
    paid = 0
    deck = random.sample(cards, len(cards))  # shuffle
    # testing a setup
    while len(player) < 2:
        player.append(deck[0])  # copy top card to player hand
        deck = deck[1:]  # pop the top card off the deck
        dealer.append(deck[0])
        deck = deck[1:]

    if bet_pre_flop(player):
        bet_large = 4

    while len(table) < 3:
        table.append(deck[0])
        deck = deck[1:]
    if bet_large == 0 and bet_flop(player, table):
        bet_medium = 2

    while len(table) < 5:
        table.append(deck[0])
        deck = deck[1:]
    if bet_large == 0 and bet_medium == 0 and bet_river(player, table):
        bet_small = 1

    prank = evaluate_cards(player[0], player[1], table[0], table[1], table[2], table[3], table[4])
    drank = evaluate_cards(dealer[0], dealer[1], table[0], table[1], table[2], table[3], table[4])
    play_bet = bet_large + bet_medium + bet_small
    wagered = 2 + play_bet
    if prank == drank and play_bet > 0:
        paid = wagered  # on a push, player gets their bet back
    if prank > drank > 6185 and play_bet > 0:
        paid = 1  # when the dealer doesn't qualify, the ante is a push. but the rest of our bet is lost on a loss
    if prank < drank and play_bet > 0:
        if drank <= 6185:
            paid += 2  # dealer qualified, ante bet pays 1:1
        else:
            paid += 1  # deal did not qualify, ante bet refunded
        paid += 2 * play_bet  # on a win, the play pays 1:1
        # ante and play always pay 1:1, but the bet may pay a bonus
        if prank == 1:
            paid += 501  # royal flush pays 500:1
        elif prank <= 10:
            paid += 51  # straight flush pays 50:1
        elif prank <= 166:
            paid += 11  # quads pays 10:1
        elif prank <= 322:
            paid += 4  # full house pays 3:1
        elif prank <= 1599:
            paid += 2.5  # flush pays 3:2
        elif prank <= 1609:
            paid += 2  # straight pays 1:1
        else:
            paid += 1  # all other winning hands push the bet
    data = player + table + dealer + [wagered, paid, prank, drank]
    return data


def play_session(num_hands=200, outfile="ultimate_holdem.csv"):
    with open(outfile, 'w') as f:
        write = csv.writer(f)
        write.writerow(["P1", "P2", "T1", "T2", "T3", "T4", "T5", "D1", "D2", "Wager", "Paid", "P-Rank", "D-Rank"])
        hands_played = 0
        while hands_played < num_hands:
            hand_data = play()
            write.writerow(hand_data)
            hands_played += 1


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
    print(f'W:{wins} L:{losses} T:{ties} R:{wins + losses + ties}')
    print(f'W%:{wins / runs * 100} L%:{losses / runs * 100} T%:{ties / runs * 100}')


def sim_card_off(rank, runs):
    # this is a convenience function to run all possibilities of the given rank with the 13 ranks in another suit
    # handy for giving odds pre-flop to build a chart for when to 4-bet
    for r in ranks:
        hand = [rank + 's', r + 'h']
        sim_hand(hand, runs)


def sim_card_suited(rank, runs):
    # this is a convenience function to run all possibilities of the given rank with the 12 ranks in the same suit
    # handy for giving odds pre-flop to build a chart for when to 4-bet
    for r in ranks:
        hand = [rank + 's', r + 's']
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
        return [hole_cards[1], hole_cards[0]]
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


def hidden_pair(hole_cards, table):
    # do one of our hold cards pair the table?
    # a hidden pair is hidden because our hold cards are "hidden" from the table
    # conversely, a pair on the board would be "open"
    for hc in hole_cards:
        for tc in table:
            if rank(hc) == rank(tc):
                return 1
    return 0


def bet_flop(hole_cards, table):
    hole_cards = order_hole_cards(hole_cards)
    combined_cards = hole_cards + table
    hand_rank = evaluate_cards(*combined_cards)
    # bet if you will play at least two pair
    if hand_rank <= 3325:
        return 1
    # bet if you will play at least 1 pair AND you don't have pocket deuces AND you beat the board (have a hidden pair)
    if hand_rank <= 6185:  # hand is worth at least a pair
        if rank(hole_cards[0]) == rank(hole_cards[1]) and rank(hole_cards[0]) != '2':
            return 1  # pocket pair that isn't pocket deuces
        if hidden_pair(hole_cards, table):
            return 1  # paired the board
    # bet if your first hole card is Ten or higher and four to a flush
    if ranks.index(rank(hole_cards[0])) >= 8:
        flush_count = 1
        flush_suit = suit(hole_cards[0])
        for c in table:
            if suit(c) == flush_suit:
                flush_count += 1
        if flush_count >= 4:
            return 1
    # bet if your second hole card is Ten or higher and four to a flush
    if ranks.index(rank(hole_cards[1])) >= 8:
        flush_count = 1
        flush_suit = suit(hole_cards[1])
        for c in table:
            if suit(c) == flush_suit:
                flush_count += 1
        if flush_count >= 4:
            return 1
    # otherwise don't bet
    return 0


def bet_river(hole_cards, table):
    combined_cards = hole_cards + table
    hand_rank = evaluate_cards(*combined_cards)
    table_rank = evaluate_cards(*table)
    # bet a straight or better, even if it's on the board (the dealer won't have more than 20 outs)
    if hand_rank <= 1609:
        return 1
    # bet one pair or better if there's a hidden pair (1 pair, 2 pair, or trips where we're using a hole card)
    if hand_rank <= 6185 and hidden_pair(hole_cards, table):
        return 1
    # bet if the dealer has fewer than 21 outs
    if dealer_outs(hole_cards, table) < 21:
        return 1
    return 0


def hand_check():
    # in order to check for payouts on the Trips side bet, we need to know the ranks that qualify for each payout
    rank = evaluate_cards('2s', '2c', '3h', '4d', '5s')
    print(f'Worst one-pair hand rank {rank}')  # 6185 - I needed this for dealer qualification checking
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
