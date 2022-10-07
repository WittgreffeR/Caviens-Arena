import random
from os import system, name

###TEXT COLOURS
class colour:   #Colours only display properly when run directly from the file, they bug out in shell
    GREEN = "\033[92m"      #Health
    RED = "\033[91m"        #Damage and Lives
    YELLOW = "\033[93m"     #Coins
    BLUE = "\033[94m"       #Energy
    CYAN = "\033[96m"       #Ammunition or use limit
    PURPLE = "\033[95m"     #Block
    END = "\033[0m"         #Stop use of colour

###READ DECK FROM CARDS.TXT
deck = []

with open("Cards.txt", "r") as deck_file:
    cards = deck_file.read().split("\n")

for x in range (0, len(cards)):
    card = list(cards[x].split(","))
    card[3] = int(card[3])  #Energy cost
    card[4] = int(card[4])  #Coin cost
    if not card[0] == "Magic":  #Keep entry 5 as string if it is a magic card
        card[5] = int(card[5])  #Otherwise convert to int as the entry will be a number
    card[6] = int(card[6])  #Usually a dmg/healing value
    card[7] = int(card[7])  #Used to keep track of maximum melee use limit or ammo, or health boost for passives
    deck.append(card)


#Cards use the following values according to their type (first entry):
#[Melee,Name,Description,Energy Cost,Coin Cost,Melee Use Limit,Damage,Max Use Limit]
#[Defence,Name,Description,Energy Cost,Coin Cost,0,Block Value,0]
#[Ranged,Name,Description,Energy Cost,Coin Cost,Ammunition,Damage,Max Ammo]
#[Magic,Name,Description,Energy Cost,Coin Cost,Magic Type,Damage/Healing (if heal magic),0]
#[Item,Name,Description,Lives Returned,Coin Cost,Damage,Healing,Energy Boost]
#[Passive,Name,Description,Block Boost,Coin Cost,Damage Boost,Coin Boost,Health Boost]


###VARIABLE SETUP

ai_enabled = 0   #Currently a useless variable, but can be changed with an input when setting up the game once AI is implemented
round_count = 1     #How many rounds have passed
lives_to_lose = 1   #How many lives are lost upon defeat - increases by 1 on round 3 and then increases by 1 every other round from there
round_increment = 0 #Used in calculation of lives_to_lose
card_count = len(deck)-1    #How many cards are in the deck minus one, to use for selecting a card from the deck
drawn_cards = []   #Drawn cards
damage_dealt = 0    #Used to track and calculate damage dealt

#Player 1 variables
p1_lives = 10
p1_coins = 5
p1_energy = 4
p1_block = 0
p1_health = 50
p1_hand = []
p1_exhausted = 0
p1_did_forfeit = 0

#Player 2 variables (this is the AI player if AI is enabled)
p2_lives = 10
p2_coins = 5
p2_energy = 4
p2_block = 0
p2_health = 50
p2_hand = []
p2_exhausted = 0
p2_did_forfeit = 0


###CORE FUNCTIONS
def clear():    #Clear the screen - only works if run directly from the file, does NOT work in python shell
    if name == "nt":
        _ = system("cls")

    else:
        _ = system("clear")

def play_round():   #Unfortunately all these variables have to be global to avoid fatal errors
    global p1_health
    global p2_health
    global p1_energy
    global p2_energy
    global p1_block
    global p2_block
    global p1_coins
    global p2_coins
    global p1_exhausted
    global p2_exhausted
    global p1_did_forfeit
    global p2_did_forfeit
    global p1_lives
    global p2_lives

    #I don't actually know if these three NEED to be global but I'm making them global just in case to prevent any potential errors, since local variables cause such a hassle here
    global round_count
    global lives_to_lose
    global round_increment
    
    #Begin shop phase
    p1_shop()
    p2_shop()

    p1_exhausted = 0
    p1_did_forfeit = 0
    p2_exhausted = 0
    p2_did_forfeit = 0

    #Reset health
    p1_health = 50
    for x in range (0,len(p1_hand)):    #Add health boosts from passives to health pool if they exist
        if p1_hand[x][0] == "Passive" and p1_hand[x][7] > 0:
            p1_health += p1_hand[x][7]

    p2_health = 50
    for x in range (0,len(p2_hand)):    #Add health boosts from passives to health pool if they exist
        if p2_hand[x][0] == "Passive" and p2_hand[x][7] > 0:
            p2_health += p2_hand[x][7]

    #Play out turns until finish
    while p1_health > 0 and p2_health > 0 and not (p1_exhausted == 1 and p2_exhausted == 1):
        p1_battle()
        p1_energy += 1
        clear()
        p2_battle()
        p2_energy += 1
        clear()

    #Coins
    p1_coins += 3
    for x in range (0,len(p1_hand)):    #Add coin boosts from passives if they exist
        if p1_hand[x][0] == "Passive" and p1_hand[x][6] > 0:
            p1_coins += p1_hand[x][6]
    
    p2_coins += 3
    for x in range (0,len(p2_hand)):    #Add coin boosts from passives if they exist
        if p2_hand[x][0] == "Passive" and p2_hand[x][6] > 0:
            p2_coins += p2_hand[x][6]

    #Round counter and lives to lose
    round_count += 1
    round_increment += 1

    if round_increment == 2:
        round_increment = 1
        lives_to_lose += 1

    #Win messages
    if p1_health > 0 and p2_health <= 0:    #p1 kills p2
        p2_lives -= lives_to_lose
        print("Player 1 wins this round by killing player 2!")
        p1_defeats_p2()
    elif p1_health <= 0 and p2_health > 0:  #p2 kills p1
        p1_lives -= lives_to_lose
        print("Player 2 wins this round by killing player 1!")
        p2_defeats_p1()
    elif p1_exhausted == 1 and p2_exhausted == 1:   #Ended by exhaustion
        if p1_health > p2_health:
            p2_lives -= lives_to_lose
            print("Player 1 wins this round by having more health than player 2 after their cards were exhausted!")
            p1_defeats_p2()
        elif p1_health < p2_health:
            p1_lives -= lives_to_lose
            print("Player 2 wins this round by having more health than player 1 after their cards were exhausted!")
            p2_defeats_p1()
        elif p1_health == p2_health:
            input("This round has ended in a draw, as both players exhausted their offensive options and were left with equal health.\nNeither player has lost any lives. ")
    clear()
    

def p1_defeats_p2():    #Just so I don't have to repeat this code several times
    if lives_to_lose == 1:
        print("\nPlayer 2 has lost "+colour.RED+"1"+colour.END+" life ", end="")
    else:
        print("\nPlayer 2 has lost "+colour.RED+str(lives_to_lose)+colour.END+" lives ", end="")
        
    if p2_lives == 1:
        input("and now has "+colour.RED+"1"+colour.END+" life remaining. ")
    elif p2_lives <= 0:
        input("and now has "+colour.RED+"NO"+colour.END+" lives remaining! ")
    else:
        input("and now has "+colour.RED+str(p2_lives)+colour.END+" lives remaining. ")

def p2_defeats_p1():    #Just so I don't have to repeat this code several times
    if lives_to_lose == 1:
        print("\nPlayer 1 has lost "+colour.RED+"1"+colour.END+" life ", end="")
    else:
        print("\nPlayer 1 has lost "+colour.RED+str(lives_to_lose)+colour.END+" lives ", end="")
        
    if p1_lives == 1:
        input("and now has "+colour.RED+"1"+colour.END+" life remaining. ")
    elif p1_lives <= 0:
        input("and now has "+colour.RED+"NO"+colour.END+" lives remaining! ")
    else:
        input("and now has "+colour.RED+str(p1_lives)+colour.END+" lives remaining. ")


