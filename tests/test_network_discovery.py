from infinity_os.network_discovery import NetworkDiscovery


def test_private_network_is_limited_to_24():
    net = NetworkDiscovery._safe_network('192.168.10.25', '255.255.0.0')
    assert str(net) == '192.168.10.0/24'


def test_public_addresses_are_not_discoverable():
    assert NetworkDiscovery._safe_network('8.8.8.8', '255.255.255.0') is None
    assert NetworkDiscovery._is_private_host('192.168.1.7')
    assert not NetworkDiscovery._is_private_host('8.8.8.8')
