#!/bin/bash

# Get the script's own directory
ANONSUITE_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

export BLUE='\033[1;94m'
export GREEN='\033[1;92m'
export RED='\033[1;91m'
export RESETCOLOR='\033[1;00m'

# Destinations you don't want routed through Tor
# Note: 127.0.0.1 is handled by the pf rules automatically
TOR_EXCLUDE="{ 192.168.0.0/16, 172.16.0.0/12, 10.0.0.0/8 }"

# The UID Tor runs as (less relevant on macOS, but we keep the variable)
TOR_UID="_tor"


function start {
	# Make sure only root can run this script
	if [ $(id -u) -ne 0 ]; then
		echo -e "\n$GREEN[$RED!$GREEN] $RED This script must be run as root$RESETCOLOR\n" >&2
		exit 1
	fi

	echo -e "\n$GREEN[$BLUE i$GREEN ]$BLUE Starting anonymous mode:$RESETCOLOR\n"
	
	# Start multitor
	echo -e " $GREEN*$BLUE Starting multitor...$RESETCOLOR\n"
	"${ANONSUITE_DIR}/multitor/multitor" --init 2 --user "$USER" --socks-port 9000 --control-port 9900 --proxy privoxy --haproxy
	sleep 5 # Give multitor time to start

	# --- OS-Specific Firewall Configuration ---
	if [[ "$(uname)" == "Darwin" ]]; then
		# macOS configuration using pfctl
		TOR_PORT="9050" # HAProxy port for macOS redirection
		echo "Configuring for macOS using pf..."
		# Backup current DNS settings
		cp /etc/resolv.conf /etc/resolv.conf.anonsuite.bak
		# Set DNS to a public resolver to prevent leaks before Tor is active
		echo "nameserver 8.8.8.8" > /etc/resolv.conf

		# Create pf rules for redirection
		echo "
rdr pass on en0 inet proto tcp from any to any -> 127.0.0.1 port $TOR_PORT
rdr pass on en0 inet proto udp from any to any -> 127.0.0.1 port $TOR_PORT
" > /etc/pf.anonsuite.rules

		# Load the pf rules
		pfctl -f /etc/pf.anonsuite.rules
		pfctl -E
	elif [[ "$(uname)" == "Linux" ]]; then
		# Linux configuration using iptables
		TOR_PORT="9040" # Tor's default TransPort for Linux
		echo "Configuring for Linux using iptables..."
		# Backup and set DNS is more complex on Linux (systemd-resolved)
		# For simplicity, we'll just focus on iptables rules here.
		# A real implementation would need to handle DNS carefully.

		# Flush existing rules
		iptables -F
		iptables -t nat -F

		# Redirect all TCP traffic to Tor's TransPort
		iptables -t nat -A OUTPUT -p tcp --syn -j REDIRECT --to-ports $TOR_PORT

	else
		echo -e "\n$GREEN[$RED!$GREEN] $RED Unsupported Operating System: $(uname)$RESETCOLOR\n" >&2
		exit 1
	fi

	echo -e "$GREEN *$BLUE All traffic was redirected through Tor$RESETCOLOR\n"
	echo -e "$GREEN[$BLUE i$GREEN ]$BLUE You are under AnonSuite tunnel$RESETCOLOR\n"
}

function stop {
	# Make sure only root can run our script
	if [ $(id -u) -ne 0 ]; then
		echo -e "\n$GREEN[$RED!$GREEN] $RED This script must be run as root$RESETCOLOR\n" >&2
		exit 1
	fi
	echo -e "\n$GREEN[$BLUE i$GREEN ]$BLUE Stopping anonymous mode:$RESETCOLOR\n"

	# Stop multitor
	"${ANONSUITE_DIR}/multitor/multitor" --kill

	# --- OS-Specific Firewall Cleanup ---
	if [[ "$(uname)" == "Darwin" ]]; then
		# Disable the pf firewall and remove the rules file
		pfctl -d
		rm -f /etc/pf.anonsuite.rules
	elif [[ "$(uname)" == "Linux" ]]; then
		# Flush iptables rules
		iptables -F
		iptables -t nat -F
	fi

	# Restore DNS settings
	if [ -f /etc/resolv.conf.anonsuite.bak ]; then
		mv /etc/resolv.conf.anonsuite.bak /etc/resolv.conf
	fi

	echo -e " $GREEN*$BLUE Anonymous mode stopped$RESETCOLOR\n"
}

case "$1" in
	start)
		start
	;;
	stop)
		stop
	;;
	restart)
		$0 stop
		sleep 1
		$0 start
	;;
   *)
echo -e "
AnonSuite - A Unified Anonymity Toolkit

  Usage:
    anonsuite {start|stop|restart}

  start   - Start system-wide anonymous tunneling.
  stop    - Reset original iptables settings.
  restart - Combines "stop" and "start" options.

" >&2
exit 1
;;
esac

echo -e $RESETCOLOR
exit 0