###SHOP FUNCTIONS

def p1_shop():  #Player 1's shop phase
    global p1_hand
    drawn_cards = []    #Reset the list
    for x in range (0,4):   #Draw 4 random cards
        drawn_cards.append(deck[random.randint(0,card_count)])

    #If there are no attack cards in player's hand and no attack cards in the draw, replace the 4th card with Punch
    if not ("Melee" in [x[0] for x in p1_hand] or "Ranged" in [x[0] for x in p1_hand] or any(x[0] == "Item" and x[5] > 0 for x in p1_hand) or any(x[0] == "Magic" and x[5] != "Healing" for x in p1_hand)) and not ("Melee" in [x[0] for x in drawn_cards] or "Ranged" in [x[0] for x in drawn_cards] or any(x[0] == "Item" and x[5] > 0 for x in drawn_cards) or any(x[0] == "Magic" and x[5] != "Healing" for x in drawn_cards)):
        drawn_cards.pop(3)
        drawn_cards.append(deck[0]) #First entry in Cards.txt MUST ALWAYS be Punch for this to work
    
    p1_printdraw(drawn_cards)
    clear()

def p1_printdraw(drawn_cards):
    global p1_coins
    global p1_hand

    if lives_to_lose == 1:
        print("PLAYER 1'S SHOP PHASE\n\nIt is round "+str(round_count)+". You will lose "+colour.RED+"1"+colour.END+" life if you lose this round.")
    else:
        print("PLAYER 1'S SHOP PHASE\n\nIt is round "+str(round_count)+". You will lose "+colour.RED+str(lives_to_lose)+colour.END+" lives if you lose this round.")
        
    if p1_lives == 1:
        print("You have "+colour.RED+"1"+colour.END+" life remaining.")
    else:
        print("You have "+colour.RED+str(p1_lives)+colour.END+" lives remaining.")
    
    if p1_coins == 1:
        print("You have "+colour.YELLOW+"1 Coin"+colour.END+".")
    else:
        print("You have "+colour.YELLOW+str(p1_coins)+" Coins"+colour.END+".")

    print("You have "+colour.PURPLE+str(p1_block)+" Block"+colour.END+". Your Block is retained between rounds, but your Health is not.\n\nYou can buy:\n")
    
    for x in range (0,len(drawn_cards)):
        if drawn_cards[x][0] == "Magic":  #If card is a magic card, list magic type (stored in position 5)
            print(str(x+1)+". "+str(drawn_cards[x][1])+" ("+str(drawn_cards[x][0])+" - "+str(drawn_cards[x][5])+")")
        else:
             print(str(x+1)+". "+str(drawn_cards[x][1])+" ("+str(drawn_cards[x][0])+")")
    
        print("\t"+drawn_cards[x][2]+"\n\n\tCoin Cost: "+colour.YELLOW+str(drawn_cards[x][4])+colour.END)
    
        if not drawn_cards[x][0] == "Item" and not drawn_cards[x][0] == "Passive":   #Items and Passives do not have an energy cost, so only display this if its another type
            print("\tEnergy Cost: "+colour.BLUE+str(drawn_cards[x][3])+colour.END)

        if drawn_cards[x][0] == "Melee" or drawn_cards[x][0] == "Ranged":
            print("\tDamage: "+colour.RED+str(drawn_cards[x][6])+colour.END)
        elif drawn_cards[x][0] == "Magic" and not drawn_cards[x][5] == "Healing":
            print("\tDamage: "+colour.RED+str(drawn_cards[x][6])+colour.END)
        elif drawn_cards[x][0] == "Magic" and drawn_cards[x][5] == "Healing":
            print("\tHealing: "+colour.GREEN+str(drawn_cards[x][6])+colour.END)
        elif drawn_cards[x][0] == "Item" and drawn_cards[x][5] > 0:
            print("\tDamage: "+colour.RED+str(drawn_cards[x][5])+colour.END)
        elif drawn_cards[x][0] == "Item" and drawn_cards[x][6] > 0:
            print("\tHealing: "+colour.GREEN+str(drawn_cards[x][6])+colour.END)
        elif drawn_cards[x][0] == "Item" and drawn_cards[x][3] > 0:
            if drawn_cards[x][3] == 1:
                print("\tGain "+colour.RED+"1"+colour.END+" Life")
            else:
                print("\tGain "+colour.RED+str(drawn_cards[x][3])+colour.END+" Lives")
        elif drawn_cards[x][0] == "Item" and drawn_cards[x][7] > 0:
            print("\tGain "+colour.BLUE+str(drawn_cards[x][7])+colour.END+" Energy")
        elif drawn_cards[x][0] == "Defence":
            print("\tBlock: "+colour.PURPLE+str(drawn_cards[x][6])+colour.END)
        elif drawn_cards[x][0] == "Passive":
            if drawn_cards[x][3] > 0:
                print("\tIncreases added Block by "+colour.PURPLE+str(drawn_cards[x][3])+colour.END)
            if drawn_cards[x][5] > 0:
                print("\tIncreases all Damage by "+colour.RED+str(drawn_cards[x][5])+colour.END)
            if drawn_cards[x][6] > 0:
                print("\tIncreases Coins per turn by "+colour.YELLOW+str(drawn_cards[x][6])+colour.END)
            if drawn_cards[x][7] > 0:
                print("\tIncreases maximum Health by "+colour.GREEN+str(drawn_cards[x][7])+colour.END)

        if drawn_cards[x][0] == "Melee":
            if drawn_cards[x][5] > 1:
                print("\tCan be used "+colour.CYAN+str(drawn_cards[x][5])+colour.END+" times per round")
            else:
                print("\tCan be used "+colour.CYAN+"once"+colour.END+" per round")
        elif drawn_cards[x][0] == "Ammunition":
            print("\tAmmunition: "+colour.CYAN+str(drawn_cards[x][5])+colour.END)

        print("")

    buy = input("Type the number of the card you wish to buy. If you wish to sell a card in your hand, type \"s\". If you wish to end the shop phase, type \"n\". ")
    print("")
    if buy == "1" or buy == "2" or buy == "3" or buy == "4":
        buy = int(buy)
        buy -= 1
        if buy <= len(drawn_cards)-1:
            if p1_coins >= drawn_cards[buy][4]: #Make sure the player can afford the card
                p1_hand.append([*drawn_cards[buy]])
                p1_coins -= drawn_cards[buy][4]
                if drawn_cards[buy][4] > 1:
                    input("You have bought "+str(drawn_cards[buy][1])+" for "+colour.YELLOW+str(drawn_cards[buy][4])+" coins"+colour.END+". ")
                else:
                    input("You have bought "+str(drawn_cards[buy][1])+" for "+colour.YELLOW+"1 coin"+colour.END+". ")
                drawn_cards.pop(buy)
            else:
                input("You cannot afford to buy "+str(drawn_cards[buy][1])+"! ")
        else:   #Failsafe in case player tries to buy a card that doesnt exist
            input("There is no card "+str(buy+1)+" to purchase! ")
    elif buy == "s":
        if p1_hand == []:   #Failsafe in case player tries to sell cards without having any
            input("You have no cards to sell! ")
        else:
            clear()
            p1_sellcards()
    elif buy == "n":
        if "Melee" in [x[0] for x in p1_hand] or "Ranged" in [x[0] for x in p1_hand] or any(x[0] == "Item" and x[5] > 0 for x in p1_hand) or any(x[0] == "Magic" and x[5] != "Healing" for x in p1_hand):
            clear()
            input("\nNow ending player 1's shop phase. Player 2, please take the seat. ") #Show a different message when playing against AI
            return
        else:
            clear()
            noattack = input("You are about to end your shop phase with no damage-dealing cards in your hand.\nUnless your opponent also has no damage-dealing cards, you are guaranteed to lose the next round. Are you sure you want to continue? (y/n) ")
            if noattack == "y":
                input("\nNow ending player 1's shop phase. Player 2, please take the seat. ") #Show a different message when playing against AI
                return
    else:
        input("Input not understood. ")

    clear()
    p1_printdraw(drawn_cards)

