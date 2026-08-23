import ipaddress


def is_safe_target(target_ip):

    try:

        ip = ipaddress.ip_address(target_ip)

    except ValueError:

        return False

    return ip == ipaddress.ip_address("127.0.0.1")
