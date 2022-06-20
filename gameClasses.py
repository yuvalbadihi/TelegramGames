import json
import time
import threading

LOCAL_CONFIGURATION_FILE = "configuration.json"
with open(LOCAL_CONFIGURATION_FILE) as local_config_file:
    local_config = json.load(local_config_file)
database_file = local_config["Details"]["database_file"]

threads = []
sem = threading.Semaphore()
basic_cooldown = 3600
basic_pickaxe = 100



def Lock():
    sem.acquire()


def UnLock():
    sem.release()


class Player:
    def __init__(self, user_id, firstname):
        self.user_id = user_id
        self.firstname = firstname

    def line(self, wb, ws):
        Lock()
        j = 1
        line = 0
        for i in ws:
            if self.user_id == ws['A' + str(j)].value:
                line = j
            j += 1

        if line == 0:
            ws.append([self.user_id])
            line = j
            ws['A' + str(j)].value = self.user_id
            ws['C' + str(j)].value = 0

        wb.save(database_file)
        UnLock()
        return line

    def withdrawal_addy(self, wb, ws):
        coins = self.line(wb, ws)
        Lock()
        with_addy = ws['B' + str(coins)].value
        UnLock()
        return with_addy

    def set_withdrawal_addy(self, addy, wb, ws):
        coins = self.line(wb, ws)
        Lock()
        if len(addy) < 50:
            ws['B' + str(coins)].value = addy
            wb.save(database_file)
            UnLock()
            return True
        UnLock()
        return False

    def set_fm_tag(self, addy, wb, ws):
        coins = self.line(wb, ws)
        Lock()
        if len(addy) < 50 and addy[0] == "@":
            ws['E' + str(coins)].value = addy
            ws['F' + str(coins)].value = 0
            wb.save(database_file)
            UnLock()
            return True
        wb.save(database_file)
        UnLock()
        return False

    def set_fm_boost(self, boost, wb, ws):  # ADD LOCKS TAKE CARE FROM DEADLOCKS
        coins = self.line(wb, ws)
        boost = int(boost)
        if ws['E' + str(coins)].value != None and int(self.chips(wb, ws)) >= boost:
            self.reduce_chips(wb, ws, boost)
            ws['F' + str(coins)] = ws['F' + str(coins)].value + boost
            wb.save(database_file)
            return True
        return False

    def getFM(self, wb, ws):
        coins = self.line(wb, ws)
        Lock()
        if ws['E' + str(coins)].value != None:
            UnLock()
            return ws['E' + str(coins)].value
        UnLock()

    def getFMRank(self, wb, ws):
        coins = self.line(wb, ws)
        Lock()
        if ws['F' + str(coins)].value != None:
            UnLock()
            return ws['F' + str(coins)].value
        UnLock()

    def addy(self, wb, ws):
        coins = self.line(wb, ws)
        Lock()
        addy = ws['A' + str(coins)].value
        wb.save(database_file)
        UnLock()
        return addy

    def chips(self, wb, ws):
        coins = self.line(wb, ws)
        Lock()
        user_coins = ws['C' + str(coins)].value
        UnLock()
        return int(user_coins)

    def increase_chips(self, wb, ws, amount):
        line = self.line(wb, ws)
        Lock()
        ws['C' + str(line)].value += amount
        wb.save(database_file)
        UnLock()
        return True

    def reduce_chips(self, wb, ws, amount):
        line = self.line(wb, ws)
        Lock()
        ws['C' + str(line)].value -= amount
        wb.save(database_file)
        UnLock()
        return True

    def check_mine_time(self, wb, ws,letter):
        line = self.line(wb, ws)
        Lock()
        if ws[letter + str(line)].value == None:
            UnLock()
            return time.time() - 1
        UnLock()
        return ws[letter + str(line)].value

    def mine(self, current_time, wb, ws):
        line = self.line(wb, ws)
        added_time = basic_cooldown * self.get_mine_val(wb, ws, 'G')
        added_amount = basic_pickaxe * self.get_mine_val(wb, ws, 'H')
        Lock()
        ws['D' + str(line)].value = time.time() + added_time
        ws['C' + str(line)].value += added_amount
        wb.save(database_file)
        UnLock()
        return int(added_amount)

    def get_mine_val(self,wb,ws,letter):
        line = self.line(wb, ws)
        Lock()
        if ws[letter + str(line)].value == None:
            UnLock()
            return 1
        UnLock()
        return float(ws[letter + str(line)].value)

    def get_improve_price(self,wb,ws,letter):
        current_val = self.get_mine_val(wb, ws, letter)
        offset = (100-current_val*100)*(100 - current_val*100)
        return offset

    def improve_item(self,wb,ws,letter,change):
        line = self.line(wb, ws)
        new_val = self.get_mine_val(wb, ws, letter) * change
        Lock()
        ws[letter + str(line)].value = new_val
        wb.save(database_file)
        UnLock()
        return True


    def get_fame(self,wb,ws,change,famer_id,famer_firstname,stat,famer_username):
        line = self.line(wb, ws)
        self.add_history(wb, ws, famer_id, famer_firstname, stat,famer_username)
        Lock()
        if ws['I' + str(line)].value == None:
            ws['I' + str(line)].value = change
            UnLock()
            wb.save(database_file)
            return ws['I' + str(line)].value
        else:
            ws['I' + str(line)].value = int(ws['I' + str(line)].value) + change
            UnLock()
            wb.save(database_file)
            return ws['I' + str(line)].value

    def get_value_or_zero(self, wb, ws, letter):
        line = self.line(wb, ws)
        Lock()
        if ws[letter + str(line)].value == None:
            UnLock()
            return 0
        UnLock()
        return ws[letter + str(line)].value


    def fame_someone(self,wb,ws,player_to_fame,change,my_username):
        timeout_fame = int(self.check_mine_time(wb, ws,'J'))
        my_line = self.line(wb, ws)
        offset = 7200 # 2 hours
        if change == 1:
            thestat = 'fame'
        else:
            thestat = 'defame'
        if time.time() > timeout_fame:
            player_to_fame.get_fame(wb,ws,change,self.user_id,self.firstname,thestat,my_username)
            Lock()
            ws['J' + str(my_line)].value = time.time() + offset
            UnLock()
            wb.save(database_file)
            return True

        elif time.time() < timeout_fame:
            timeleft = int(timeout_fame - time.time())
            minsleft = timeleft // 60
            UnLock()
            wb.save(database_file)
            return minsleft

    def set_new_shop(self, addy, wb, ws):
        line = self.line(wb, ws)
        Lock()
        if len(addy) < 200:
            ws['K' + str(line)].value = addy
            wb.save(database_file)
            UnLock()
            return True
        UnLock()
        return False

    def get_a_value(self,wb,ws,letter):
        line = self.line(wb, ws)
        return ws[letter + str(line)].value

    def show_history(self,wb,ws):
        history = self.get_a_value(wb,ws,'L')
        if history == None:
            return "This user have no history"
        return history

    def add_history(self, wb, ws,famer_id,famer_firstname,stat,famer_usename):
        line = self.line(wb, ws)
        history = self.show_history(wb,ws)
        if len(history) > 32000:
            print('TO LONG HISTORY HANDLE IT')
            return 0
        Lock()
        if history == "This user have no history":
            ws['L' + str(line)].value = f'📜 {self.firstname} 𝗛𝗶𝘀𝘁𝗼𝗿𝘆\n\n𝙽𝚊𝚖𝚎: {famer_firstname}\n𝚄𝚜𝚎𝚛𝚗𝚊𝚖𝚎: {famer_usename}\n𝙸𝙳: FM{famer_id}\n𝙰𝚌𝚝𝚒𝚘𝚗: {stat}\n\n'
            UnLock()
            return True
        ws['L' + str(line)].value = history + f'𝙽𝚊𝚖𝚎: {famer_firstname}\n𝚄𝚜𝚎𝚛𝚗𝚊𝚖𝚎: {famer_usename}\n𝙸𝙳: FM{famer_id}\n𝙰𝚌𝚝𝚒𝚘𝚗: {stat}\n\n'
        UnLock()
        return True