def p1_sellcards():
    global p1_coins
    global p1_hand
    
    if lives_to_lose == 1:
        print("PLAYER 1'S SHOP PHASE\n\nIt is round "+str(round_count)+". You will lose "+colour.RED+"1"+colour.END+" life if you lose this round.")
    else:
        print("PLAYER 1'S SHOP PHASE\n\nIt is round "+str(round_count)+". You will lose "+colour.RED+str(lives_to_lose)+colour.END+" lives if you lose this round.")
        
    if p1_lives == 1:
        print("You have "+colour.RED+"1"+colour.END+" life remaining.")
    else:
        print("You have "+colour.RED+str(p1_lives)+colour.END+" lives remaining.")
    
    if p1_coins == 1:
        print("You have "+colour.YELLOW+"1 Coin"+colour.END+".")
    else:
        print("You have "+colour.YELLOW+str(p1_coins)+" Coins"+colour.END+".")

    print("You have "+colour.PURPLE+str(p1_block)+" Block"+colour.END+". Your Block is retained between rounds, but your Health is not.\n\nYou can sell:\n")
    
    for x in range (0,len(p1_hand)):
        if p1_hand[x][0] == "Magic":  #If card is a magic card, list magic type (stored in position 5)
            print(str(x+1)+". "+str(p1_hand[x][1])+" ("+str(p1_hand[x][0])+" - "+str(p1_hand[x][5])+")")
        else:
             print(str(x+1)+". "+str(p1_hand[x][1])+" ("+str(p1_hand[x][0])+")")
    
        print("\t"+p1_hand[x][2]+"\n\n\tCoin Cost: "+colour.YELLOW+str(p1_hand[x][4])+colour.END)
    
        if not p1_hand[x][0] == "Item" and not p1_hand[x][0] == "Passive":   #Items and Passives do not have an energy cost, so only display this if its another type
            print("\tEnergy Cost: "+colour.BLUE+str(p1_hand[x][3])+colour.END)

        if p1_hand[x][0] == "Melee" or p1_hand[x][0] == "Ranged":
            print("\tDamage: "+colour.RED+str(p1_hand[x][6])+colour.END)
        elif p1_hand[x][0] == "Magic" and not p1_hand[x][5] == "Healing":
            print("\tDamage: "+colour.RED+str(p1_hand[x][6])+cp1_coinsolour.END)
        elif p1_hand[x][0] == "Magic" and p1_hand[x][5] == "Healing":
            print("\tHealing: "+colour.GREEN+str(p1_hand[x][6])+colour.END)
        elif p1_hand[x][0] == "Item" and p1_hand[x][5] > 0:
            print("\tDamage: "+colour.RED+str(p1_hand[x][5])+colour.END)
        elif p1_hand[x][0] == "Item" and p1_hand[x][6] > 0:
            print("\tHealing: "+colour.GREEN+str(p1_hand[x][6])+colour.END)
        elif p1_hand[x][0] == "Item" and p1_hand[x][3] > 0:
            if p1_hand[x][3] == 1:
                print("\tGain "+colour.RED+"1"+colour.END+" Life")
            else:
                print("\tGain "+colour.RED+str(p1_hand[x][3])+colour.END+" Lives")
        elif p1_hand[x][0] == "Item" and p1_hand[x][7] > 0:
            print("\tGain "+colour.BLUE+str(p1_hand[x][7])+colour.END+" Energy")
        elif p1_hand[x][0] == "Defence":
            print("\tBlock: "+colour.PURPLE+str(p1_hand[x][6])+colour.END)
        elif p1_hand[x][0] == "Passive":
            if p1_hand[x][3] > 0:
                print("\tIncreases added Block by "+colour.PURPLE+str(p1_hand[x][3])+colour.END)
            if p1_hand[x][5] > 0:
                print("\tIncreases all Damage by "+colour.RED+str(p1_hand[x][5])+colour.END)
            if p1_hand[x][6] > 0:
                print("\tIncreases Coins per turn by "+colour.YELLOW+str(p1_hand[x][6])+colour.END)
            if p1_hand[x][7] > 0:
                print("\tIncreases maximum Health by "+colour.GREEN+str(p1_hand[x][7])+colour.END)

        if p1_hand[x][0] == "Melee":
            if p1_hand[x][5] > 1:
                print("\tCan be used "+colour.CYAN+str(p1_hand[x][5])+colour.END+" times per round")
            else:
                print("\tCan be used "+colour.CYAN+"once"+colour.END+" per round")
        elif p1_hand[x][0] == "Ammunition":
            print("\tAmmunition: "+colour.CYAN+str(p1_hand[x][5])+"/"+str(p1_hand[x][7])+colour.END)

        print("")

    sell = input("Type the number of the card you wish to sell. Remember that selling any card only returns "+colour.YELLOW+"1 coin"+colour.END+". If you wish to return to the buy menu, type \"b\". ")
    print("")
    if sell == "1" or sell == "2" or sell == "3" or sell == "4" or sell == "5" or sell == "6" or sell == "7":
        sell = int(sell)
        sell -= 1
        if sell <= len(p1_hand)-1:
            p1_coins += 1
            input("You have sold "+str(p1_hand[sell][1])+" and gained back "+colour.YELLOW+"1 coin"+colour.END+". ")
            p1_hand.pop(sell)
        else:   #Failsafe in case player tries to sell a card that doesnt exist
            input("There is no card "+str(sell+1)+" to sell! ")
    elif sell == "b":
        return
    else:
        input("Input not understood. ")
        
    clear()
    p1_sellcards()

def p2_shop():  #Player 2's shop phase
    global p2_hand
    drawn_cards = []    #Reset the list
    for x in range (0,4):   #Draw 4 random cards
        drawn_cards.append(deck[random.randint(0,card_count)])

    #If there are no attack cards in player's hand and no attack cards in the draw, replace the 4th card with Punch
    if not ("Melee" in [x[0] for x in p2_hand] or "Ranged" in [x[0] for x in p2_hand] or any(x[0] == "Item" and x[5] > 0 for x in p2_hand) or any(x[0] == "Magic" and x[5] != "Healing" for x in p2_hand)) and not ("Melee" in [x[0] for x in drawn_cards] or "Ranged" in [x[0] for x in drawn_cards] or any(x[0] == "Item" and x[5] >0 for x in drawn_cards) or any(x[0] == "Magic" and x[5] != "Healing" for x in drawn_cards)):
        drawn_cards.pop(3)
        drawn_cards.append(deck[0]) #First entry in Cards.txt MUST ALWAYS be Punch for this to work
    
    p2_printdraw(drawn_cards)
    clear()

