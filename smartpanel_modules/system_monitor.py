"""
System Monitoring for Smart Panel
CPU, memory, disk, temperature, and network monitoring
"""

import psutil


def get_system_info():
    """Get comprehensive system information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        temperature = get_cpu_temperature()
        network = get_network_info()

        return {
            'cpu': cpu_percent,
            'memory': memory.percent,
            'memory_used': memory.used // (1024*1024),  # MB
            'memory_total': memory.total // (1024*1024),  # MB
            'disk': disk.percent,
            'disk_used': disk.used // (1024*1024*1024),  # GB
            'disk_total': disk.total // (1024*1024*1024),  # GB
            'temperature': temperature,
            'network': network,
            'uptime': get_uptime()
        }
    except Exception as e:
        print(f"Error getting system info: {e}")
        return {}


def get_cpu_temperature():
    """Get CPU temperature in Celsius"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read()) / 1000.0
        return temp
    except:
        return 0.0


def get_network_info():
    """Get network interface information"""
    try:
        addrs = psutil.net_if_addrs()
        for interface, addresses in addrs.items():
            if interface.startswith(('eth', 'wlan')):
                for addr in addresses:
                    if addr.family.name == 'AF_INET':
                        return {
                            'interface': interface,
                            'ip': addr.address,
                            'netmask': addr.netmask
                        }
        return {'interface': 'none', 'ip': '0.0.0.0', 'netmask': '0.0.0.0'}
    except:
        return {'interface': 'error', 'ip': '0.0.0.0', 'netmask': '0.0.0.0'}


def get_uptime():
    """Get system uptime as formatted string"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            days = int(uptime_seconds // (24 * 3600))
            hours = int((uptime_seconds % (24 * 3600)) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{days}d {hours}h {minutes}m"
    except:
        return "unknown"

