import json, urllib.request, urllib.parse, unittest
from infinity_os.core import InfinityCore
from infinity_os.remote_server2 import RemoteServer2

class RemoteTests(unittest.TestCase):
    def test_pair_status_and_confirmation(self):
        c=InfinityCore();srv=RemoteServer2(c.pairing,c,0)
        try:
            srv.start();port=srv.httpd.server_address[1];pin=c.pairing.pin
            opener=urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
            response=opener.open(f'http://127.0.0.1:{port}/pair?pin={pin}&name=TestPhone')
            token=urllib.parse.parse_qs(urllib.parse.urlparse(response.geturl()).query)['token'][0]
            status=json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/api/status?token={urllib.parse.quote(token)}').read())
            self.assertEqual(status['version'],'7.9.0-ultimate')
            req=urllib.request.Request(f'http://127.0.0.1:{port}/api/command?token={urllib.parse.quote(token)}',data=json.dumps({'command':'press ctrl+l'}).encode(),headers={'Content-Type':'application/json'},method='POST')
            result=json.loads(urllib.request.urlopen(req).read())
            self.assertTrue(result.get('requires_confirmation'))
        finally:srv.stop();c.shutdown()

if __name__=='__main__':unittest.main()