def p2_printdraw(drawn_cards):
    global p2_coins
    global p2_hand
    
    if lives_to_lose == 1:
        print("PLAYER 2'S SHOP PHASE\n\nIt is round "+str(round_count)+". You will lose "+colour.RED+"1"+colour.END+" life if you lose this round.")
    else:
        print("PLAYER 2'S SHOP PHASE\n\nIt is round "+str(round_count)+". You will lose "+colour.RED+str(lives_to_lose)+colour.END+" lives if you lose this round.")
        
    if p2_lives == 1:
        print("You have "+colour.RED+"1"+colour.END+" life remaining.")
    else:
        print("You have "+colour.RED+str(p2_lives)+colour.END+" lives remaining.")
    
    if p2_coins == 1:
        print("You have "+colour.YELLOW+"1 Coin"+colour.END+".")
    else:
        print("You have "+colour.YELLOW+str(p2_coins)+" Coins"+colour.END+".")

    print("You have "+colour.PURPLE+str(p2_block)+" Block"+colour.END+". Your Block is retained between rounds, but your Health is not.\n\nYou can buy:\n")
       
    for x in range (0,len(drawn_cards)):
        if drawn_cards[x][0] == "Magic":  #If card is a magic card, list magic type (stored in position 5)
            print(str(x+1)+". "+str(drawn_cards[x][1])+" ("+str(drawn_cards[x][0])+" - "+str(drawn_cards[x][5])+")")
        else:
             print(str(x+1)+". "+str(drawn_cards[x][1])+" ("+str(drawn_cards[x][0])+")")
    
        print("\t"+drawn_cards[x][2]+"\n\n\tCoin Cost: "+colour.YELLOW+str(drawn_cards[x][4])+colour.END)
    
        if not drawn_cards[x][0] == "Item" and not drawn_cards[x][0] == "Passive":   #Items and Passives do not have an energy cost, so only display this if its another type
            print("\tEnergy Cost: "+colour.BLUE+str(drawn_cards[x][3])+colour.END)

        if drawn_cards[x][0] == "Melee" or drawn_cards[x][0] == "Ranged":
            print("\tDamage: "+colour.RED+str(drawn_cards[x][6])+colour.END)
        elif drawn_cards[x][0] == "Magic" and not drawn_cards[x][5] == "Healing":
            print("\tDamage: "+colour.RED+str(drawn_cards[x][6])+colour.END)
        elif drawn_cards[x][0] == "Magic" and drawn_cards[x][5] == "Healing":
            print("\tHealing: "+colour.GREEN+str(drawn_cards[x][6])+colour.END)
        elif drawn_cards[x][0] == "Item" and drawn_cards[x][5] > 0:
            print("\tDamage: "+colour.RED+str(drawn_cards[x][5])+colour.END)
        elif drawn_cards[x][0] == "Item" and drawn_cards[x][6] > 0:
            print("\tHealing: "+colour.GREEN+str(drawn_cards[x][6])+colour.END)
        elif drawn_cards[x][0] == "Item" and drawn_cards[x][3] > 0:
            if drawn_cards[x][3] == 1:
                print("\tGain "+colour.RED+"1"+colour.END+" Life")
            else:
                print("\tGain "+colour.RED+str(drawn_cards[x][3])+colour.END+" Lives")
        elif drawn_cards[x][0] == "Item" and drawn_cards[x][7] > 0:
            print("\tGain "+colour.BLUE+str(drawn_cards[x][7])+colour.END+" Energy")
        elif drawn_cards[x][0] == "Defence":
            print("\tBlock: "+colour.PURPLE+str(drawn_cards[x][6])+colour.END)
        elif drawn_cards[x][0] == "Passive":
            if drawn_cards[x][3] > 0:
                print("\tIncreases added Block by "+colour.PURPLE+str(drawn_cards[x][3])+colour.END)
            if drawn_cards[x][5] > 0:
                print("\tIncreases all Damage by "+colour.RED+str(drawn_cards[x][5])+colour.END)
            if drawn_cards[x][6] > 0:
                print("\tIncreases Coins per turn by "+colour.YELLOW+str(drawn_cards[x][6])+colour.END)
            if drawn_cards[x][7] > 0:
                print("\tIncreases maximum Health by "+colour.GREEN+str(drawn_cards[x][7])+colour.END)

        if drawn_cards[x][0] == "Melee":
            if drawn_cards[x][5] > 1:
                print("\tCan be used "+colour.CYAN+str(drawn_cards[x][5])+colour.END+" times per round")
            else:
                print("\tCan be used "+colour.CYAN+"once"+colour.END+" per round")
        elif drawn_cards[x][0] == "Ammunition":
            print("\tAmmunition: "+colour.CYAN+str(drawn_cards[x][5])+colour.END)

        print("")

    buy = input("Type the number of the card you wish to buy. If you wish to sell a card in your hand, type \"s\". If you wish to end the shop phase, type \"n\". ")
    print("")
    if buy == "1" or buy == "2" or buy == "3" or buy == "4":
        buy = int(buy)
        buy -= 1
        if buy <= len(drawn_cards)-1:
            if p2_coins >= drawn_cards[buy][4]: #Make sure the player can afford the card
                p2_hand.append([*drawn_cards[buy]])
                p2_coins -= drawn_cards[buy][4]
                if drawn_cards[buy][4] > 1:
                    input("You have bought "+str(drawn_cards[buy][1])+" for "+colour.YELLOW+str(drawn_cards[buy][4])+" coins"+colour.END+". ")
                else:
                    input("You have bought "+str(drawn_cards[buy][1])+" for "+colour.YELLOW+"1 coin"+colour.END+". ")
                drawn_cards.pop(buy)
            else:
                input("You cannot afford to buy "+str(drawn_cards[buy][1])+"! ")
        else:   #Failsafe in case player tries to buy a card that doesnt exist
            input("There is no card "+str(buy+1)+" to purchase! ")
    elif buy == "s":
        if p2_hand == []:   #Failsafe in case player tries to sell cards without having any
            input("You have no cards to sell! ")
        else:
            clear()
            p2_sellcards()
    elif buy == "n":
        if "Melee" in [x[0] for x in p2_hand] or "Ranged" in [x[0] for x in p2_hand] or any(x[0] == "Item" and x[5] > 0 for x in p2_hand) or any(x[0] == "Magic" and x[5] != "Healing" for x in p2_hand):
            clear()
            input("\nNow ending player 2's shop phase. Player 1, please take the seat. ") #Show a different message when playing against AI
            return
        else:
            clear()
            noattack = input("You are about to end your shop phase with no damage-dealing cards in your hand.\nUnless your opponent also has no damage-dealing cards, you are guaranteed to lose the next round. Are you sure you want to continue? (y/n) ")
            if noattack == "y":
                input("\nNow ending player 2's shop phase. Player 1, please take the seat. ") #Show a different message when playing against AI
                return
    else:
        input("Input not understood. ")
        
    clear()
    p2_printdraw(drawn_cards)