class NewGame:
    def __init__(self, message_id, chat_id, player1_id, amount, inline_message_id, player1_firstname, player2_firstname,
                 player2_id):
        self.player1_id = player1_id
        self.player1_firstname = player1_firstname

        self.player2_id = player2_id
        self.player2_firstname = player2_firstname

        self.message_id = message_id
        self.chat_id = chat_id
        self.amount = amount
        self.inline_message_id = inline_message_id

    def change_chips(self, new_amount, call_back_id, wb, ws, currency_symbol, bot_username, badi_bot, currency):
        # LOCK
        player1 = Player(self.player1_id, self.player1_firstname)
        player1_chips = player1.chips(wb, ws)
        if new_amount >= 0 and new_amount + self.amount <= player1_chips:
            button_dices = {"inline_keyboard": [[{"text": '🕹️ Join Match', "callback_data": 'join_dices'},
                                                 {"text": '🎲 Start', "callback_data": 'start_dices'}],
                                                [{"text": f'1 {currency_symbol}', "callback_data": 'add_1_chip'},
                                                 {"text": f'2 {currency_symbol}', "callback_data": 'add_2_chip'},
                                                 {"text": f'4 {currency_symbol}', "callback_data": 'add_4_chip'},
                                                 {"text": f'8 {currency_symbol}', "callback_data": 'add_8_chip'},
                                                 {"text": f'16 {currency_symbol}', "callback_data": 'add_16_chip'}]]}
            button_dices = json.dumps(button_dices)  # "resize_inline_keyboard": True ,
            self.amount += new_amount
            self.player2_id = None
            self.player2_firstname = None
            badi_bot.edit_message_inline_id(self.inline_message_id,
                                            f'Hey, I would like to play dices with you on \n{self.amount} {currency}.',
                                            button_dices)

        elif new_amount + self.amount > player1_chips:
            badi_bot.awnser_call_back_alert(call_back_id,
                                            f'❌ Unfortunately you do not have enough {currency} to complete this operation,\nMake sure to buy {currency} through {bot_username} before trying again.')
        # UNLOCK
        return True

    # def play
    # def wait for another player


