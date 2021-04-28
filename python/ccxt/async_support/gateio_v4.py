# -*- coding: utf-8 -*-

from ccxt.async_support.base.exchange import Exchange
import hashlib
from ccxt.base.errors import *
from ccxt.base.errors import AuthenticationError
from ccxt.base.errors import ArgumentsRequired
from ccxt.base.errors import InsufficientFunds
from ccxt.base.errors import InvalidOrder
from ccxt.base.errors import OrderNotFound
from ccxt.base.errors import NotSupported
from ccxt.base.errors import DDoSProtection
import time
import hashlib
import hmac
import json


class gateio_v4(Exchange):

    def describe(self):
        return self.deep_extend(super(gateio_v4, self).describe(), {
            'id': 'gateio_v4',
            'name': 'Gate.io',
            'countries': ['CN'],
            'version': '4',
            'rateLimit': 300,
            'pro': True,
            'has': {
                'cancelOrder': True,
                'createOrder': True,
                'fetchOrder': True,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/31784029-0313c702-b509-11e7-9ccc-bc0da6a0e435.jpg',
                'api': {
                    'public': 'https://api.gateio.ws',
                    'private': 'https://api.gateio.ws',
                },
                'prefix': '/api/v4',
                'www': 'https://gate.io/',
                'doc': 'https://gate.io/api2',
                'fees': [
                    'https://gate.io/fee',
                    'https://support.gate.io/hc/en-us/articles/115003577673',
                ],
                'referral': 'https://www.gate.io/signup/2436035',
            },
            'api': {
                'public': {
                    'get': [
                    ],
                },
                'private': {
                    'get': [
                        'orders/{id}'
                    ],
                    'post': [
                        'orders'
                    ],
                    'delete': [
                        'orders/{id}'
                    ]
                },
            },
            'fees': {
                'trading': {
                    'tierBased': True,
                    'percentage': True,
                    'maker': 0.002,
                    'taker': 0.002,
                },
            },
            'exceptions': {
                'exact': {
                    'BAD_REQUEST': BadRequest,
                    'INTERNAL': NetworkError,
                    'REQUEST_EXPIRED': NetworkError,
                    'SERVER_ERROR': NetworkError,
                    'TOO_BUSY': NetworkError,
                    'INVALID_PRECISION': BadRequest,
                    'MISSING_REQUIRED_PARAM': BadRequest,
                    'MISSING_REQUIRED_HEADER': BadRequest,
                    'INVALID_REQUEST_BODY': BadRequest,
                    'ACCOUNT_LOCKED': AccountSuspended,
                    'FORBIDDEN': AccountSuspended,
                    'ORDER_CLOSED': OrderNotFound,
                    'ORDER_CANCELLED': OrderNotFound,
                    'INVALID_CURRENCY': BadSymbol,
                    'INVALID_CURRENCY_PAIR': BadSymbol,
                    'ORDER_NOT_FOUND': OrderNotFound,
                    'INVALID_SIGNATURE': AuthenticationError,
                    'INVALID_KEY': AuthenticationError,
                    'BALANCE_NOT_ENOUGH': InsufficientFunds,
                    'AMOUNT_TOO_LITTLE': InsufficientFunds,
                    'AMOUNT_TOO_MUCH': InsufficientFunds,
                    'QUANTITY_NOT_ENOUGH': InsufficientFunds
                }
            },
            'options': {
                'limits': {
                    'cost': {
                        'min': {
                            'ETH': '0.001',
                            'USDT': '1',
                            'BTC': '0.0001',
                            'QTUM': '0.01',
                            'LTC': '0.003',
                            'CNYX': '3'
                        },
                    },
                },
            },
            'requiredCredentials': {
                'apiKey': True,
                'secret': True
            }
        })

    async def fetch_order(self, id, symbol=None, params={}):
        request = {
            'currency_pair': symbol,
        }
        response = await self.privateGetOrdersId(self.extend({
            'id': id
        }, request))
        return self.parse_order(response)

    def parse_order(self, order, market=None):
        # {'id': '43805824096', 'text': 't-123456', 'create_time': '1619546248', 'update_time': '1619546248', 'status': 'open', 'currency_pair': 'ETH_USDT', 'type': 'limit', 'account': 'spot', 'side': 'sell', 'amount': '0.001', 'price': '10000', 'time_in_force': 'gtc', 'iceberg': '0', 'auto_borrow': None, 'left': '0.001', 'fill_price': '0', 'filled_total': '0', 'fee': '0', 'fee_currency': 'USDT', 'point_fee': '0', 'gt_fee': '0', 'gt_discount': False, 'rebated_fee': '0', 'rebated_fee_currency': 'ETH'}
        id = self.safe_string(order, 'id')
        symbol = self.safe_string(order, 'currency_pair')
        timestamp = self.safe_timestamp(order, 'create_time')
        lastTradeTimestamp = self.safe_timestamp(order, 'update_time')
        status = self.safe_string(order, 'status')
        time_in_force = self.safe_string(order, 'time_in_force')
        side = self.safe_string(order, 'type')
        price = self.safe_number(order, 'price')
        amount = self.safe_number(order, 'amount')
        filled = self.safe_number(order, 'filled_total')
        remaining = self.safe_number(order, 'left')
        feeCost = self.safe_number(order, 'fee')
        feeCurrency = self.safe_string(order, 'fee_currency')
        return self.safe_order({
            'id': id,
            'clientOrderId': None,
            'datetime': self.iso8601(timestamp),
            'timestamp': timestamp,
            'lastTradeTimestamp': lastTradeTimestamp,
            'status': status,
            'symbol': symbol,
            'type': 'limit',
            'timeInForce': time_in_force,
            'postOnly': None,
            'side': side,
            'price': price,
            'stopPrice': None,
            'cost': None,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'average': None,
            'trades': None,
            'fee': {
                'cost': feeCost,
                'currency': feeCurrency
            },
            'info': order,
        })

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        if type == 'market':
            raise ExchangeError(self.id + ' allows limit orders only')
        request = {"currency_pair": symbol, "type": type, "account": "spot", "side": side, "amount": amount, "price": price}
        response = await self.privatePostOrders(self.extend(request, params))
        return self.parse_order(self.extend({
            'status': 'open',
            'type': side,
            'initialAmount': amount,
        }, response))

    async def cancel_order(self, id, symbol=None, params={}):
        if symbol is None:
            raise ArgumentsRequired(self.id + ' cancelOrder() requires symbol argument')
        request = {
            'currency_pair': symbol,
        }
        response = await self.privateDeleteOrdersId(self.extend({
            'id': id
        }, request))
        return self.parse_order(response)

    def handle_errors(self, code, reason, url, method, headers, body, response, requestHeaders, requestBody):
        if response is None:
            return
        errorCode = self.safe_string(response, 'label')
        message = self.safe_string(response, 'message')
        if errorCode is not None:
            self.throw_exactly_matched_exception(self.exceptions['exact'], errorCode, message)

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        prefix = self.urls['prefix']
        postfix = "/spot/" + self.implode_params(path, params)
        url = self.urls['api'][api] + prefix + postfix
        body = None
        self.check_required_credentials()
        query_string = ''
        if method == 'POST':
            body = json.dumps(params)
        else:
            query_string = self.rawencode(params)
            url = url + "?" + query_string
            del params['id']
        signature = self.gen_sign(self.apiKey, self.secret, method, prefix + postfix, query_string, body)
        headers = {
            'KEY': self.apiKey,
            'Timestamp': signature["Timestamp"],
            'SIGN': signature["SIGN"],
        }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def gen_sign(self, apiKey, secret, method, url, query_string=None, payload_string=None):
        t = time.time()
        m = hashlib.sha512()
        m.update((payload_string or "").encode('utf-8'))
        hashed_payload = m.hexdigest()
        s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, t)
        sign = hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
        return {'KEY': apiKey, 'Timestamp': str(t), 'SIGN': sign}