def p2_sellcards():
    global p2_coins
    global p2_hand
    
    if lives_to_lose == 1:
        print("PLAYER 2'S SHOP PHASE\n\nIt is round "+str(round_count)+". You will lose "+colour.RED+"1"+colour.END+" life if you lose this round.")
    else:
        print("PLAYER 2'S SHOP PHASE\n\nIt is round "+str(round_count)+". You will lose "+colour.RED+str(lives_to_lose)+colour.END+" lives if you lose this round.")
        
    if p2_lives == 1:
        print("You have "+colour.RED+"1"+colour.END+" life remaining.")
    else:
        print("You have "+colour.RED+str(p2_lives)+colour.END+" lives remaining.")
    
    if p2_coins == 1:
        print("You have "+colour.YELLOW+"1 Coin"+colour.END+".")
    else:
        print("You have "+colour.YELLOW+str(p2_coins)+" Coins"+colour.END+".")

    print("You have "+colour.PURPLE+str(p2_block)+" Block"+colour.END+". Your Block is retained between rounds, but your Health is not.\n\nYou can buy:\n")
        
    for x in range (0,len(p2_hand)):
        if p2_hand[x][0] == "Magic":  #If card is a magic card, list magic type (stored in position 5)
            print(str(x+1)+". "+str(p2_hand[x][1])+" ("+str(p2_hand[x][0])+" - "+str(p2_hand[x][5])+")")
        else:
             print(str(x+1)+". "+str(p2_hand[x][1])+" ("+str(p2_hand[x][0])+")")
    
        print("\t"+p2_hand[x][2]+"\n\n\tCoin Cost: "+colour.YELLOW+str(p2_hand[x][4])+colour.END)
    
        if not p2_hand[x][0] == "Item" and not p2_hand[x][0] == "Passive":   #Items and Passives do not have an energy cost, so only display this if its another type
            print("\tEnergy Cost: "+colour.BLUE+str(p2_hand[x][3])+colour.END)

        if p2_hand[x][0] == "Melee" or p2_hand[x][0] == "Ranged":
            print("\tDamage: "+colour.RED+str(p2_hand[x][6])+colour.END)
        elif p2_hand[x][0] == "Magic" and not p2_hand[x][5] == "Healing":
            print("\tDamage: "+colour.RED+str(p2_hand[x][6])+colour.END)
        elif p2_hand[x][0] == "Magic" and p2_hand[x][5] == "Healing":
            print("\tHealing: "+colour.GREEN+str(p2_hand[x][6])+colour.END)
        elif p2_hand[x][0] == "Item" and p2_hand[x][5] > 0:
            print("\tDamage: "+colour.RED+str(p2_hand[x][5])+colour.END)
        elif p2_hand[x][0] == "Item" and p2_hand[x][6] > 0:
            print("\tHealing: "+colour.GREEN+str(p2_hand[x][6])+colour.END)
        elif p2_hand[x][0] == "Item" and p2_hand[x][3] > 0:
            if p2_hand[x][3] == 1:
                print("\tGain "+colour.RED+"1"+colour.END+" Life")
            else:
                print("\tGain "+colour.RED+str(p2_hand[x][3])+colour.END+" Lives")
        elif p2_hand[x][0] == "Item" and p2_hand[x][7] > 0:
            print("\tGain "+colour.BLUE+str(p2_hand[x][7])+colour.END+" Energy")
        elif p2_hand[x][0] == "Defence":
            print("\tBlock: "+colour.PURPLE+str(p2_hand[x][6])+colour.END)
        elif p2_hand[x][0] == "Passive":
            if p2_hand[x][3] > 0:
                print("\tIncreases added Block by "+colour.PURPLE+str(p2_hand[x][3])+colour.END)
            if p2_hand[x][5] > 0:
                print("\tIncreases all Damage by "+colour.RED+str(p2_hand[x][5])+colour.END)
            if p2_hand[x][6] > 0:
                print("\tIncreases Coins per turn by "+colour.YELLOW+str(p2_hand[x][6])+colour.END)
            if p2_hand[x][7] > 0:
                print("\tIncreases maximum Health by "+colour.GREEN+str(p2_hand[x][7])+colour.END)

        if p2_hand[x][0] == "Melee":
            if p2_hand[x][5] > 1:
                print("\tCan be used "+colour.CYAN+str(p2_hand[x][5])+colour.END+" times per round")
            else:
                print("\tCan be used "+colour.CYAN+"once"+colour.END+" per round")
        elif p2_hand[x][0] == "Ammunition":
            print("\tAmmunition: "+colour.CYAN+str(p2_hand[x][5])+"/"+str(p2_hand[x][7])+colour.END)

        print("")

    sell = input("Type the number of the card you wish to sell. Remember that selling any card only returns "+colour.YELLOW+"1 coin"+colour.END+". If you wish to return to the buy menu, type \"b\". ")
    print("")
    if sell == "1" or sell == "2" or sell == "3" or sell == "4" or sell == "5" or sell == "6" or sell == "7":
        sell = int(sell)
        sell -= 1
        if sell <= len(p2_hand)-1:
            p2_coins += 1
            input("You have sold "+str(p2_hand[sell][1])+" and gained back "+colour.YELLOW+"1 coin"+colour.END+". ")
            p2_hand.pop(sell)
        else:   #Failsafe in case player tries to sell a card that doesnt exist
            input("There is no card "+str(sell+1)+" to sell! ")
    elif sell == "b":
        return
    else:
        input("Input not understood. ")
        
    clear()
    p2_sellcards()


