"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent - Info linux
This module provides functions to gather system information on Linux systems.
"""

# Standard
import os
import socket
import subprocess
import re
import shutil

from utils import create_machine_id

def get_cpus():
    """ Get number of CPUs """
    return os.cpu_count()

def get_nodename():
    """ Get system nodename """
    return os.uname().nodename

def get_hostname():
    """ Get Hostname """
    return socket.gethostname()

def get_ip_address(hostname):
    """
    Get IP Address
    """
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror as e:
        raise ValueError(f"Unable to resolve hostname '{hostname}': {e}") from e

def cpu_usage(cpu_load):
    if not isinstance(cpu_load, (int, float)) or cpu_load < 0:
        raise ValueError("cpu_load must be a non-negative number")

    total_cpus = get_cpus()
    if total_cpus == 0:
        return False

    cpu_usage_percentage = (cpu_load / total_cpus) * 100

    return round(cpu_usage_percentage, 2)


def bytes_to_mb(bytes_value):
    """
    bytes to megabytes.

    Args:
        bytes_value (int): bytes.

    Returns:
        int:  megabytes (rounded).
    """
    if bytes_value < 0:
        return 0
    return round(bytes_value / (1024 ** 2))

def get_load_avg():
    """Returns the system load average from /proc/loadavg.

    Returns:
        dict: Dictionary with load averages and CPU usage.

    Raises:
        FileNotFoundError: If /proc/loadavg does not exist (not a Linux system).
        ValueError: If the file format is incorrect.
        Exception: For other unexpected errors.
    """
    try:
        with open("/proc/loadavg", "r", encoding='utf-8') as f:
            values = f.readline().split()
            load1, load5, load15 = map(float, values[:3])

    except FileNotFoundError as e:
        raise FileNotFoundError("/proc/loadavg not found (not a Linux system?)") from e
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid /proc/loadavg format: {e}") from e
    except Exception as e:
        raise Exception(f"Unexpected error reading /proc/loadavg: {e}") from e

    current_cpu_usage = cpu_usage(load1)  # Asumo que cpu_usage está definida en otro lugar

    return {
        "loadavg": {
            "1min": round(load1, 2),
            "5min": round(load5, 2),
            "15min": round(load15, 2),
            "usage": round(current_cpu_usage, 2)
        }
    }

def get_memory_info():
    """
    Obtain memory info from /proc/meminfo.

    Returns:
        dict: Dictionary with memory information in MB and percentages.

    Raises:
        FileNotFoundError: If /proc/meminfo does not exist.
        OSError: If there are problems reading the file.
        ValueError: If the data format is invalid.
    """
    if not os.path.exists("/proc/meminfo"):
        raise FileNotFoundError("/proc/meminfo does not exist")

    meminfo = {}
    try:
        with open("/proc/meminfo", "r", encoding='utf-8') as f:
            for line in f:
                key, value = line.split(":")
                meminfo[key.strip()] = int(value.split()[0]) * 1024  # Convert to bytes
    except (OSError, ValueError) as e:
        raise type(e)(f"Error processing /proc/meminfo: {e}") from e

    # Calculate memory metrics
    total = meminfo.get("MemTotal", 0)
    available = meminfo.get("MemAvailable", 0)
    free = meminfo.get("MemFree", 0)
    cached = meminfo.get("Cached", 0)
    buffers = meminfo.get("Buffers", 0)

    used = total - available
    cache_used = cached + buffers

    return {
        "meminfo": {
            "total": bytes_to_mb(total),
            "available": bytes_to_mb(available),
            "free": bytes_to_mb(free),
            "used": bytes_to_mb(used),
            "cache_used": bytes_to_mb(cache_used),
            "cache_percent": round((cache_used / total) * 100, 2) if total > 0 else 0,
            "percent": round((used / total) * 100, 2) if total > 0 else 0
        }
    }

def get_disks_info():
    """
    Obtain disk info from /proc/mounts.

    Returns:
        dict: Disk partitions info with keys: "disksinfo" (list of dicts).

    Raises:
        FileNotFoundError: If /proc/mounts does not exist.
        OSError: If there are problems reading the file or getting stats.
    """
    if not os.path.exists("/proc/mounts"):
        raise FileNotFoundError("/proc/mounts does not exist")

    disks_info = []
    real_filesystems = {
        "ext4", "ext3", "ext2", "xfs", "zfs", "btrfs", "reiserfs",
        "vfat", "fat32", "ntfs", "hfsplus", "exfat", "iso9660",
        "udf", "f2fs", "nfs"
    }

    try:
        with open("/proc/mounts", "r", encoding='utf-8') as mounts:
            for line in mounts:
                try:
                    parts = line.split()
                    if len(parts) < 3:
                        continue

                    device, mountpoint, fstype = parts[0], parts[1], parts[2]

                    if fstype not in real_filesystems:
                        continue

                    stat = os.statvfs(mountpoint)
                    total = bytes_to_mb(stat.f_blocks * stat.f_frsize)
                    free = bytes_to_mb(stat.f_bfree * stat.f_frsize)
                    used = total - free
                    percent = (used / total) * 100 if total > 0 else 0

                    disks_info.append({
                        "device": device,
                        "mountpoint": mountpoint,
                        "fstype": fstype,
                        "total": total,
                        "used": used,
                        "free": free,
                        "percent": round(percent, 2)
                    })

                except (OSError, ValueError, IndexError) as e:
                    continue # Skip this mount

    except OSError as e:
        raise OSError(f"Error reading /proc/mounts: {e}") from e

    return {"disksinfo": disks_info}


def get_uptime():
    """
    Get system uptime in seconds from /proc/uptime.

    Returns:
        float: Uptime in seconds.

    Raises:
        FileNotFoundError: If /proc/uptime does not exist.
        ValueError: If the data format is invalid.
        OSError: For other file reading errors.
    """
    try:
        with open('/proc/uptime', 'r', encoding='utf-8') as f:
            content = f.readline().strip()
            if not content:
                raise ValueError("Empty /proc/uptime file")

            try:
                return float(content.split()[0])
            except (IndexError, ValueError) as e:
                raise ValueError(f"Invalid uptime format: {content}") from e

    except FileNotFoundError as e:
        raise FileNotFoundError("/proc/uptime not found - not a Linux system?") from e
    except OSError as e:
        raise OSError(f"Error reading /proc/uptime: {e}") from e

def read_cpu_stats():
    """
    Read CPU statistics from /proc/stat.

    Returns:
        tuple: (user, nice, system, idle, iowait) CPU time values.

    Raises:
        FileNotFoundError: If /proc/stat doesn't exist.
        ValueError: If data format is invalid.
        OSError: For other I/O related errors.
    """
    if not os.path.exists("/proc/stat"):
        raise FileNotFoundError("/proc/stat does not exist")

    try:
        with open("/proc/stat", "r", encoding='utf-8') as f:
            for line in f:
                if line.startswith("cpu "):
                    parts = line.split()
                    if len(parts) < 7:  # Ensure we have enough values
                        raise ValueError("Malformed cpu line in /proc/stat")
                    return tuple(map(int, parts[1:6]))

        raise ValueError("No CPU data found in /proc/stat")

    except (OSError, ValueError) as e:
        raise type(e)(f"Error reading CPU stats: {e}") from e

def get_iowait(last_cpu_times, current_cpu_times):
    """
    Calculate the percentage of I/O wait time.

    Args:
        last_cpu_times (scputimes): Previous CPU times.
        current_cpu_times (scputimes): Current CPU times.

    Returns:
        float: Calculated I/O wait percentage.
    """

    # Calcular diferencias acumulativas
    user_diff = current_cpu_times.user - last_cpu_times.user
    nice_diff = current_cpu_times.nice - last_cpu_times.nice
    system_diff = current_cpu_times.system - last_cpu_times.system
    idle_diff = current_cpu_times.idle - last_cpu_times.idle
    iowait_diff = (
        (current_cpu_times.iowait - last_cpu_times.iowait)
        if hasattr(current_cpu_times, 'iowait') else 0
    )

    # Suma total de diferencias
    total_diff = user_diff + nice_diff + system_diff + idle_diff + iowait_diff

    # Actualizar el estado anterior
    last_cpu_times = current_cpu_times

    # Calcular el porcentaje de IO Wait
    if total_diff > 0:
        return (iowait_diff / total_diff) * 100

    return 0

def get_listen_ports_info():
    """
    Fetch active listening ports using the `ss` command.

    Returns:
        dict: {"listen_ports_info": [list of port dictionaries]}.

    Raises:
        FileNotFoundError: If the `ss` command is not available.
        subprocess.CalledProcessError: If the `ss` command fails.
        Exception: For other unexpected errors.
    """
    ports_flattened = []
    seen_ports = set()

    # Check for ss command first
    if not shutil.which("ss"):
        raise FileNotFoundError("ss command not found in PATH")

    try:
        # Run `ss` command to list listening sockets
        output = subprocess.check_output(
            ['ss', '-tulnp'],
            stderr=subprocess.PIPE,
            text=True
        ).splitlines()

        ss_regex = re.compile(
            r'(?P<state>LISTEN|UNCONN)\s+\d+\s+\d+\s+'
            r'(?P<local_address>\[.*?\]|[^:\s]+|\*)\:(?P<port>\d+)\s+'
            r'[^\s]+:\*\s+users:\(\((?P<service>.+?)\)\)'
        )

        for line in output:
            try:
                match = ss_regex.search(line)
                if not match:
                    continue

                local_address = match.group('local_address')
                port = int(match.group('port'))
                services_raw = match.group('service')

                # Extract service name
                first_service = re.search(r'"([^"]+)"', services_raw)
                service = first_service.group(1) if first_service else "unknown"

                # Determine protocol and IP version
                protocol = 'tcp' if 'tcp' in line else 'udp'
                ip_version = 'ipv6' if ':' in local_address else 'ipv4'

                # Deduplication
                dedup_key = (local_address, port, protocol, ip_version)
                if dedup_key in seen_ports:
                    continue

                # Format interface address
                interface = '0.0.0.0' if local_address == '*' and ip_version == 'ipv4' else (
                    '[::]' if local_address == '*' and ip_version == 'ipv6' else local_address
                )

                ports_flattened.append({
                    'interface': interface,
                    'port': port,
                    'service': service,
                    'protocol': protocol,
                    'ip_version': ip_version
                })
                seen_ports.add(dedup_key)

            except (ValueError, AttributeError) as e:
                # Skip malformed lines but continue processing
                continue

    except subprocess.CalledProcessError as e:
        error_msg = f"ss command failed: {e.stderr.strip()}" if e.stderr else "ss command failed"
        raise subprocess.CalledProcessError(
            e.returncode, e.cmd, error_msg
        ) from e

    return {"listen_ports_info": ports_flattened}

def is_system_shutting_down() -> bool:
    """
    Detect if the system is shutting down using multiple checks.
    Returns True if any indicator suggests a shutdown.
    """
    try:
        # Check /run/nologin fast check
        if os.path.exists("/run/nologin"):
            return True

        # Check systemd shutdown target
        if shutil.which("systemctl"):
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", "shutdown.target"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if result.stdout.strip().lower() == "active":
                    return True
                # Check systemd global status
                result = subprocess.run(
                    ["systemctl", "is-system-running"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                status = result.stdout.strip().lower()
                if status in ("stopping", "maintenance"):
                    return True
            except subprocess.TimeoutExpired:
                pass
            except subprocess.CalledProcessError:
                pass
            # Avoid check runlevel on systemd systems
            return False

        # Check runlevel (SysV init compatibility)
        try:
            result = subprocess.run(
                ["runlevel"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            runlevel = result.stdout.strip().split()[-1]
            if runlevel in ("0", "6"):
                return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass

    except Exception:
        pass  # Fallback: Assume not shutting down if checks fail

    return False

def get_machine_id(path="/etc/machine-id"):
    """
    Lee el machine-id de un sistema Linux. Si no existe, lo crea usando utils.get_or_create_machine_id().
    Args:
        path (str): Ruta al fichero machine-id (por defecto /etc/machine-id).
    Returns:
        str: machine-id (32 caracteres hex, minúsculas, sin guiones).
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            machine_id = f.read().strip()
            if machine_id:
                return machine_id
    except FileNotFoundError:
        return create_machine_id(path)
    except Exception as e:
        raise RuntimeError(f"Error al leer machine-id: {e}")

    return create_machine_id(path)