class NewSlotsGame:
    def __init__(self, message_id, chat_id, player1_id, amount, inline_message_id, player1_firstname):
        self.player1_id = player1_id
        self.player1_firstname = player1_firstname
        self.message_id = message_id
        self.chat_id = chat_id
        self.amount = amount
        self.inline_message_id = inline_message_id
        self.limit = 0
        self.lock = 0

    def change_chips(self, new_amount, call_back_id, wb, ws, currency_symbol, bot_username, badi_bot, currency):
        # LOCK ??
        player1 = Player(self.player1_id, self.player1_firstname)
        player1_chips = player1.chips(wb, ws)
        if new_amount >= 0 and new_amount + self.amount <= player1_chips:
            button_slots = {"inline_keyboard": [[{"text": '📍 Spin', "callback_data": 'spin_now'}],
                                                [{"text": f'1 {currency_symbol}', "callback_data": 'add-1-chip'},
                                                 {"text": f'2 {currency_symbol}', "callback_data": 'add-2-chip'},
                                                 {"text": f'4 {currency_symbol}', "callback_data": 'add-4-chip'},
                                                 {"text": f'8 {currency_symbol}', "callback_data": 'add-8-chip'},
                                                 {"text": f'16 {currency_symbol}', "callback_data": 'add-16-chip'}]]}
            button_slots = json.dumps(button_slots)
            self.amount += new_amount
            badi_bot.edit_message_inline_id(self.inline_message_id,
                                            f"🎰 If you’re looking for a thrill, then you better take chances on playing a 3-reel slot game!\n\n𝗠𝘂𝗹𝘁𝗶𝗽𝗹𝗶𝗲𝗿: {self.amount}",
                                            button_slots)

        elif new_amount + self.amount > player1_chips:
            badi_bot.awnser_call_back_alert(call_back_id,
                                            f'❌ Unfortunately you do not have enough {currency} to complete this operation,\nMake sure to mine {currency} through {bot_username} before trying again.')
        # UNLOCK ??
        return True


class a_fm_instance:
    def __init__(self, addy, rank):
        self.addy = addy
        self.rank = rank