###BATTLE FUNCTIONS
def p1_battle():    #Having so many global variables is yucky but I can't see any other way to get this to work, so many errors otherwise
    global p1_hand
    global p1_block
    global p1_lives
    global p1_health
    global p1_energy
    global p1_exhausted
    global p2_exhausted
    global p1_did_forfeit
    global p2_did_forfeit
    global p2_health
    global p2_block
    global p2_hand
    global damage_dealt
    
    print("PLAYER 1\t\t\t\t\t\tPLAYER 2\nLives Remaining: "+colour.RED+str(p1_lives)+colour.END+"\t\t\t\t\tLives Remaining: "+colour.RED+str(p2_lives)+colour.END+"\nHealth: "+colour.GREEN+str(p1_health)+colour.END+"\t\t\t\t\t\tHealth: "+colour.GREEN+str(p2_health)+colour.END+"\nBlock: "+colour.PURPLE+str(p1_block)+colour.END+"\t\t\t\t\t\tBlock: "+colour.PURPLE+str(p2_block)+colour.END+"\n\nEnergy Remaining: "+colour.BLUE+str(p1_energy)+colour.END+"\n\n\nYour hand is:\n")
    
    for x in range (0,len(p1_hand)):
        if p1_hand[x][0] == "Magic":  #If card is a magic card, list magic type (stored in position 5)
            print(str(x+1)+". "+str(p1_hand[x][1])+" ("+str(p1_hand[x][0])+" - "+str(p1_hand[x][5])+")")
        else:
            print(str(x+1)+". "+str(p1_hand[x][1])+" ("+str(p1_hand[x][0])+")")
        
        if not (p1_hand[x][0] == "Item" or p1_hand[x][0] == "Passive"):   #Items and Passives do not have an energy cost, so only display this if its another type
            print("\tEnergy Cost: "+colour.BLUE+str(p1_hand[x][3])+colour.END)

        if p1_hand[x][0] == "Melee" or p1_hand[x][0] == "Ranged":
            print("\tDamage: "+colour.RED+str(p1_hand[x][6])+colour.END)
        elif p1_hand[x][0] == "Magic" and not p1_hand[x][5] == "Healing":
            print("\tDamage: "+colour.RED+str(p1_hand[x][6])+colour.END)
        elif p1_hand[x][0] == "Magic" and p1_hand[x][5] == "Healing":
            print("\tHealing: "+colour.GREEN+str(p1_hand[x][6])+colour.END)
        elif p1_hand[x][0] == "Item" and p1_hand[x][5] > 0:
            print("\tDamage: "+colour.RED+str(p1_hand[x][5])+colour.END)
        elif p1_hand[x][0] == "Item" and p1_hand[x][6] > 0:
            print("\tHealing: "+colour.GREEN+str(p1_hand[x][6])+colour.END)
        elif p1_hand[x][0] == "Item" and p1_hand[x][3] > 0:
            if p1_hand[x][3] == 1:
                print("\tGain "+colour.RED+"1"+colour.END+" Life")
            else:
                print("\tGain "+colour.RED+str(p1_hand[x][3])+colour.END+" Lives")
        elif p1_hand[x][0] == "Item" and p1_hand[x][7] > 0:
            print("\tGain "+colour.BLUE+str(p1_hand[x][7])+colour.END+" Energy")
        elif p1_hand[x][0] == "Defence":
            print("\tBlock: "+colour.PURPLE+str(p1_hand[x][6])+colour.END)
        elif p1_hand[x][0] == "Passive":
            if p1_hand[x][3] > 0:
                print("\tIncreases added Block by "+colour.PURPLE+str(p1_hand[x][3])+colour.END)
            if p1_hand[x][5] > 0:
                print("\tIncreases all Damage by "+colour.RED+str(p1_hand[x][5])+colour.END)
            if p1_hand[x][6] > 0:
                print("\tIncreases Coins per turn by "+colour.YELLOW+str(p1_hand[x][6])+colour.END)
            if p1_hand[x][7] > 0:
                print("\tIncreases maximum Health by "+colour.GREEN+str(p1_hand[x][7])+colour.END)
        
        if p1_hand[x][0] == "Melee":
            print("\tUses this round: "+colour.CYAN+str(p1_hand[x][5])+"/"+str(p1_hand[x][7])+colour.END)
        elif p1_hand[x][0] == "Ranged":
            print("\tAmmunition: "+colour.CYAN+str(p1_hand[x][5])+"/"+str(p1_hand[x][7])+colour.END)

        print("")

    #Actual battle functions can only occur if the player has any cards left that they can still use
    if (any(x[0] == "Melee" and x[5] > 0 for x in p1_hand) or "Defence" in [x[0] for x in p1_hand] or "Ranged" in [x[0] for x in p1_hand] or any(x[0] == "Item" and x[7] == 0 for x in p1_hand) or any(x[0] == "Magic" for x in p1_hand)) and p1_exhausted == 0:
        if p2_exhausted == 0:
            turn = input("Type the number of the card you wish to play. Keep in mind that Passive cards are not playable in rounds.\nTo end your round early, type \"f\". To end your turn and hand control to the other player, type \"n\". ")
        else:
            turn = input("Type the number of the card you wish to play. Keep in mind that Passive cards are not playable in rounds.\nTo end your round early, type \"f\". The other player has ended their round, so ending now will result in victory as long as you have the highest health.\nTo end your turn and hand control to the other player, type \"n\". ")
        print("")
        if turn == "1" or turn == "2" or turn == "3" or turn == "4" or turn == "5" or turn == "6" or turn == "7":
            turn = int(turn)
            turn -= 1
            if turn <= len(p1_hand)-1:
                if p1_hand[turn][0] == "Passive":    #In case player tries to play a passive
                    input("Passive cards cannot be played in rounds! ")
                else:
                    if not p1_hand[turn][0] == "Item" and p1_hand[turn][3] > p1_energy:
                        input("You do not have enough Energy to play this card! ")
                    else:
                        #Playing a Defence card to add Block
                        if p1_hand[turn][0] == "Defence":
                            for x in range (0,len(p1_hand)):    #Add block boosts from passive cards to added block if they exist
                                if p1_hand[x][0] == "Passive" and p1_hand[x][3] > 0:
                                    p1_hand[turn][6] += p1_hand[x][3]
                            input("Your Block has been increased by "+colour.PURPLE+str(p1_hand[turn][6])+colour.END+".\n"+p1_hand[turn][1]+" has been consumed. ")
                            p1_block += p1_hand[turn][6]
                            p1_energy -= p1_hand[turn][3]
                            p1_hand.pop(turn)

                        #Playing an Item card for any of the following effects:
                        #[x][3] = Lives
                        #[x][5] = Damage
                        #[x][6] = Healing
                        #[x][7] = Energy
                        elif p1_hand[turn][0] == "Item":
                            if p1_hand[turn][3] > 0: #Adding Lives
                                p1_lives += p1_hand[turn][3]
                                input("Your Lives count has been increased by "+colour.RED+str(p1_hand[turn][3])+colour.END+".\n"+p1_hand[turn][1]+" has been consumed. ")
                            elif p1_hand[turn][5] > 0: #Dealing Damage
                                p1_hurts_p2(p1_hand[turn][5])
                                input("You have inflicted "+colour.RED+str(damage_dealt)+colour.END+" damage onto the enemy.\n"+p1_hand[turn][1]+" has been consumed. ")
                            elif p1_hand[turn][6] > 0: #Healing
                                p1_health += p1_hand[turn][6]
                                input("Your Health has been increased by "+colour.GREEN+str(p1_hand[turn][6])+colour.END+".\n"+p1_hand[turn][1]+" has been consumed. ")
                            elif p1_hand[turn][7] > 0: #Adding Energy
                                p1_energy += p1_hand[turn][7]
                                input("Your Energy has been increased by "+colour.BLUE+str(p1_hand[turn][7])+colour.END+".\n"+p1_hand[turn][1]+" has been consumed. ")
                            p1_hand.pop(turn)

                        #Playing a Magic card to either deal damage or heal
                        elif p1_hand[turn][0] == "Magic":
                            if p1_hand[turn][5] == "Healing":    #Add health if healing magic
                                p1_health += p1_hand[turn][6]
                                input("Your Health has been increased by "+colour.GREEN+str(p1_hand[turn][6])+colour.END+".\n"+p1_hand[turn][1]+" has been consumed. ")
                            else:   #Deal damage if plasma or shadow magic
                                p1_hurts_p2(p1_hand[turn][6])
                                input("You have inflicted "+colour.RED+str(damage_dealt)+colour.END+" damage onto the enemy.\n"+p1_hand[turn][1]+" has been consumed. ")
                            p1_energy -= p1_hand[turn][3]
                            p1_hand.pop(turn)

                        #Playing a Melee card to deal damage, uses round use limits rather than being removed on use
                        elif p1_hand[turn][0] == "Melee":
                            if p1_hand[turn][5] > 0:
                                p1_hurts_p2(p1_hand[turn][6])
                                p1_energy -= p1_hand[turn][3]
                                p1_hand[turn][5] -= 1    #Uses remaining - for some BIZARRE reason this reduces the use limit on identical melee cards???? why??????????
                                if p1_hand[turn][5] == 1:
                                    input("You have inflicted "+colour.RED+str(damage_dealt)+colour.END+" damage onto the enemy.\n"+p1_hand[turn][1]+" has "+colour.CYAN+"1"+colour.END+" use remaining this round. ")
                                else:
                                    input("You have inflicted "+colour.RED+str(damage_dealt)+colour.END+" damage onto the enemy.\n"+p1_hand[turn][1]+" has "+colour.CYAN+str(p1_hand[turn][5])+colour.END+" uses remaining this round. ")
                            else:
                                input("This card has exhausted its use limit this round and cannot be played again until the next round! ")

                        #Playing a Ranged card to deal damage, uses ammunition and is removed on consuming all ammo
                        elif p1_hand[turn][0] == "Ranged":
                            p1_hurts_p2(p1_hand[turn][6])
                            p1_energy -= p1_hand[turn][3]
                            p1_hand[turn][5] -= 1 #Ammo
                            if p1_hand[turn][5] == 0:
                                input("You have inflicted "+colour.RED+str(damage_dealt)+colour.END+" damage onto the enemy.\n"+p1_hand[turn][1]+" has no remaining ammunition and has been consumed. ")
                                p1_hand.pop(turn)
                            else:
                                input("You have inflicted "+colour.RED+str(damage_dealt)+colour.END+" damage onto the enemy.\n"+p1_hand[turn][1]+" has "+colour.CYAN+str(p1_hand[turn][5])+colour.END+" ammunition remaining ")
                        
            else:   #Failsafe in case player tries to play a card that doesnt exist
                input("There is no card "+str(turn+1)+" to play! ")
        elif turn == "n":
            clear()
            input("\nNow ending player 1's turn. Player 2, please take the seat. ") #Show a different message when playing against AI
            return
        elif turn == "f":
            clear()
            p1_exhausted = 1
            p1_did_forfeit = 1
            input("\nNow ending player 1's turn. Player 2, please take the seat. ") #Show a different message when playing against AI
            return
        else:
            input("Input not understood. ")

    else:   #Auto-end turn if player has no useful cards remaining, and set exhausted value to 1 (round ends if both players have exhausted all damage options)
        if p1_did_forfeit == 0:
            p1_exhausted = 1
            input("You have no usable cards remaining that are not energy boosters, and therefore you cannot act until the next round. ")
        else:
            input("You have ended your round early, and so cannot take any actions until the next round. ")
        clear()
        input("\nNow ending player 1's turn. Player 2, please take the seat. ") #Show a different message when playing against AI
        return

    clear()
    p1_battle()


