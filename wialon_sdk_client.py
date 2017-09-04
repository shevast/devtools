from PyQt5 import QtCore, QtNetwork
import json


class WialonSDKClient():
	def __init__(self):
		self.secure = False
		self.host = str()
		self.port = str()
		self.sid = str()
		self.nm = QtNetwork.QNetworkAccessManager()

	def login(self, user, password, cb):
		"Try to login/relogin"

		if not self.host:
			cb(1, 'Host isn\'t specified')
			return

		if not self.port:
			cb(1, 'Port isn\'t specified')
			return

		if not user:
			cb(1, 'Please, provide username')
			return

		login_url = '{}://{}:{}/oauth/authorize.html'.format(self.get_protocol(), self.host, self.port)

		request = {
			'client_id': 'Devtools',
			'login': user,
			'passw': password,
			'response_type': 'token',
			'activation_time': 0,
			'duration': 22592000,
			'redirect_uri': 'devtools://redir',
			'access_type': 0x100
		}

		self.post(login_url, request, self.finish_login, cb)

	def token_login(self, access_token, cb):
		token_url = '{}://{}:{}/wialon/ajax.html'.format(self.get_protocol(), self.host, self.port)

		request = {
			'svc': 'token/login',
			'params': json.dumps({'token': access_token})
		}

		self.post(token_url, request, self.update_sid, cb)

	def finish_login(self, reply, cb):
		if reply.error() != QtNetwork.QNetworkReply.NoError:
			cb(1, 'Auth failed')
			return

		access_token = None
		if reply.hasRawHeader(b'Location'):
			access_token = get_token(reply.header(QtNetwork.QNetworkRequest.LocationHeader).toString())
		else:
			cb(1, 'Auth failed')
			return

		self.token_login(access_token, cb)

	def update_sid(self, reply, cb):
		if reply.error() != QtNetwork.QNetworkReply.NoError:
			cb(1, 'Auth failed')
			return

		response = json.loads(reply.readAll().data().decode('utf-8'))

		self.sid = response['eid']
		cb(0, 'Auth successfull')

	def execute_request(self, svc, params, cb):
		if not svc:
			cb(1, 'Service isn\'t specified')
			return

		if params is None:
			cb(1, 'Params aren\'t specified')
			return

		if not self.host:
			cb(1, 'Host isn\'t specified')
			return

		if not self.port:
			cb(1, 'Port isn\'t specified')
			return

		if not self.sid:
			cb(1, 'Not logged in')
			return

		service_url = '{}://{}:{}/wialon/ajax.html'.format(self.get_protocol(), self.host, self.port)

		request = {
			'sid': self.sid,
			'svc': svc,
			'params': json.dumps(params)
		}

		self.post(service_url, request, self.finish_execute, cb)

	def finish_execute(self, reply, cb):
		if reply.error() != QtNetwork.QNetworkReply.NoError:
			cb(1, 'Request failed')
			return

		response = json.loads(reply.readAll().data().decode('ascii'))
		cb(0, response)

	def set_host(self, ip):
		self.host = ip

	def get_host(self):
		return self.host

	def set_port(self, port):
		self.port = port

	def get_port(self):
		return self.port

	def set_secure(self, secure):
		self.secure = secure

	def is_secure(self):
		return self.secure

	def set_sid(self, sid):
		self.sid = sid

	def get_sid(self):
		return self.sid

	def get_protocol(self):
		if self.is_secure:
			return 'https'
		else:
			return 'http'

	def post(self, url, data, cb, cb_args):
		body = QtCore.QByteArray()
		body.append('&'.join(k + '=' + str(v) for k,v in data.items()))

		qurl = QtCore.QUrl(url)
		request = QtNetwork.QNetworkRequest(qurl)
		request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded")
		reply = self.nm.post(request, body)
		reply.ignoreSslErrors()
		reply.finished.connect(callback_factory(reply=reply, cb=cb, cb_args=cb_args))


def callback_factory(*factory_args, **factory_kwargs):
	def response_hook(*args, **kwargs):
		factory_kwargs['cb'](factory_kwargs['reply'], factory_kwargs['cb_args'])
	return response_hook


def get_token(url):
	query = url.split('?')[1]
	params = query.split('&')
	for p in params:
		if 'access_token' in p:
			return p.split('=')[1]
