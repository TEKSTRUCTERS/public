import websocket
import json
import threading
import time

class BillAcceptor:
    def __init__(self):
        self.is_inited = False
        self.cassette_inserted = True
        self.is_disabled = False
        self.allow_amount = []
        self.device_id = '0'
        self.url = 'ws://localhost:8083/'
        self.ws = None
        self.events = {}
        self.errors = {}

    def reset_events(self):
        self.events = {
            'INITIALIZED': lambda: print('Initialized'),
            'IDLING': lambda: print('Idling'),
            'READY_TO_ACCEPT': lambda: print('Ready to accept'),
            'REJECTING': lambda: print('Rejecting'),
            'ACCEPTING': lambda: print('Accepting'),
            'STACKING': lambda: print('Stacking'),
            'STACKED': lambda amount: print('Stacked:', amount),
            'PAUSED': lambda: print('Paused'),
            'CASHBOX_INSERTED': lambda: print('Cashbox inserted'),
            'CASHBOX_OUT': lambda: print('Cashbox out')
        }

    def reset_errors(self):
        self.errors = {
            'CASHBOX_FULL': lambda: print('Cashbox full'),
            'VALIDATOR_JAMMED': lambda: print('Validator jammed'),
            'CASHBOX_JAMMED': lambda: print('Cashbox jammed'),
            'FAILURE': lambda: print('Failure'),
            'PAUSED': lambda: print('Paused'),
            'CHEATED': lambda: print('Cheated'),
            'DEVICE_NOT_FOUND': lambda: print('Device not found')
        }

    def on_message(self, ws, message):
        print('WS Message:', message)
        msg = json.loads(message)
        self.proceed(msg)

    def on_open(self, ws):
        print('WS Opened')
        self.inited()

    def on_error(self, ws, error):
        print('WS Error')

    def init(self):
        self.reset_events()
        self.reset_errors()
        self.ws = websocket.WebSocketApp(self.url, on_message=self.on_message, on_open=self.on_open, on_error=self.on_error)
        threading.Thread(target=self.ws.run_forever).start()

    def inited(self):
        self.is_inited = True

    def command(self, command, params=None):
        o = {
            'device_type': 'bill_acceptor',
            'method': command,
            'device': self.device_id
        }
        if params:
            o['data'] = params

        self.ws.send(json.dumps(o))

    def reset(self):
        if not self.is_inited:
            return
        self.command('cmd_reset')

    def start_accepting(self):
        if not self.is_inited:
            return
        self.command('cmd_start_accepting', self.allow_amount)

    def stop_accepting(self):
        if not self.is_inited:
            return
        self.command('cmd_stop_accepting')

    def proceed(self, msg):
        print(msg)
        if 'event' in msg:
            event = msg['event']
            if event == 'IDLING':
                self.is_disabled = True
                self.cassette_inserted = True
            else:
                self.is_disabled = False

            if event == 'CASHBOX_INSERTED':
                self.cassette_inserted = True

            if event == 'CASHBOX_OUT':
                self.cassette_inserted = False

            if event in self.events:
                if 'data' in msg:
                    self.events[event](msg['data'])
                else:
                    self.events[event]()

        if 'error' in msg:
            error = msg['error']
            if error in self.errors:
                if 'data' in msg:
                    self.errors[error](msg['data'])
                else:
                    self.errors[error]()

if __name__ == '__main__':
    bill_acceptor = BillAcceptor()
    bill_acceptor.init()

    # Example usage
    time.sleep(1)  # Wait for WebSocket connection to establish
    bill_acceptor.start_accepting()
    time.sleep(5)  # Wait for 5 seconds
    bill_acceptor.stop_accepting()
    bill_acceptor.reset()