def p2_battle():
    global p2_hand
    global p2_block
    global p2_lives
    global p2_health
    global p2_energy
    global p1_exhausted
    global p2_exhausted
    global p1_did_forfeit
    global p2_did_forfeit
    global p1_health
    global p1_block
    global p1_hand
    global damage_dealt
    
    print("PLAYER 2\t\t\t\t\t\tPLAYER 1\nLives Remaining: "+colour.RED+str(p2_lives)+colour.END+"\t\t\t\t\tLives Remaining: "+colour.RED+str(p1_lives)+colour.END+"\nHealth: "+colour.GREEN+str(p2_health)+colour.END+"\t\t\t\t\t\tHealth: "+colour.GREEN+str(p1_health)+colour.END+"\nBlock: "+colour.PURPLE+str(p2_block)+colour.END+"\t\t\t\t\t\tBlock: "+colour.PURPLE+str(p1_block)+colour.END+"\n\nEnergy Remaining: "+colour.BLUE+str(p2_energy)+colour.END+"\n\n\nYour hand is:\n")
    
    for x in range (0,len(p2_hand)):
        if p2_hand[x][0] == "Magic":  #If card is a magic card, list magic type (stored in position 5)
            print(str(x+1)+". "+str(p2_hand[x][1])+" ("+str(p2_hand[x][0])+" - "+str(p2_hand[x][5])+")")
        else:
            print(str(x+1)+". "+str(p2_hand[x][1])+" ("+str(p2_hand[x][0])+")")
        
        if not (p2_hand[x][0] == "Item" or p2_hand[x][0] == "Passive"):   #Items and Passives do not have an energy cost, so only display this if its another type
            print("\tEnergy Cost: "+colour.BLUE+str(p2_hand[x][3])+colour.END)

        if p2_hand[x][0] == "Melee" or p2_hand[x][0] == "Ranged":
            print("\tDamage: "+colour.RED+str(p2_hand[x][6])+colour.END)
        elif p2_hand[x][0] == "Magic" and not p2_hand[x][5] == "Healing":
            print("\tDamage: "+colour.RED+str(p2_hand[x][6])+colour.END)
        elif p2_hand[x][0] == "Magic" and p2_hand[x][5] == "Healing":
            print("\tHealing: "+colour.GREEN+str(p2_hand[x][6])+colour.END)
        elif p2_hand[x][0] == "Item" and p2_hand[x][5] > 0:
            print("\tDamage: "+colour.RED+str(p2_hand[x][5])+colour.END)
        elif p2_hand[x][0] == "Item" and p2_hand[x][6] > 0:
            print("\tHealing: "+colour.GREEN+str(p2_hand[x][6])+colour.END)
        elif p2_hand[x][0] == "Item" and p2_hand[x][3] > 0:
            if p2_hand[x][3] == 1:
                print("\tGain "+colour.RED+"1"+colour.END+" Life")
            else:
                print("\tGain "+colour.RED+str(p2_hand[x][3])+colour.END+" Lives")
        elif p2_hand[x][0] == "Item" and p2_hand[x][7] > 0:
            print("\tGain "+colour.BLUE+str(p2_hand[x][7])+colour.END+" Energy")
        elif p2_hand[x][0] == "Defence":
            print("\tBlock: "+colour.PURPLE+str(p2_hand[x][6])+colour.END)
        elif p2_hand[x][0] == "Passive":
            if p2_hand[x][3] > 0:
                print("\tIncreases added Block by "+colour.PURPLE+str(p2_hand[x][3])+colour.END)
            if p2_hand[x][5] > 0:
                print("\tIncreases all Damage by "+colour.RED+str(p2_hand[x][5])+colour.END)
            if p2_hand[x][6] > 0:
                print("\tIncreases Coins per turn by "+colour.YELLOW+str(p2_hand[x][6])+colour.END)
            if p2_hand[x][7] > 0:
                print("\tIncreases maximum Health by "+colour.GREEN+str(p2_hand[x][7])+colour.END)
        
        if p2_hand[x][0] == "Melee":
            print("\tUses this round: "+colour.CYAN+str(p2_hand[x][5])+"/"+str(p2_hand[x][7])+colour.END)
        elif p2_hand[x][0] == "Ranged":
            print("\tAmmunition: "+colour.CYAN+str(p2_hand[x][5])+"/"+str(p2_hand[x][7])+colour.END)

        print("")

    #Actual battle functions can only occur if the player has any usable damage-dealing cards remaining
    if (any(x[0] == "Melee" and x[5] > 0 for x in p2_hand) or "Defence" in [x[0] for x in p1_hand] or "Ranged" in [x[0] for x in p2_hand] or any(x[0] == "Item" and x[7] == 0 for x in p2_hand) or any(x[0] == "Magic" for x in p2_hand)) and p2_exhausted == 0:
        if p1_exhausted == 0:
            turn = input("Type the number of the card you wish to play. Keep in mind that Passive cards are not playable in rounds.\nTo end your round early, type \"f\". To end your turn and hand control to the other player, type \"n\". ")
        else:
            turn = input("Type the number of the card you wish to play. Keep in mind that Passive cards are not playable in rounds.\nTo end your round early, type \"f\". The other player has ended their round, so ending now will result in victory as long as you have the highest health.\nTo end your turn and hand control to the other player, type \"n\". ")
        print("")
        if turn == "1" or turn == "2" or turn == "3" or turn == "4" or turn == "5" or turn == "6" or turn == "7":
            turn = int(turn)
            turn -= 1
            if turn <= len(p2_hand)-1:
                if p2_hand[turn][0] == "Passive":    #In case player tries to play a passive
                    input("Passive cards cannot be played in rounds! ")
                else:
                    if not p2_hand[turn][0] == "Item" and p2_hand[turn][3] > p2_energy:
                        input("You do not have enough Energy to play this card! ")
                    else:
                        #Playing a Defence card to add Block
                        if p2_hand[turn][0] == "Defence":
                            for x in range (0,len(p2_hand)):    #Add block boosts from passive cards to added block if they exist
                                if p2_hand[x][0] == "Passive" and p2_hand[x][3] > 0:
                                    p2_hand[turn][6] += p2_hand[x][3]
                            input("Your Block has been increased by "+colour.PURPLE+str(p2_hand[turn][6])+colour.END+".\n"+p2_hand[turn][1]+" has been consumed. ")
                            p2_block += p2_hand[turn][6]
                            p2_energy -= p2_hand[turn][3]
                            p2_hand.pop(turn)

                        #Playing an Item card for any of the following effects:
                        #[x][3] = Lives
                        #[x][5] = Damage
                        #[x][6] = Healing
                        #[x][7] = Energy
                        elif p2_hand[turn][0] == "Item":
                            if p2_hand[turn][3] > 0: #Adding Lives
                                p2_lives += p2_hand[turn][3]
                                input("Your Lives count has been increased by "+colour.RED+str(p2_hand[turn][3])+colour.END+".\n"+p2_hand[turn][1]+" has been consumed. ")
                            elif p2_hand[turn][5] > 0: #Dealing Damage
                                p2_hurts_p1(p2_hand[turn][5])
                                input("You have inflicted "+colour.RED+str(damage_dealt)+colour.END+" damage onto the enemy.\n"+p2_hand[turn][1]+" has been consumed. ")
                            elif p2_hand[turn][6] > 0: #Healing
                                p2_health += p2_hand[turn][6]
                                input("Your Health has been increased by "+colour.GREEN+str(p2_hand[turn][6])+colour.END+".\n"+p2_hand[turn][1]+" has been consumed. ")
                            elif p2_hand[turn][7] > 0: #Adding Energy
                                p2_energy += p2_hand[turn][7]
                                input("Your Energy has been increased by "+colour.BLUE+str(p2_hand[turn][7])+colour.END+".\n"+p2_hand[turn][1]+" has been consumed. ")
                            p2_hand.pop(turn)

                        #Playing a Magic card to either deal damage or heal
                        elif p2_hand[turn][0] == "Magic":
                            if p2_hand[turn][5] == "Healing":    #Add health if healing magic
                                p2_health += p2_hand[turn][6]
                                input("Your Health has been increased by "+colour.GREEN+str(p2_hand[turn][6])+colour.END+".\n"+p2_hand[turn][1]+" has been consumed. ")
                            else:   #Deal damage if plasma or shadow magic
                                p2_hurts_p1(p2_hand[turn][6])
                                input("You have inflicted "+colour.RED+str(p2_hand[turn][6])+colour.END+" damage onto the enemy.\n"+p2_hand[turn][1]+" has been consumed. ")
                            p2_energy -= p2_hand[turn][3]
                            p2_hand.pop(turn)

                        #Playing a Melee card to deal damage, uses round use limits rather than being removed on use
                        elif p2_hand[turn][0] == "Melee":
                            if p2_hand[turn][5] > 0:
                                p2_hurts_p1(p2_hand[turn][6])
                                p2_energy -= p2_hand[turn][3]
                                p2_hand[turn][5] -= 1    #Uses remaining
                                if p2_hand[turn][5] == 1:
                                    input("You have inflicted "+colour.RED+str(damage_dealt)+colour.END+" damage onto the enemy.\n"+p2_hand[turn][1]+" has "+colour.CYAN+"1"+colour.END+" use remaining this round. ")
                                else:
                                    input("You have inflicted "+colour.RED+str(damage_dealt)+colour.END+" damage onto the enemy.\n"+p2_hand[turn][1]+" has "+colour.CYAN+str(p2_hand[turn][5])+colour.END+" uses remaining this round. ")
                            else:
                                input("This card has exhausted its use limit this round and cannot be played again until the next round! ")

                        #Playing a Ranged card to deal damage, uses ammunition and is removed on consuming all ammo
                        elif p2_hand[turn][0] == "Ranged":
                            p2_hurts_p1(p2_hand[turn][6])
                            p2_energy -= p2_hand[turn][3]
                            p2_hand[turn][5] -= 1 #Ammo
                            if p2_hand[turn][5] == 0:
                                input("You have inflicted "+colour.RED+str(damage_dealt)+colour.END+" damage onto the enemy.\n"+p2_hand[turn][1]+" has no remaining ammunition and has been consumed. ")
                                p2_hand.pop(turn)
                            else:
                                input("You have inflicted "+colour.RED+str(damage_dealt)+colour.END+" damage onto the enemy.\n"+p2_hand[turn][1]+" has "+colour.CYAN+str(p2_hand[turn][5])+colour.END+" ammunition remaining ")
                        
            else:   #Failsafe in case player tries to play a card that doesnt exist
                input("There is no card "+str(turn+1)+" to play! ")
        elif turn == "n":
            clear()
            input("\nNow ending player 2's turn. Player 1, please take the seat. ") #Show a different message when playing against AI
            return
        elif turn == "f":
            clear()
            p2_exhausted = 1
            p2_did_forfeit = 1
            input("\nNow ending player 2's turn. Player 1, please take the seat. ") #Show a different message when playing against AI
            return
        else:
            input("Input not understood. ")

    else:   #Auto-end turn if player has no damage-dealing cards remaining, and set exhausted value to 1 (round ends if both players have exhausted all damage options)
        if p2_did_forfeit == 0:
            p2_exhausted = 1
            input("You have no usable cards remaining that are not energy boosters, and therefore you cannot act until the next round. ")
        else:
            input("You have ended your round early, and so cannot take any actions until the next round. ")
        clear()
        input("\nNow ending player 2's turn. Player 1, please take the seat. ") #Show a different message when playing against AI
        return

    clear()
    p2_battle()


def p1_hurts_p2(p1_dmg):    #This goes into a function so I don't have to repeat the code over and over for every instance of dealing damage
    global p2_block
    global p2_health
    global damage_dealt
    global p1_hand
    
    for x in range (0,len(p1_hand)):    #Add damage boosts if they exist
        if p1_hand[x][0] == "Passive" and p1_hand[x][5] > 0:
            p1_dmg += p1_hand[x][5]

    damage_dealt = p1_dmg
            
    if p2_block >= p1_dmg:  #If p2's block can fully absorb damage, simply remove damage from p2's block
        p2_block -= p1_dmg
    else:
        p1_dmg -= p2_block  #If damage will punch through p2's block, then reduce damage by p2's block, set p2's block to zero, and reduce p2's health by remaining damage
        p2_block = 0
        p2_health -= p1_dmg

def p2_hurts_p1(p2_dmg):    #Same as above but players swapped
    global p1_block
    global p1_health
    global damage_dealt
    global p2_hand
    
    for x in range (0,len(p2_hand)):    #Add damage boosts if they exist
        if p2_hand[x][0] == "Passive" and p2_hand[x][5] > 0:
            p2_dmg += p2_hand[x][5]

    damage_dealt = p2_dmg
        
    if p1_block >= p2_dmg:
        p1_block -= p2_dmg
    else:
        p2_dmg -= p1_block
        p1_block = 0
        p1_health -= p2_dmg


###GAME START

input("Welcome to the digital version of the card game Cavien's Arena. The functionality to play vs AI is not yet finished, so currently only hotseat multiplayer is available.\n")
clear()
input("Currently the functionality to play different characters is unavailable. Both players will be a standard Elf capable of plasma, shield and healing magic.\n")
clear()
while p1_lives > 0 and p2_lives > 0:
    play_round()
